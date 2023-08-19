import json
from os import curdir
from sqlite3 import Cursor
from uuid import uuid4
from flask import (
    Flask,
    render_template,
    request,
    make_response,
    redirect,
    url_for,
)

from database.mysql_db import (
    get_connection,
    get_party_by_party_code,
    get_player_by_cookie,
    insert_party,
    insert_round,
    get_round_by_id,
    update_round,
    update_player,
    update_player_name,
    get_all_round_type_highscores,
    insert_player,
    get_player_by_id,
    get_all_rounds_from_player,
)
from game import Game, submit_guess, split_genre
from datetime import date

from utils.pusher import init_pusher


app = Flask(__name__)

db = get_connection()
game = Game()
pusher = init_pusher()

ROUND_TYPES = ["5"]


@app.route("/")
def index():
    return render_template("main/index.html", round_types=ROUND_TYPES)


@app.route("/create_game", methods=["POST"])
def create_game():
    round_type = "5"
    cookie_id = str(uuid4())

    cursor = db.cursor()
    player_id = insert_player(cursor, cookie_id, round_type)
    player = get_player_by_id(cursor, player_id)

    rounds_data = game.generate_all_rounds(int(round_type))

    for round_ in rounds_data:
        (artist, genre, related_genres) = round_
        round_id = insert_round(cursor, player, related_genres, genre, artist)
        print(round_id)

    db.commit()
    cursor.close()

    resp = make_response(redirect(url_for("guess")))
    resp.set_cookie("cookie_id", value=cookie_id)
    resp.set_cookie("round_type", value=round_type)
    resp.set_cookie("round_id", expires=0)
    return resp


@app.route("/guess", methods=["GET", "POST"])
def guess():
    cookie_id = request.cookies.get("cookie_id")
    round_type = request.cookies.get("round_type")

    if not cookie_id or request.cookies.get("round_id"):
        return redirect(url_for("index"))

    cursor = db.cursor()
    player = get_player_by_cookie(cursor, cookie_id)

    if not player:
        return redirect(url_for("index"))

    valid_rounds = get_all_rounds_from_player(cursor, player.id, empty_guess_only=True)

    total_words = len(split_genre(valid_rounds[0].genre))

    resp = make_response(
        render_template(
            "main/guess.html",
            round_number=player.total_rounds,
            round_type=player.round_type,
            points_total=player.total_score,
            artist_url=valid_rounds[0].artist_preview_url,
            total_words=total_words,
        )
    )
    resp.set_cookie("round_id", value=str(valid_rounds[0].id))
    return resp


@app.route("/answer", methods=["POST"])
def answer():
    round_id = request.cookies.get("round_id")
    cookie_id = request.cookies.get("cookie_id")

    if not round_id or not cookie_id:
        return redirect(url_for("index"))

    cursor = db.cursor()
    round_ = get_round_by_id(cursor, int(round_id))

    if round_.guess:
        return redirect(url_for("index"))

    round_.guess = request.form.get("genre_guess")
    round_.points, message = submit_guess(round_)

    if not round_.guess:
        round_.guess = "skipped"

    cursor = db.cursor()
    player = get_player_by_cookie(cursor, cookie_id)

    answer_dict = round_.get_answer_fields()
    answer_dict["message"] = message
    answer_dict["round_number"] = player.total_rounds

    update_round(cursor, round_)
    update_player(cursor, player, round_.points)

    db.commit()

    end = 0 == len(get_all_rounds_from_player(cursor, player.id, empty_guess_only=True))
    cursor.close()

    # unpacking: rounds, points, guess, genre, artist, spotify_link, message
    resp = make_response(render_template("main/answer.html", **answer_dict, end=end))
    resp.set_cookie("round_id", expires=0)
    return resp


@app.route("/submit_score", methods=["POST"])
def submit_score():
    name = request.form.get("name")
    cookie_id = request.cookies.get("cookie_id")
    if not name or not cookie_id or not request.form.get("submit_score"):
        redirect(url_for("index"))

    cursor = db.cursor()
    player = get_player_by_cookie(cursor, cookie_id)
    update_player_name(cursor, player, name)
    db.commit()
    cursor.close()

    return redirect(
        url_for("leaderboards", round_type=player.round_type, id_=player.id)
    )


@app.route("/leaderboards/")
@app.route("/leaderboards/<round_type>/<id_>")
def leaderboards(round_type=5, id_=None):
    print(id_, round_type)

    cursor = db.cursor()
    main_high_scores = get_all_round_type_highscores(cursor, ROUND_TYPES)[0]["data"]

    return render_template(
        "leaderboards/leaderboards.html",
        player_id=id_,
        current_round_type=round_type,
        main_high_scores=main_high_scores,
    )


@app.route("/match_details/<player_id>")
def match_details(player_id):
    cursor = db.cursor()
    player = get_player_by_id(cursor, int(player_id))

    # guess, genre, points, artist_name, artist_spotify
    rounds = get_all_rounds_from_player(cursor, player.id)

    rounds_dict = [
        {
            "guess": r.guess,
            "genre": r.genre,
            "points": r.points,
            "artist_name": r.artist_name,
            "artist_spotify": r.artist_spotify,
        }
        for r in rounds
    ]

    if not player or not rounds:
        return redirect(url_for("index"))

    return render_template(
        "leaderboards/match_details.html",
        name=player.name,
        score=player.total_score,
        rounds=rounds_dict,
    )


@app.route("/party")
def party():
    party_code = str(uuid4()).replace("-", "")[0:16]
    return render_template("party/party.html", party_code=party_code)


@app.route("/create_party", methods=["POST"])
def create_party():
    party_code = str(uuid4()).replace("-", "")[0:16]

    cursor = db.cursor()
    insert_party(cursor, party_code)

    return render_template(
        "party/lobby.html", party_code=party_code, user_limit=6, is_host=True
    )


@app.route("/join_party", methods=["POST"])
def join_party():
    party_code = request.form.get("party_code")

    if not party_code:
        return render_template("party/party.html")

    cursor = db.cursor()
    party_game = get_party_by_party_code(cursor, party_code)

    if not party_game or party_game.game_started:
        return render_template("party/party.html")

    return render_template(
        "party/lobby.html", party_code=party_code, user_limit=6, is_host=False
    )
