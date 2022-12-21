from random import randint
import pandas as pd
import wordsegment
from everynoise_scraper import scrape_all_genres, scrape_genre_artists


class Game:
    points = []
    points_total = 0
    game = False
    round = 0
    genres_df = None
    random_artists = []
    random_genres = []
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

    def init_new_round(self):
        self.round += 1

        random_genre = self.genres_df.iloc[randint(0, len(self.genres_df) - 1)]
        self.random_genres.append(random_genre['genre'])
        artists_df = scrape_genre_artists(random_genre)
        artists_df.index.name = random_genre["genre"]
        random_artist = artists_df.iloc[randint(0, len(artists_df) - 1)]
        self.random_artists.append(random_artist)

        print(f"Listen: {random_artist['preview_url']}\n")
        print(wordsegment.segment(self.random_genres[-1]))
        return self.round, self.points_total, random_artist['preview_url'], random_genre['genre']

    def submit_guess(self, guess, genre):
        self.guesses.append(guess)

        answer = wordsegment.segment(genre)
        split_answer = {x.lower() for x in answer}
        split_guess = {x.lower() for x in wordsegment.segment(guess)}

        self.points_total += self._calculate_points(split_guess, split_answer)

        print(f"guess: {guess}")
        print(f"answer: {self.random_genres[-1]}")

        return {
            "round_number": self.round,
            "points": self.points[-1],
            "guess": guess,
            "genre": " ".join(wordsegment.segment(self.random_genres[-1])),
            "artist": self.random_artists[-1]['artist'],
            "spotify_link": self.random_artists[-1]['spotify_link']
        }

    def _calculate_points(self, guess: set, answer: set):
        song_points = 0
        for guess_part in guess:
            if guess_part in answer:
                song_points += 10
            elif song_points >= 2:
                song_points -= 2

        if sorted(answer) == sorted(guess):
            song_points = 50

        self.points.append(song_points)
        return song_points

    def reset(self):
        self.points = []
        self.points_total = 0
        self.round = 0
        self.random_artists = []
        self.random_genres = []
        self.guesses = []

