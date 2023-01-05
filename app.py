import json
from uuid import uuid4
from flask import (
    Flask,
    render_template,
    request,
    make_response,
)

from database.mysql_db import (
    get_connection,
    get_player_by_cookie,
    insert_round,
    get_round_by_id,
    update_round,
    update_player,
)
from game import Game, submit_guess
import logging as logger


app = Flask(__name__)
db = get_connection()
game = Game()


@app.route("/")
def index():
    cookie_id = str(uuid4())

    cursor = db.cursor()
    query_insert_player = """INSERT INTO players (cookie_id) VALUES (%s)"""
    cursor.execute(query_insert_player, [cookie_id])
    db.commit()

    resp = make_response(render_template("index.html"))
    resp.set_cookie("cookie_id", value=cookie_id)
    return resp


@app.route("/guess", methods=["GET", "POST"])
def guess():
    cookie_id = request.cookies.get("cookie_id")
    if not cookie_id:
        return render_template("index.html")

    cursor = db.cursor()
    player = get_player_by_cookie(cursor, cookie_id)

    artist, genre, related_genres = game.init_new_round()
    round_id = insert_round(cursor, player, related_genres, genre, artist)
    db.commit()

    resp = make_response(
        render_template(
            "guess.html",
            round_number=player.total_rounds,
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
        return render_template("index.html")

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

    # unpacking: rounds, points, guess, genre, artist, spotify_link, message
    return render_template("answer.html", **answer_dict)

