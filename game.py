import json
from random import randint, choice
import pandas as pd
import requests
from pandas import Series

from database.models import Round
from everynoise_scraper import scrape_all_genres, scrape_genre_page
from dataclasses import dataclass
from uuid import uuid4
import re


@dataclass
class Player:
    """Class for keeping track of individual player data."""

    points: list
    random_artists: list
    random_genres: list
    guesses: list
    related_genres: list
    points_total: int = 0
    round: int = 0


class PlayerNotFoundError(Exception):
    pass


def split_genre(genre) -> list:
    return sorted(set(re.split(r"[ -]", genre)))


def _calculate_points(guess: str, answer: str, related: list):
    split_guess = split_genre(guess)
    split_answer = split_genre(answer)

    if any(
        [
            answer == guess,
            split_answer == split_guess,
            "".join(split_guess) == "".join(split_answer),
        ]
    ):
        song_points = 750
        message = "INSANE! You guessed the exact genre!"
        return song_points, message

    correct_parts_count = sum(guess_part in split_answer for guess_part in split_guess)
    if correct_parts_count:
        part_percentage = correct_parts_count / len(split_answer)
        song_points = int(500 * part_percentage)
        message = f"NICE! You guessed {correct_parts_count} part(s) and {int(part_percentage * 100)}% of the genre correctly!"

        if len(split_guess) - len(split_answer) > 0:
            extra = len(split_guess) - len(split_answer)
            song_points -= int(((500 / len(split_answer)) * extra) / 2)
            message = message + f" {extra} extra word(s).."
            if song_points < 0:
                song_points = 0
        return song_points, message

    for related_genre in related:
        split_related = split_genre(related_genre)
        if any(
            [
                guess == related_genre,
                split_guess == split_related,
                "".join(split_guess) == "".join(split_related),
            ]
        ):
            song_points = 100
            message = "Close! You guessed a related genre!"
            return song_points, message

    for guess_part in split_guess:
        for related_genre in related:
            if guess_part in split_genre(related_genre):
                song_points = 50
                message = (
                    "You guessed part of a related genre. Here are some pity points."
                )
                return song_points, message

    song_points = 0
    message = [
        "Get good.",
        "Almost but not really.",
        "Bruh moment.",
        "We'll get em next time.",
        "Oof.",
        "Embarrassing.",
        "Have you even listened to the audio clip?",
        "That's clearly siberian post modern funk harsh noise.",
    ]
    return song_points, choice(message)


def init_new_player() -> Player:
    return Player(
        points=[],
        random_artists=[],
        random_genres=[],
        guesses=[],
        related_genres=[],
    )


def submit_guess(round_: Round):

    answer: str = round_.genre.lower()
    related: list = [genre.lower() for genre in json.loads(round_.related_genres)]

    points, message = _calculate_points(round_.guess.lower(), answer, related)
    round_.points = points

    print(message)
    print(f"guess: {round_.guess}")
    print(f"answer: {round_.genre}")

    return points, message


class Game:
    players: list[Player] = []
    game = False
    genres_df = None

    def __init__(self):
        self.game = True

        try:
            self.genres_df = pd.read_csv("genres.csv")
        except FileNotFoundError:
            self.genres_df = scrape_all_genres()

        print("STARTING GAME!")
        print(f"{len(self.genres_df)} genres loaded..")
        print("Guess genres to gain points..", end="\n\n")

    def _get_player_by_id(self, id_) -> Player:
        player = next((p for p in self.players if p.player_id == id_), None)

        if not player:
            raise PlayerNotFoundError(
                f"Player not found. id: {id_}, self.players: {[p.__dict__ for p in self.players]}"
            )

        return player

    def init_new_round(self):
        random_genre: Series = self.genres_df.iloc[randint(0, len(self.genres_df) - 1)]

        artists_df, real_genre, related_genres = scrape_genre_page(random_genre)
        random_artist = artists_df.iloc[randint(0, len(artists_df) - 1)]

        print(f"Listen: {random_artist['preview_url']}")
        print(real_genre)
        print(related_genres)

        return random_artist, real_genre, related_genres

    def generate_all_rounds(self, round_type):
        try:
            round_type = int(round_type)
        except ValueError:
            if round_type == ["daily_challenge"]:
                round_type = 3
            round_type = 5

        rounds = []
        while len(rounds) != round_type:
            random_genre: Series = self.genres_df.iloc[
                randint(0, len(self.genres_df) - 1)
            ]

            artists_df, real_genre, related_genres = scrape_genre_page(random_genre)
            random_artist = artists_df.iloc[randint(0, len(artists_df) - 1)]

            try:
                response = requests.get(random_artist["preview_url"])
            except Exception as e:
                continue

            if response.status_code != 200:
                continue

            print(f"Listen: {random_artist['preview_url']}")
            print(real_genre)
            print(related_genres)

            rounds.append((random_artist, real_genre, related_genres))

        return rounds
