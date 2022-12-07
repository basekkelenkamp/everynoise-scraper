from random import randint
import pandas as pd
import wordsegment
from everynoise_scraper import scrape_all_genres, scrape_genre_artists


class Game:
    points = 0
    game = False
    round = 0
    genres_df = None
    random_artists = []
    random_genres = []
    guesses = []


    def __init__(self):
        self.game = True
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
        self.random_genres.append(random_genre)

        artists_df = scrape_genre_artists(random_genre)
        artists_df.index.name = random_genre["genre"]
        random_artist = artists_df.iloc[randint(0, len(artists_df) - 1)]
        self.random_artists.append(random_artist)

        print(f"Listen: {random_artist['preview_url']}\n")
        return self.round, self.points, random_artist['preview_url']

    def submit_guess(self, guess):
        self.guesses.append(guess)
        print(f"guess: {guess}")
        print(f"answer: {self.random_genres[self.round-1]['genre']}")
