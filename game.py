from random import randint
import pandas as pd
import wordsegment
from everynoise_scraper import scrape_all_genres, scrape_genre_artists

if __name__ == "__main__":
    try:
        g_df = pd.read_csv("genres.csv")
    except FileNotFoundError:
        g_df = scrape_all_genres()

    print("STARTING GAME!")
    print(f"{len(g_df)} genres loaded..")
    print("Guess genres to gain points..", end="\n\n")

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
        split_guess = {
            x.lower() for x in wordsegment.segment(input("Guess the genre: "))
        }

        split_answer = {x.lower() for x in answer}

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
