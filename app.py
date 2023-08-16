import json
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
    get_player_by_cookie,
    insert_round,
    get_round_by_id,
    update_round,
    update_player,
    update_player_name,
    get_all_round_type_highscores,
    insert_player,
    get_player_by_id,
    get_all_rounds_from_player,
    get_daily_challenge_by_date,
    insert_daily_challenge,
    update_player_daily_challenge_id,
)
from game import Game, submit_guess, split_genre
from datetime import date

# import logging as logger
# from util.assets import bundles
# from flask_assets import Environment

app = Flask(__name__)

# assets = Environment(app)
# assets.manifest = False
# assets.cache = False
# assets.register(bundles)

db = get_connection()
game = Game()

ROUND_TYPES = [
    "5",
    # "10",
    # "30"
]


@app.route("/")
def index():
    return render_template("index.html", round_types=ROUND_TYPES)


@app.route("/create_game", methods=["POST"])
def create_game():
    round_type = "5"
    cookie_id = str(uuid4())

    # if not round_type:
    #     return redirect(url_for("index"))

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
            "guess.html",
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
    resp = make_response(render_template("answer.html", **answer_dict, end=end))
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
    main_high_scores = get_all_round_type_highscores(cursor, ROUND_TYPES)[0]['data']

    return render_template(
        "leaderboards.html",
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
        "match_details.html",
        name=player.name,
        score=player.total_score,
        rounds=rounds_dict,
    )


@app.route("/create_daily_challenge")
def create_daily_challenge():
    daily_date = request.cookies.get("daily_challenge")

    if daily_date and daily_date == str(date.today()):
        return redirect(url_for("index"))
    else:
        daily_date = str(date.today())

    cookie_id = str(uuid4())
    cursor = db.cursor()

    # check if daily_challenge for current day exist, if yes get it from db, if no create it
    daily_challenge = get_daily_challenge_by_date(cursor, daily_date)

    round_type = "5"
    player_id = insert_player(cursor, cookie_id, round_type)
    player = get_player_by_id(cursor, player_id)

    daily_challenge = get_daily_challenge_by_date(cursor, daily_date)
    if daily_challenge:
        daily_challenge_id = daily_challenge.id
        round_ids = json.loads(daily_challenge.round_ids)
        rounds = [get_round_by_id(cursor, round_id) for round_id in round_ids]

        for round_ in rounds:
            round_id = insert_round(
                cursor,
                player,
                round_.related_genres,
                round_.genre,
                {
                    "artist": round_.artist_name,
                    "spotify_link": round_.artist_spotify,
                    "preview_url": round_.artist_preview_url,
                },
            )

    if not daily_challenge:
        rounds_data = game.generate_all_rounds(int(round_type))
        round_ids = []
        for round_ in rounds_data:
            (artist, genre, related_genres) = round_
            round_id = insert_round(cursor, player, related_genres, genre, artist)
            round_ids.append(round_id)

        daily_challenge_id = insert_daily_challenge(
            cursor, daily_date, json.dumps(round_ids), int(round_type)
        )

    update_player_daily_challenge_id(cursor, daily_challenge_id, player.id)
    db.commit()

    resp = make_response(redirect(url_for("guess_daily", daily_date=daily_date)))
    resp.set_cookie("cookie_id", value=cookie_id)
    resp.set_cookie("daily_date", daily_date)
    resp.set_cookie("round_id", expires=0)
    return resp


@app.route("/guess/daily/<daily_date>", methods=["GET", "POST"])
def guess_daily(daily_date):
    cookie_id = request.cookies.get("cookie_id")
    cookie_daily_date = request.cookies.get("daily_date")

    if not cookie_daily_date:
        return redirect(url_for("index"))

    if not cookie_id or request.cookies.get("round_id"):
        return redirect(url_for("index"))

    cursor = db.cursor()
    player = get_player_by_cookie(cursor, cookie_id)

    if not player:
        return redirect(url_for("index"))

    valid_rounds = get_all_rounds_from_player(cursor, player.id, empty_guess_only=True)
    print(valid_rounds)
    total_words = len(split_genre(valid_rounds[0].genre))

    resp = make_response(
        render_template(
            "guess.html",
            round_number=player.total_rounds,
            round_type=player.round_type,
            points_total=player.total_score,
            artist_url=valid_rounds[0].artist_preview_url,
            total_words=total_words,
        )
    )
    resp.set_cookie("round_id", value=str(valid_rounds[0].id))
    return resp
