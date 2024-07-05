import json
from uuid import uuid4
from flask import (
    Flask,
    render_template,
    request,
    make_response,
    redirect,
    url_for,
    jsonify,
)
from database.supabase_db import (
    get_first_player_by_party_code,
    get_last_updated_round_from_party_players,
    get_party_by_party_code,
    get_party_players,
    get_player_by_cookie,
    get_player_rank_and_score_by_id,
    increment_party_rounds_by_one,
    insert_party,
    insert_round,
    get_round_by_id,
    remove_player_by_id,
    update_party,
    update_round,
    update_player,
    update_player_name,
    get_all_round_type_highscores,
    insert_player,
    get_player_by_id,
    get_all_rounds_from_player,
)
from everynoise_scraper import scrape_artist_page
from game import Game, Player, submit_guess, split_genre
from utils.pusher import get_pusher_key, init_pusher


app = Flask(__name__)

game = Game()
pusher = init_pusher()

ROUND_TYPES = ["5"]


def create_new_player(round_type="5", party_code=None):
    cookie_id = str(uuid4())

    player_id = insert_player(cookie_id, round_type, party_code)
    return get_player_by_id(player_id)


def generate_player_rounds(player: Player, round_type="5"):
    rounds_data = game.generate_all_rounds(int(round_type))

    for round_ in rounds_data:
        artist, genre, related_genres = round_
        round_id = insert_round(player, related_genres, genre, artist)
        print(round_id)


@app.route("/")
def index():
    return render_template("main/index.html", round_types=ROUND_TYPES)


@app.route("/about")
def about():
    return render_template("main/about.html")


@app.route("/create_game", methods=["POST"])
def create_game():
    round_type = "5"
    player = create_new_player(round_type=round_type)

    generate_player_rounds(player)

    resp = make_response(redirect(url_for("guess")))
    resp.set_cookie("cookie_id", value=player.cookie_id)
    resp.set_cookie("round_type", value="5")
    resp.set_cookie("round_id", expires=0)
    resp.set_cookie("party_code", expires=0)
    return resp


@app.route("/guess", methods=["GET", "POST"])
def guess():
    cookie_id = request.cookies.get("cookie_id")
    round_type = request.cookies.get("round_type")

    if not cookie_id or request.cookies.get("round_id"):
        return redirect(url_for("index"))

    player = get_player_by_cookie(cookie_id)

    if not player:
        return redirect(url_for("index"))

    valid_rounds = get_all_rounds_from_player(player.id, empty_guess_only=True)

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
    party_code = request.cookies.get("party_code")

    if not round_id or not cookie_id:
        return redirect(url_for("index"))

    round_ = get_round_by_id(int(round_id))

    if round_.guess:
        return redirect(url_for("index"))

    round_.guess = request.form.get("genre_guess")
    round_.points, message = submit_guess(round_)

    if not round_.guess:
        round_.guess = "skipped"

    player = get_player_by_cookie(cookie_id)

    answer_dict = round_.get_answer_fields()
    answer_dict["message"] = message
    answer_dict["round_number"] = player.total_rounds

    update_round(round_)
    update_player(player, round_.points)

    end = 0 == len(get_all_rounds_from_player(player.id, empty_guess_only=True))
    ranking, total_score = None, None

    if end:
        ranking, total_score = get_player_rank_and_score_by_id(player.id)

    if party_code:
        is_host = True if request.cookies.get("is_host") else False

        print(
            f"{player.name}. isHost:{is_host}, guess:{round_.guess}, points:{round_.points}, round_num:{player.total_rounds}"
        )

        party = get_party_by_party_code(party_code)
        total_players = party.total_players

        resp = make_response(
            render_template(
                "party/party_wait.html",
                guess=answer_dict["guess"],
                message=answer_dict["message"],
                player_id=str(player.id),
                total_players=total_players,
                is_host=is_host,
                pusher_key=get_pusher_key(),
                party_code=party_code,
                round_id=round_id,
            )
        )
    else:
        # unpacking: rounds, points, guess, genre, artist, spotify_link, message
        resp = make_response(
            render_template(
                "main/answer.html",
                **answer_dict,
                end=end,
                ranking=ranking,
                total_score=total_score,
            )
        )
        resp.set_cookie("round_id", expires=0)

    return resp


@app.route("/submit_score", methods=["POST"])
def submit_score():
    name = request.form.get("name")
    cookie_id = request.cookies.get("cookie_id")
    if not name or not cookie_id or not request.form.get("submit_score"):
        redirect(url_for("index"))

    player = get_player_by_cookie(cookie_id)
    update_player_name(player.id, name)

    return redirect(
        url_for("leaderboards", round_type=player.round_type, id_=player.id)
    )


@app.route("/leaderboards/")
@app.route("/leaderboards/<round_type>/<id_>")
def leaderboards(round_type=5, id_=None):
    main_high_scores = get_all_round_type_highscores(ROUND_TYPES)[0]["data"]

    return render_template(
        "leaderboards/leaderboards.html",
        player_id=id_,
        current_round_type=round_type,
        main_high_scores=main_high_scores,
    )


@app.route("/match_details/<player_id>")
def match_details(player_id):
    player = get_player_by_id(int(player_id))

    # guess, genre, points, artist_name, artist_spotify
    rounds = get_all_rounds_from_player(player.id)

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
    resp = make_response(render_template("party/party.html"))
    resp.set_cookie("cookie_id", expires=0)
    resp.set_cookie("party_code", expires=0)
    resp.set_cookie("round_type", expires=0)
    resp.set_cookie("round_id", expires=0)
    resp.set_cookie("player_id", expires=0)
    resp.set_cookie("is_host", expires=0)
    return resp


@app.route("/create_party", methods=["POST"])
def create_party():
    party_code = str(uuid4()).replace("-", "")[0:16]

    insert_party(party_code)

    player = create_new_player(party_code=party_code)

    generate_player_rounds(player)

    pusher_key = get_pusher_key()

    resp = make_response(
        render_template(
            "party/lobby.html",
            party_code=party_code,
            user_limit=6,
            pusher_key=pusher_key,
            is_host=True,
            player_id=str(player.id),
        )
    )

    resp.set_cookie("cookie_id", value=player.cookie_id)
    resp.set_cookie("party_code", value=party_code)
    resp.set_cookie("round_type", value="5")
    resp.set_cookie("round_id", expires=0)
    resp.set_cookie("is_host", value="true")
    resp.set_cookie("player_id", value=str(player.id))
    return resp


@app.route("/join_party/<party_code>", methods=["GET"])
@app.route("/join_party", methods=["POST"])
def join_party(party_code=None):

    if request.method == "POST":
        party_code = request.form.get("party_code")

    if not party_code:
        return render_template("party/party.html")

    party_game = get_party_by_party_code(party_code)

    if not party_game or party_game.game_started:
        return render_template("party/party.html")

    host_player = get_first_player_by_party_code(party_code)
    rounds = get_all_rounds_from_player(host_player.id)

    player = create_new_player(party_code=party_code)

    for round_ in rounds:
        artist_dict = {
            "artist": round_.artist_name,
            "spotify_link": round_.artist_spotify,
            "preview_url": round_.artist_preview_url,
        }
        round_id = insert_round(
            player, json.loads(round_.related_genres), round_.genre, artist_dict
        )
        print(round_id)

    pusher_key = get_pusher_key()

    resp = make_response(
        render_template(
            "party/lobby.html",
            party_code=party_code,
            user_limit=6,
            pusher_key=pusher_key,
            is_host=False,
            player_id=str(player.id),
        )
    )

    resp.set_cookie("cookie_id", value=player.cookie_id)
    resp.set_cookie("party_code", value=party_code)
    resp.set_cookie("round_type", value="5")
    resp.set_cookie("round_id", expires=0)
    resp.set_cookie("is_host", expires=0)
    resp.set_cookie("player_id", value=str(player.id))
    return resp


@app.route("/pusher/auth", methods=["POST"])
def pusher_authentication():
    player_id = request.cookies.get("player_id")

    channel_name = request.form.get("channel_name")
    socket_id = request.form.get("socket_id")

    auth = pusher.authenticate(
        channel=channel_name,
        socket_id=socket_id,
        custom_data={
            "user_id": player_id,
        },
    )
    return json.dumps(auth)


@app.route("/initialize_party", methods=["POST"])
def initialize_party():
    data = request.json
    party_code = request.cookies.get("party_code")
    is_host = True if request.cookies.get("is_host") else False

    # Only triggered when the game starts
    if is_host:
        players = data.get("playerData")
        update_party(party_code=party_code, game_started=True, total_players=len(players))

        players_data = get_party_players(party_code)
        for player in players_data:
            player_id = str(player.id)
            if player_id not in players:
                remove_player_by_id(player_id)

        for player_id, player_name in players.items():
            update_player_name(player_id, player_name)

    return jsonify({"redirect_url": "guess"})


@app.route("/get_round_party_data", methods=["POST"])
def get_round_party_data():
    data = request.json
    round_id = data.get("roundId")
    party_code = request.cookies.get("party_code")

    final_data = get_last_updated_round_from_party_players(party_code, int(round_id))
    increment_party_rounds_by_one(party_code)

    return jsonify(final_data)


@app.route("/party_round_answer", methods=["POST"])
def party_round_answer():
    data = request.form
    answer = data.get("answer")
    message = data.get("message")
    artist = data.get("artist")
    artist_link = data.get("artist_link")
    party_code = request.cookies.get("party_code")

    players_data = []
    current_player = {}

    for k, value in data.items():
        if k in ["answer", "message", "artist", "artist_link"]:
            continue

        player_name, key = k.split(".")
        if player_name != current_player.get("player_name"):
            if current_player:  # Append the current player's data
                players_data.append(current_player)
            current_player = {"player_name": player_name}
        current_player[key] = value

    # Append the last player's data
    if current_player:
        players_data.append(current_player)

    party = get_party_by_party_code(party_code)

    end = False
    if party.finished_rounds >= 5:
        end = True
        # remove_all_party_data(party_code)

    sorted_players_data = sorted(
        players_data, key=lambda x: int(x["total_points"]), reverse=True
    )

    resp = make_response(
        render_template(
            "party/party_answer.html",
            players_data=sorted_players_data,
            answer=answer,
            message=message,
            artist=artist,
            artist_link=artist_link,
            end=end,
        )
    )

    resp.set_cookie("round_id", expires=0)
    return resp
