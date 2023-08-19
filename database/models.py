from dataclasses import dataclass
from typing import Optional


@dataclass
class Player:
    id: str
    cookie_id: int
    round_type: int
    name: Optional[str]
    total_score: int
    total_rounds: int
    party_code: Optional[str] = None
    party_state: Optional[str] = None


@dataclass
class Round:
    id: str
    player_id: str
    guess: Optional[str]
    points: Optional[int]
    round_number: int
    genre: str
    related_genres: str
    artist_name: str
    artist_spotify: str
    artist_preview_url: str
    party_code: Optional[str] = None

    def get_answer_fields(self):
        return {
            "round_number": self.round_number,
            "points": self.points,
            "guess": self.guess,
            "genre": self.genre,
            "artist": self.artist_name,
            "spotify_link": self.artist_spotify,
            "message": None,
        }


@dataclass
class PartyGame:
    party_code: str
    game_started: bool
    finished_rounds: int
    total_players: int
