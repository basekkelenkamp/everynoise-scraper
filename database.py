from dotenv import load_dotenv
import MySQLdb
from os import getenv

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
        breakpoint()
    if cursor.execute("SHOW TABLES") == 0:
        print("Attempting to create db tables..")

        q1 = "CREATE TABLE players (" \
             "id int PRIMARY KEY AUTO_INCREMENT, " \
             "name VARCHAR(64), " \
             "total_score int DEFAULT 0, " \
             "total_rounds int DEFAULT 0)"

        q2 = "CREATE TABLE rounds (" \
             "id int PRIMARY KEY AUTO_INCREMENT, " \
             "player_id int, KEY player_id_idx (player_id), " \
             "guess VARCHAR(200), " \
             "points int DEFAULT 0, " \
             "round_number int, " \
             "genre VARCHAR(200), " \
             "related_genres VARCHAR(500), " \
             "artist_name VARCHAR(200), " \
             "artist_spotify VARCHAR(200), " \
             "artist_preview_url VARCHAR(200))"

        cursor.execute(q1)
        cursor.execute(q2)

    cursor.execute("SHOW TABLES")
    for x in cursor:
        print(x)

    breakpoint()
    cursor.execute("DROP TABLE IF EXISTS players")
    cursor.execute("DROP TABLE IF EXISTS rounds")
