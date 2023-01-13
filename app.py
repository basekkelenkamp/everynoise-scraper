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
)
from game import Game, submit_guess
# import logging as logger
from util.assets import bundles
from flask_assets import Environment

app = Flask(__name__)

assets = Environment(app)
assets.register(bundles)

db = get_connection()
game = Game()

ROUND_TYPES = ["5", "10", "30"]


@app.route("/")
def index():
    resp = make_response(render_template("index.html", round_types=ROUND_TYPES))
    resp.set_cookie("cookie_id", value=str(uuid4()))
    return resp


@app.route("/guess", methods=["GET", "POST"])
def guess():
    cookie_id = request.cookies.get("cookie_id")
    round_type = request.form.get("box[1][]")
    if not cookie_id:
        return render_template("index.html")

    if not round_type:
        round_type = "0"

    cursor = db.cursor()
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
    cursor.close()

    end = player.total_rounds >= int(player.round_type)

    # unpacking: rounds, points, guess, genre, artist, spotify_link, message
    return render_template("answer.html", **answer_dict, end=end)


@app.route("/submit_score", methods=["POST"])
def submit_score():
    name = request.form.get("name")
    cookie_id = request.cookies.get("cookie_id")
    if not name and not cookie_id and not request.form.get("submit_score"):
        render_template("index.html")

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
