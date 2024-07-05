CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    cookie_id VARCHAR(64) NOT NULL,
    round_type VARCHAR(16) NOT NULL,
    name VARCHAR(64),
    total_score INT DEFAULT 0,
    total_rounds INT DEFAULT 1,
    party_code VARCHAR(32),
    party_state VARCHAR(32)
);

CREATE TABLE IF NOT EXISTS rounds (
    id SERIAL PRIMARY KEY,
    player_id INT REFERENCES players(id),
    guess VARCHAR(200),
    points INT DEFAULT 0,
    round_number INT,
    genre VARCHAR(200),
    related_genres JSONB,
    artist_name VARCHAR(200),
    artist_spotify VARCHAR(200),
    artist_preview_url VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS party_games (
    party_code VARCHAR(8) PRIMARY KEY,
    game_started BOOLEAN DEFAULT FALSE,
    finished_rounds INT DEFAULT 0,
    total_players INT DEFAULT 0
);
