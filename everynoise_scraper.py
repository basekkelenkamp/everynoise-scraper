import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from random import randint
from pandas import Series
import wordsegment

wordsegment.load()

base_url = "https://everynoise.com/"
game_length = 5


def scrape_all_genres():
    every_noise = requests.get(base_url)
    soup = BeautifulSoup(every_noise.content, "html.parser")
    canvas = soup.find("div", {"class": "canvas"})
    genre_divs = canvas.find_all("div")

    genres_df = pd.DataFrame(columns=["id", "genre", "href"])
    for genre_div in genre_divs:
        genre_id = int(genre_div.get("id").replace("item", ""))
        href = genre_div.a.get("href")
        genre = href.replace("engenremap-", "").replace(".html", "")

        df = pd.DataFrame(
            [
                {
                    "id": genre_id,
                    "genre": genre,
                    "href": href,
                }
            ]
        )
        genres_df = pd.concat([genres_df, df], ignore_index=True)

    genres_df.to_csv("genres.csv", index=False)
    return genres_df


def scrape_genre_artists(genre: Series):
    genre_url = os.path.join(base_url, genre["href"])
    every_noise_genre = requests.get(genre_url)
    soup = BeautifulSoup(every_noise_genre.content, "html.parser")
    canvas = soup.find("div", {"class": "canvas"})
    artist_divs = canvas.find_all("div")

    return pd.DataFrame(
        [
            {
                "artist": artist_div.text.replace("» ", ""),
                "preview_url": artist_div.get("preview_url"),
                "spotify_link": artist_div.a.get("href"),
            }
            for artist_div in artist_divs
        ]
    )


if __name__ == "__main__":
    try:
        g_df = pd.read_csv("genres.csv")
    except FileNotFoundError:
        g_df = scrape_all_genres()

    print("STARTING GAME!")
    print(f"{len(g_df)} genres loaded..")
    print(f"Guess genres to gain points..", end="\n\n")

    points = 0
    game = True
    iteration = 0
    while game:
        iteration += 1
        random_genre = g_df.iloc[randint(0, len(g_df) - 1)]

        artists_df = scrape_genre_artists(random_genre)
        artists_df.index.name = random_genre["genre"]
        random_artist = artists_df.iloc[randint(0, len(artists_df) - 1)]

        print(f"Listen: {random_artist['preview_url']}\n")

        answer = wordsegment.segment(random_genre["genre"])
        split_guess = set(
            [x.lower() for x in wordsegment.segment(input("Guess the genre: "))]
        )
        split_answer = set([x.lower() for x in answer])

        song_points = 0
        for guess_part in split_guess:
            if guess_part in split_answer:
                song_points += 10
            elif song_points >= 2:
                song_points -= 2

        if split_answer == split_guess:
            song_points = 50

        points += song_points

        print(f"{iteration}. Gained +{song_points} song points. Total score: {points}")
        print(f"\nThe correct genre is: {' '.join(answer)}.")
        print(
            f"Artist: {random_artist['artist']}. Save: {random_artist['spotify_link']}",
            end="\n\n",
        )
        key = input("Any key to continue, press x to quit..\n")

        if key == "x":
            print(f"Points: {points}. Total guesses: {iteration}")
            game = False
            quit()
