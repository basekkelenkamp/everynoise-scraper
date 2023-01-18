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
)
from game import Game, submit_guess
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

ROUND_TYPES = ["5", "10", "30"]


@app.route("/")
def index():
    resp = make_response(render_template("index.html", round_types=ROUND_TYPES))
    resp.set_cookie("cookie_id", value=str(uuid4()))
    return resp


@app.route("/guess", methods=["POST"])
def guess():
    cookie_id = request.cookies.get("cookie_id")
    round_type = request.form.get("box[1][]")
    if not cookie_id:
        return redirect(url_for("index"))

    if not round_type:
        round_type = "0"

    cursor = db.cursor()

    player = get_player_by_cookie(cursor, cookie_id)
    if not player:
        insert_player(cursor, cookie_id, round_type)
        db.commit()
        player = get_player_by_cookie(cursor, cookie_id)

    artist, genre, related_genres = game.init_new_round()
    round_id = insert_round(cursor, player, related_genres, genre, artist)
    db.commit()
    cursor.close()

    resp = make_response(
        render_template(
            "guess.html",
            round_number=player.total_rounds,
            round_type=player.round_type,
            points_total=player.total_score,
            artist_url=artist["preview_url"],
        )
    )
    resp.set_cookie("round_id", value=str(round_id))
    return resp


@app.route("/answer", methods=["POST"])
def answer():
    round_id = request.cookies.get("round_id")
    cookie_id = request.cookies.get("cookie_id")

    if not round_id or not cookie_id:
        return redirect(url_for("index"))

    cursor = db.cursor()
    round_ = get_round_by_id(cursor, int(round_id))

    round_.guess = request.form.get("genre_guess", "")
    round_.points, message = submit_guess(round_)

    answer_dict = round_.get_answer_fields()
    answer_dict["message"] = message

    cursor = db.cursor()
    player = get_player_by_cookie(cursor, cookie_id)

    update_round(cursor, round_)
    update_player(cursor, player, round_.points)

    db.commit()
    cursor.close()

    end = player.total_rounds >= int(player.round_type)

    # unpacking: rounds, points, guess, genre, artist, spotify_link, message
    resp = make_response(render_template("answer.html", **answer_dict, end=end))
    resp.set_cookie("round_id", expires=0)
    return resp


@app.route("/submit_score", methods=["POST"])
def submit_score():
    name = request.form.get("name")
    cookie_id = request.cookies.get("cookie_id")
    if not name and not cookie_id and not request.form.get("submit_score"):
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
    round_type_highscores = get_all_round_type_highscores(cursor, ROUND_TYPES)

    return render_template(
        "leaderboards.html",
        player_id=id_,
        current_round_type=round_type,
        round_type_data=round_type_highscores,
    )


@app.route("/match_details/<player_id>")
def match_details(player_id):

    cursor = db.cursor()
    player = get_player_by_id(cursor, int(player_id))

    # guess, genre, points, artist_name, artist_spotify
    rounds = get_all_rounds_from_player(cursor, player.id)

    if not player or not rounds:
        return redirect(url_for("index"))

    return render_template(
        "match_details.html", name=player.name, score=player.total_score, rounds=rounds
    )


@app.route("/daily_challenge")
def daily_challenge():
    daily_date = request.cookies.get("daily_challenge")

    if daily_date and daily_date == str(date.today()):
        return redirect(url_for("index"))
    else:
        daily_date = str(date.today())

    resp = make_response(redirect(url_for("guess_daily", daily_date=daily_date)))
    resp.set_cookie("cookie_challenge_id", value=str(uuid4()))
    resp.set_cookie("daily_challenge", daily_date)
    return resp


@app.route("/guess/daily/<daily_date>", methods=["GET", "POST"])
def guess_daily(daily_date):
    breakpoint()
    cookie_id = request.cookies.get("cookie_challenge_id")

    if not cookie_id:
        return redirect(url_for("index"))

    cursor = db.cursor()

    player = get_player_by_cookie(cursor, cookie_id)
    if not player:
        insert_player(cursor, cookie_id, daily_date)
        db.commit()
        player = get_player_by_cookie(cursor, cookie_id)
        # get daily_challenge by daily_date
        # if not:
        #       game.init_new_daily_challenge

    # artist, genre, related_genres = game.init_new_round()
    # round_id = insert_round(cursor, player, related_genres, genre, artist)
    # db.commit()
    # cursor.close()
    #
    # resp = make_response(
    #     render_template(
    #         "guess.html",
    #         round_number=player.total_rounds,
    #         round_type=player.round_type,
    #         points_total=player.total_score,
    #         artist_url=artist["preview_url"],
    #     )
    # )
    # resp.set_cookie("round_id", value=str(round_id))
    # return resp
