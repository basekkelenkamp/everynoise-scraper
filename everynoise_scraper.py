from asyncio.format_helpers import _get_function_source
import os
from sys import builtin_module_names
import requests
from bs4 import BeautifulSoup
import pandas as pd
from pandas import Series
import re


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


def scrape_genre_page(genre: Series):
    genre_url = os.path.join(base_url, genre["href"])
    every_noise_genre = requests.get(genre_url)
    soup = BeautifulSoup(every_noise_genre.content, "html.parser")
    canvas = soup.find_all("div", {"class": "canvas"})
    artist_divs = canvas[0].find_all("div")

    artists_df = pd.DataFrame(
        [
            {
                "artist": artist_div.text.replace("» ", ""),
                "preview_url": artist_div.get("preview_url"),
                "spotify_link": artist_div.a.get("href"),
            }
            for artist_div in artist_divs
        ]
    )
    related_divs = canvas[1].find_all("div")
    related_genres = [div.text.replace("» ", "") for div in related_divs]

    match = re.search(
        r"Every Noise at Once · (.*?)\n", soup.find("div", {"class": "title"}).text
    )
    real_genre = match.group(1)
    return artists_df, real_genre, related_genres


def scrape_artist_page(artist_link: str):
    url = base_url + artist_link
    artist_page = requests.get(url)

    soup = BeautifulSoup(artist_page.content, "html.parser")
    genres_div = soup.find("div", {"class": "genres"})
    genre_links = genres_div.find_all("a")
    print(genre_links)
    return [link.text for link in genre_links]
