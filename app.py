from flask import Flask, render_template, request, url_for, redirect
from pprint import pprint
from game import Game

app = Flask(__name__)
game = Game()


@app.route("/")
def index():
    game.reset()
    return render_template("index.html")


@app.route("/start_game", methods=["GET", "POST"])
def start_game():
    round_number, points_total, artist_url = game.init_new_round()

    print(f"round: {round_number}, points: {points_total} url: {artist_url}")
    return render_template("game.html", round_number=round_number, points_total=points_total, artist_url=artist_url)


@app.route("/genre_guesser", methods=["POST"])
def genre_guesser():
    guess = request.form.get("genre_guess", "")
    answer_dict = game.submit_guess(guess)

    # unpacking: rounds, points, guess, genre, artist, spotify_link
    return render_template("answer.html", **answer_dict)


