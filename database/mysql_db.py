import json
from unicodedata import name
from dotenv import load_dotenv
from os import getenv

from database.models import PartyGame, Player, Round

import pymysql
from pymysql.cursors import Cursor

pymysql.install_as_MySQLdb()
load_dotenv()


def get_connection(refresh=False):
    load_dotenv()

    connection = pymysql.connect(
        host=getenv("PLANETSCALE_DB_HOST"),
        user=getenv("PLANETSCALE_DB_USERNAME"),
        passwd=getenv("PLANETSCALE_DB_PASSWORD"),
        database=getenv("PLANETSCALE_DB"),
        ssl_verify_identity=True,
        ssl={"ca": getenv("PLANETSCALE_SSL_CERT_PATH")},
    )

    if refresh:
        return connection

    cursor = connection.cursor()

    if not cursor.execute("select @@version"):
        print("no version found.. no db found..")
        raise Exception("Database not found.")

    if cursor.execute("SHOW TABLES") == 0:
        print("Attempting to create db tables..")

        q1 = (
            "CREATE TABLE players ("
            "id int PRIMARY KEY AUTO_INCREMENT, "
            "cookie_id VARCHAR(64) NOT NULL, "
            "round_type VARCHAR(16) NOT NULL, "
            "name VARCHAR(64), "
            "total_score int DEFAULT 0, "
            "total_rounds int DEFAULT 1, "
            "party_code VARCHAR(32) NULL, "
            "party_state VARCHAR(32) NULL)"
        )

        q2 = (
            "CREATE TABLE rounds ("
            "id int PRIMARY KEY AUTO_INCREMENT, "
            "player_id int, KEY player_id_idx (player_id), "
            "guess VARCHAR(200), "
            "points int DEFAULT 0, "
            "round_number int, "
            "genre VARCHAR(200), "
            "related_genres VARCHAR(2500), "
            "artist_name VARCHAR(200), "
            "artist_spotify VARCHAR(200), "
            "artist_preview_url VARCHAR(200))"
        )

        q3 = (
            "CREATE TABLE party_games ("
            "party_code VARCHAR(8) PRIMARY KEY, "
            "game_started BOOLEAN DEFAULT FALSE, "
            "finished_rounds int DEFAULT 0, "
            "total_players int DEFAULT 0)"
        )

        cursor.execute(q1)
        cursor.execute(q2)
        cursor.execute(q3)

    cursor.execute("SHOW TABLES")
    for x in cursor:
        print(x)

    alter_table = False
    if alter_table:
        cursor.execute("ALTER TABLE rounds DROP COLUMN party_code;")

        breakpoint()

    # Remove players by name and its rounds
    remove_player = []
    if remove_player:
        for player in remove_player:
            remove_player_by_name(cursor, player)
        connection.commit()
        print(f"removed players: {remove_player}")

    # Remove players with no name set
    remove_empty = False
    if remove_empty:
        remove_empty_names(cursor)
        connection.commit()
        print("removed all empty players")

    # set to True to reset db
    clear_db = False
    if clear_db:
        cursor.execute("DROP TABLE IF EXISTS players")
        cursor.execute("DROP TABLE IF EXISTS rounds")
        print("DROPPED TABLES")
        breakpoint()
    return connection


def insert_player(cursor: Cursor, cookie_id: str, round_type: str, party_code: str):
    query_insert_player = """INSERT INTO players (cookie_id, round_type, party_code) VALUES (%s, %s, %s)"""
    cursor.execute(query_insert_player, [cookie_id, round_type, party_code])
    return cursor.lastrowid


def get_player_by_cookie(cursor: Cursor, cookie_id: str):
    query_select_player = """SELECT * FROM players WHERE cookie_id = %s"""
    cursor.execute(query_select_player, [cookie_id])
    result = cursor.fetchone()
    if result:
        return Player(*result)
    else:
        return None


def get_player_by_id(cursor: Cursor, id_: int):
    query_select_player = """SELECT * FROM players WHERE id = %s"""
    cursor.execute(query_select_player, [id_])
    return Player(*cursor.fetchone())


def get_round_by_id(cursor: Cursor, id_: int):
    query_select_round = """SELECT * FROM rounds WHERE id = %s"""
    cursor.execute(query_select_round, [id_])

    return Round(*cursor.fetchone())


def insert_round(
    cursor: Cursor, player: Player, related_genres: list, genre: str, artist: dict
):
    query_insert_round = """
        INSERT INTO rounds (
        player_id, 
        round_number, 
        genre, 
        related_genres, 
        artist_name, 
        artist_spotify, 
        artist_preview_url
        ) VALUES (%s,%s,%s,%s,%s,%s,%s)
    """

    cursor.execute(
        query_insert_round,
        [
            player.id,
            player.total_rounds,
            genre,
            json.dumps(related_genres),
            artist["artist"],
            artist["spotify_link"],
            artist["preview_url"],
        ],
    )

    return cursor.lastrowid


def update_round(cursor: Cursor, round_: Round):
    query_update_round = """
        UPDATE rounds SET 
        guess = %s, 
        points = %s
        WHERE id = %s
        AND guess IS NULL
    """

    cursor.execute(query_update_round, [round_.guess, round_.points, round_.id])


def update_player(cursor: Cursor, player: Player, new_points: int):
    query_update_player = """
        UPDATE players SET 
        total_score = %s, 
        total_rounds = %s
        WHERE id = %s
    """

    cursor.execute(
        query_update_player,
        [
            player.total_score + new_points,
            player.total_rounds + 1,
            player.id,
        ],
    )


def update_player_name(cursor: Cursor, player_id: str, name: str):
    query_update_player = """
        UPDATE players SET 
        name = %s
        WHERE id = %s
    """

    cursor.execute(
        query_update_player,
        [
            name,
            player_id,
        ],
    )


def remove_player_by_name(cursor: Cursor, player):
    query_select_player = """SELECT * FROM players WHERE name = %s"""
    cursor.execute(query_select_player, [player])
    player_obj = Player(*cursor.fetchone())

    query_delete_rounds = """DELETE FROM rounds WHERE player_id = %s"""
    cursor.execute(query_delete_rounds, [player_obj.id])

    query_delete_player = """DELETE FROM players WHERE id = %s"""
    cursor.execute(query_delete_player, [player_obj.id])


def remove_empty_names(cursor: Cursor):
    query_select_empty = """SELECT * FROM players WHERE name is NULL OR name = ''"""
    cursor.execute(query_select_empty)
    empty_players = [Player(*player) for player in cursor.fetchall()]

    for empty_player in empty_players:
        query_delete_rounds = """DELETE FROM rounds WHERE player_id = %s"""
        cursor.execute(query_delete_rounds, [empty_player.id])

        query_delete_player = """DELETE FROM players WHERE id = %s"""
        cursor.execute(query_delete_player, [empty_player.id])


def get_all_rounds_from_player(cursor: Cursor, player_id: int, empty_guess_only=False):
    query_select_rounds = """SELECT * FROM rounds WHERE player_id = %s"""
    if empty_guess_only:
        query_select_rounds = (
            """SELECT * FROM rounds WHERE player_id = %s AND guess IS NULL"""
        )

    cursor.execute(query_select_rounds, [player_id])
    return [Round(*round) for round in cursor.fetchall()]


def get_all_round_type_highscores(cursor: Cursor, round_types: list):
    query_select_highscores = """
        SELECT * FROM players 
        WHERE round_type=%s 
        AND name IS NOT NULL
        ORDER BY total_score 
        DESC LIMIT 10
    """

    highscores = []
    for round_type in round_types:

        cursor.execute(query_select_highscores, [round_type])
        results = cursor.fetchall()

        highscore = {"round_type": round_type, "data": []}
        for result in results:
            player = Player(*result)
            highscore["data"].append(
                {"id": player.id, "name": player.name, "score": player.total_score}
            )

        highscores.append(highscore)

    return highscores


def insert_party(cursor: Cursor, party_code: str):
    query_insert_party = """INSERT INTO party_games (party_code) VALUES (%s)"""
    cursor.execute(query_insert_party, [party_code])
    return


def get_party_by_party_code(cursor: Cursor, party_code: str):
    query_select_party_game = """SELECT * FROM party_games WHERE party_code = %s"""
    cursor.execute(query_select_party_game, [party_code])
    result = cursor.fetchone()

    if result:
        return PartyGame(*result)
    else:
        return None


def insert_party_player(cursor: Cursor, cookie_id: str, round_type: str):
    query_insert_player = (
        """INSERT INTO players (cookie_id, round_type) VALUES (%s, %s)"""
    )
    cursor.execute(query_insert_player, [cookie_id, round_type])
    return cursor.lastrowid


def get_first_player_by_party_code(cursor: Cursor, party_code: str):
    query_select_player = (
        """SELECT * FROM players WHERE party_code = %s ORDER BY id ASC LIMIT 1"""
    )
    cursor.execute(query_select_player, [party_code])
    result = cursor.fetchone()
    if result:
        return Player(*result)
    else:
        return None


def update_party(
    cursor: Cursor,
    party_code: str,
    game_started=None,
    finished_rounds=None,
    total_players=None,
):
    query_params = []
    update_clauses = []

    if game_started is not None:
        update_clauses.append("game_started = %s")
        query_params.append(game_started)

    if finished_rounds is not None:
        update_clauses.append("finished_rounds = %s")
        query_params.append(finished_rounds)

    if total_players is not None:
        update_clauses.append("total_players = %s")
        query_params.append(total_players)

    query_update_party = f"""
        UPDATE party_games
        SET {', '.join(update_clauses)}
        WHERE party_code = %s
    """
    query_params.append(party_code)

    cursor.execute(query_update_party, query_params)


def increment_party_rounds_by_one(cursor: Cursor, party_code: str):
    query_increment_rounds = "UPDATE party_games SET finished_rounds = finished_rounds + 1 WHERE party_code = %s"
    cursor.execute(query_increment_rounds, [party_code])


def get_last_updated_round_from_party_players(
    cursor: Cursor, party_code: str, round_id: int
):
    players_data = []

    # Get genre from the specified round_id
    query_select_genre = "SELECT * FROM rounds WHERE id = %s"
    cursor.execute(query_select_genre, [round_id])
    host_round = Round(*cursor.fetchone())

    # Get all players by party_code
    query_select_players = "SELECT * FROM players WHERE party_code = %s"
    cursor.execute(query_select_players, [party_code])
    players = [Player(*player) for player in cursor.fetchall()]

    for player in players:
        query_select_rounds = """SELECT * FROM rounds WHERE player_id = %s AND genre = %s AND guess IS NOT NULL"""
        cursor.execute(query_select_rounds, [player.id, host_round.genre])
        rounds = [Round(*round_) for round_ in cursor.fetchall()]

        last_updated_round = rounds[0]

        # rare case if same genre appears
        if len(rounds) > 1:
            last_updated_round = max(rounds, key=lambda r: r.round_number)

        player_info = {
            "round_guess": last_updated_round.guess,
            "total_points": player.total_score,
            "round_points": last_updated_round.points,
            "player_name": player.name,
        }
        players_data.append(player_info)

    return {
        "players": players_data,
        "answer": host_round.genre,
    }
