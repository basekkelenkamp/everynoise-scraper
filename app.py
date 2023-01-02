from flask import Flask, render_template, request, url_for, redirect, session
from game import Game, PlayerNotFoundError
from flask_session import Session
import logging as logger

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

game = Game()


@app.route("/")
def index():
    session["id"] = game.init_new_player()
    return render_template("index.html")


@app.route("/start_game", methods=["GET", "POST"])
def start_game():
    try:
        round_number, points_total, artist_url = game.init_new_round(session["id"])
    except PlayerNotFoundError as e:
        logger.error("ERROR: ", e)
        return f"Error :( \n\n{e}"

    print(f"round: {round_number}, points: {points_total} url: {artist_url}")
    return render_template(
        "game.html",
        round_number=round_number,
        points_total=points_total,
        artist_url=artist_url,
    )


@app.route("/genre_guesser", methods=["POST"])
def genre_guesser():
    guess = request.form.get("genre_guess", "")
    answer_dict = game.submit_guess(session["id"], guess)

    # unpacking: rounds, points, guess, genre, artist, spotify_link
    return render_template("answer.html", **answer_dict)


@app.route("/reset_all_players", methods=["GET"])
def reset_all_players():
    game.remove_all_players()
    logger.info("All players removed.")
    return "All players removed."


@app.route("/reset_self", methods=["GET"])
def reset_self():
    game.remove_by_id(session["id"])
    session["id"] = None
    logger.info("Current player removed.")
    return "Current player removed."
