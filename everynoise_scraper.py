import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
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
