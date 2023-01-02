from random import randint, choice
import pandas as pd
from everynoise_scraper import scrape_all_genres, scrape_genre_page
from dataclasses import dataclass
from uuid import uuid4


@dataclass
class Player:
    """Class for keeping track of individual player data."""

    player_id: str
    points: list
    random_artists: list
    random_genres: list
    guesses: list
    related_genres: list
    points_total: int = 0
    round: int = 0


class PlayerNotFoundError(Exception):
    pass


def _calculate_points(guess: str, answer: str, related: list):
    split_guess = sorted(set(guess.split(" ")))
    split_answer = sorted(set(answer.split(" ")))

    if any(
        [
            answer == guess,
            split_answer == split_guess,
            "".join(split_guess) == "".join(split_answer),
        ]
    ):
        song_points = 500
        message = "INSANE! You guessed the exact genre!"
        return song_points, message

    correct_parts_count = sum(guess_part in split_answer for guess_part in split_guess)
    if correct_parts_count:
        part_percentage = correct_parts_count / len(split_answer)
        song_points = int(250 * part_percentage)
        message = f"NICE! You guessed {correct_parts_count} part(s) and {int(part_percentage * 100)}% of the genre correctly!"
        return song_points, message

    if guess in related:
        song_points = 50
        message = "Close! You guessed a related genre!"
        return song_points, message

    for guess_part in split_guess:
        for related_genre in related:
            if guess_part in related_genre.split(" "):
                song_points = 10
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

    def reset(self):
        self.points = []
        self.points_total = 0
        self.round = 0
        self.random_artists = []
        self.random_genres = []
        self.guesses = []
        self.related_genres = []

    def _get_player_by_id(self, id_) -> Player:
        player = next((p for p in self.players if p.player_id == id_), None)

        if not player:
            raise PlayerNotFoundError(
                f"Player not found. id: {id_}, self.players: {[p.__dict__ for p in self.players]}"
            )

        return player

    def init_new_round(self, id_):
        player: Player = self._get_player_by_id(id_)

        player.round += 1
        random_genre: str = self.genres_df.iloc[randint(0, len(self.genres_df) - 1)]

        artists_df, real_genre, related_genres = scrape_genre_page(random_genre)
        random_artist = artists_df.iloc[randint(0, len(artists_df) - 1)]

        player.random_genres.append(real_genre)
        player.related_genres.append(related_genres)
        player.random_artists.append(random_artist)

        print(f"Listen: {random_artist['preview_url']}")
        print(real_genre)
        print(related_genres)

        return player.round, player.points_total, random_artist["preview_url"]

    def submit_guess(self, id_, guess):
        player: Player = self._get_player_by_id(id_)

        player.guesses.append(guess)

        answer: str = player.random_genres[-1].lower()
        related: list = [genre.lower() for genre in player.related_genres[-1]]

        points, message = _calculate_points(guess.lower(), answer, related)
        player.points.append(points)
        player.points_total += points

        print(message)
        print(f"guess: {guess}")
        print(f"answer: {player.random_genres[-1]}")

        return {
            "round_number": player.round,
            "points": points,
            "guess": guess,
            "genre": player.random_genres[-1],
            "artist": player.random_artists[-1]["artist"],
            "spotify_link": player.random_artists[-1]["spotify_link"],
            "message": message,
        }

    def init_new_player(self) -> str:
        player_id = str(uuid4())
        self.players.append(
            Player(
                player_id=player_id,
                points=[],
                random_artists=[],
                random_genres=[],
                guesses=[],
                related_genres=[],
            )
        )

        return player_id

    def remove_all_players(self):
        self.players = []

    def remove_by_id(self, id_):
        for i, player in enumerate(self.players):
            if player.player_id == id_:
                del self.players[i]
                break
