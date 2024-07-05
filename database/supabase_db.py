import json
from dotenv import load_dotenv
import os
from supabase import create_client, Client

from database.models import PartyGame, Player, Round

# Load environment variables from .env file
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

print("connected")

def insert_player(cookie_id: str, round_type: str, party_code: str):
    data = {"cookie_id": cookie_id, "round_type": round_type, "party_code": party_code}
    response = supabase.table('players').insert(data).execute()
    return response.data[0]['id']

def get_player_by_cookie(cookie_id: str):
    response = supabase.table('players').select('*').eq('cookie_id', cookie_id).execute()
    if response.data:
        return Player(**response.data[0])
    return None

def get_player_by_id(id_: int):
    response = supabase.table('players').select('*').eq('id', id_).execute()
    if response.data:
        return Player(**response.data[0])
    return None

def get_round_by_id(id_: int):
    response = supabase.table('rounds').select('*').eq('id', id_).execute()
    if response.data:
        return Round(**response.data[0])
    return None

def get_player_rank_and_score_by_id(player_id: int):
    response = supabase.table('players').select('id, total_score').order('total_score', desc=True).execute()
    ranked_players = response.data
    for rank, player in enumerate(ranked_players, start=1):
        if player['id'] == player_id:
            return rank, player['total_score']
    return None, None

def insert_round(player: Player, related_genres: list, genre: str, artist: dict):
    data = {
        "player_id": player.id,
        "round_number": player.total_rounds,
        "genre": genre,
        "related_genres": json.dumps(related_genres),
        "artist_name": artist["artist"],
        "artist_spotify": artist["spotify_link"],
        "artist_preview_url": artist["preview_url"]
    }
    response = supabase.table('rounds').insert(data).execute()
    return response.data[0]['id']

def update_round(round_: Round):
    data = {"guess": round_.guess, "points": round_.points}
    response = supabase.table('rounds').update(data).eq('id', round_.id).is_('guess', None).execute()

def update_player(player: Player, new_points: int):
    data = {
        "total_score": player.total_score + new_points,
        "total_rounds": player.total_rounds + 1
    }
    response = supabase.table('players').update(data).eq('id', player.id).execute()

def update_player_name(player_id: str, name: str):
    data = {"name": name}
    response = supabase.table('players').update(data).eq('id', player_id).execute()

def remove_player_by_name(player):
    response = supabase.table('players').select('*').eq('name', player).execute()
    if response.data:
        player_obj = Player(**response.data[0])
        supabase.table('rounds').delete().eq('player_id', player_obj.id).execute()
        supabase.table('players').delete().eq('id', player_obj.id).execute()

def remove_player_by_id(player_id: str):
    response = supabase.table('players').select('*').eq('id', player_id).execute()
    if response.data:
        player_obj = Player(**response.data[0])
        supabase.table('rounds').delete().eq('player_id', player_obj.id).execute()
        supabase.table('players').delete().eq('id', player_obj.id).execute()

def remove_empty_names():
    response = supabase.table('players').select('*').is_('name', None).or_('name', '').execute()
    empty_players = [Player(**player) for player in response.data]
    for empty_player in empty_players:
        supabase.table('rounds').delete().eq('player_id', empty_player.id).execute()
        supabase.table('players').delete().eq('id', empty_player.id).execute()

def get_all_rounds_from_player(player_id: int, empty_guess_only=False):
    query = supabase.table('rounds').select('*').eq('player_id', player_id)
    if empty_guess_only:
        query = query.is_('guess', None)
    response = query.execute()
    return [Round(**round_) for round_ in response.data]

def get_all_round_type_highscores(round_types: list):
    highscores = []
    for round_type in round_types:
        response = supabase.table('players').select('*').eq('round_type', round_type).not_.is_("name", "null").order('total_score', desc=True).limit(10).execute()
        highscore = {"round_type": round_type, "data": []}
        for result in response.data:
            player = Player(**result)
            name = player.name.replace("(host)", "")
            highscore["data"].append({"id": player.id, "name": name, "score": player.total_score})
        highscores.append(highscore)
    return highscores

def insert_party(party_code: str):
    data = {"party_code": party_code}
    supabase.table('party_games').insert(data).execute()

def get_party_by_party_code(party_code: str):
    response = supabase.table('party_games').select('*').eq('party_code', party_code).execute()
    if response.data:
        return PartyGame(**response.data[0])
    return None

def insert_party_player(cookie_id: str, round_type: str):
    data = {"cookie_id": cookie_id, "round_type": round_type}
    response = supabase.table('players').insert(data).execute()
    return response.data[0]['id']

def get_first_player_by_party_code(party_code: str):
    response = supabase.table('players').select('*').eq('party_code', party_code).order('id').limit(1).execute()
    if response.data:
        return Player(**response.data[0])
    return None

def update_party(party_code: str, game_started=None, finished_rounds=None, total_players=None):
    data = {}
    if game_started is not None:
        data["game_started"] = game_started
    if finished_rounds is not None:
        data["finished_rounds"] = finished_rounds
    if total_players is not None:
        data["total_players"] = total_players
    supabase.table('party_games').update(data).eq('party_code', party_code).execute()

def increment_party_rounds_by_one(party_code: str):
    # Supabase doesn't support increment operation directly. Fetch, increment, and update
    response = supabase.table('party_games').select('finished_rounds').eq('party_code', party_code).execute()
    if response.data:
        finished_rounds = response.data[0]['finished_rounds'] + 1
        supabase.table('party_games').update({'finished_rounds': finished_rounds}).eq('party_code', party_code).execute()

def get_party_players(party_code: str):
    response = supabase.table('players').select('*').eq('party_code', party_code).execute()
    return [Player(**player) for player in response.data]

def get_last_updated_round_from_party_players(party_code: str, round_id: int):
    players_data = []

    response = supabase.table('rounds').select('*').eq('id', round_id).execute()
    host_round = Round(**response.data[0])

    players = get_party_players(party_code)

    for player in players:
        response = supabase.table('rounds').select('*').eq('player_id', player.id).eq('genre', host_round.genre).not_.is_('guess', 'null').execute()
        rounds = [Round(**round_) for round_ in response.data]

        if not rounds:
            print(player)
            continue

        last_updated_round = max(rounds, key=lambda r: r.round_number)

        player_info = {
            "round_guess": last_updated_round.guess,
            "total_points": player.total_score,
            "round_points": last_updated_round.points,
            "player_name": player.name,
        }
        players_data.append(player_info)

    return {
        "players": players_data,
        "answer": host_round.genre,
        "artist": last_updated_round.artist_name,
        "artist_link": last_updated_round.artist_spotify,
    }
