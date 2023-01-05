import json

from MySQLdb.cursors import Cursor
from dotenv import load_dotenv
import MySQLdb
from os import getenv

from database.models import Player, Round

load_dotenv()


def get_connection():
    load_dotenv()

    connection = MySQLdb.connect(
        host=getenv("HOST"),
        user=getenv("USERNAME"),
        passwd=getenv("PASSWORD"),
        database=getenv("DATABASE"),
        ssl_mode="VERIFY_IDENTITY",
        ssl={"ca": "/etc/ssl/cert.pem"},
    )

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
            "name VARCHAR(64), "
            "total_score int DEFAULT 0, "
            "total_rounds int DEFAULT 1)"
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

        cursor.execute(q1)
        cursor.execute(q2)

    cursor.execute("SHOW TABLES")
    for x in cursor:
        print(x)

    remove = False
    if remove:
        cursor.execute("DROP TABLE IF EXISTS players")
        cursor.execute("DROP TABLE IF EXISTS rounds")
        print("DROPPED TABLES")
        breakpoint()
    return connection


def get_player_by_cookie(cursor: Cursor, cookie_id: str):
    query_select_player = """SELECT * FROM players WHERE cookie_id = %s"""
    cursor.execute(query_select_player, [cookie_id])

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
