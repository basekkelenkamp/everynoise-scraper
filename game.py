from random import randint, choice
import pandas as pd
import wordsegment
from everynoise_scraper import scrape_all_genres, scrape_genre_page


class Game:
    points = []
    points_total = 0
    game = False
    round = 0
    genres_df = None
    random_artists = []
    random_genres = []
    related_genres = []
    guesses = []

    def __init__(self):
        self.game = True
        wordsegment.load()

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

    def init_new_round(self):
        self.round += 1

        random_genre = self.genres_df.iloc[randint(0, len(self.genres_df) - 1)]

        artists_df, real_genre, related_genres = scrape_genre_page(random_genre)
        artists_df.index.name = real_genre
        random_artist = artists_df.iloc[randint(0, len(artists_df) - 1)]

        self.random_genres.append(real_genre)
        self.random_artists.append(random_artist)
        self.related_genres.append(related_genres)

        print(f"Listen: {random_artist['preview_url']}")
        print(real_genre)
        print(related_genres)

        return self.round, self.points_total, random_artist["preview_url"]

    def submit_guess(self, guess):
        self.guesses.append(guess)

        answer = self.random_genres[-1].lower()
        related = [genre.lower() for genre in self.related_genres[-1]]

        points, message = self._calculate_points(guess.lower(), answer, related)
        self.points_total += points

        print(message)
        print(f"guess: {guess}")
        print(f"answer: {self.random_genres[-1]}")

        return {
            "round_number": self.round,
            "points": self.points[-1],
            "guess": guess,
            "genre": self.random_genres[-1],
            "artist": self.random_artists[-1]["artist"],
            "spotify_link": self.random_artists[-1]["spotify_link"],
            "message": message,
        }

    def _calculate_points(self, guess: str, answer: str, related: list):
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
            self.points.append(song_points)
            message = "INSANE! You guessed the exact genre!"
            return song_points, message

        correct_parts_count = sum(
            guess_part in split_answer for guess_part in split_guess
        )
        if correct_parts_count:
            part_percentage = correct_parts_count / len(split_answer)
            song_points = int(250 * part_percentage)
            self.points.append(song_points)
            message = f"NICE! You guessed {correct_parts_count} part(s) and {int(part_percentage*100)}% of the genre correctly!"
            return song_points, message

        if guess in related:
            song_points = 50
            self.points.append(song_points)
            message = "Close! You guessed a related genre!"
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
        self.points.append(song_points)
        return song_points, choice(message)
