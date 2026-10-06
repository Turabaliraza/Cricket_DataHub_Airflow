-- Cricket DataHub Database Schema

CREATE TABLE tournaments (
    tournament_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    format VARCHAR(20) NOT NULL
);


CREATE TABLE teams (
    team_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL
);


CREATE TABLE players (
    player_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);


CREATE TABLE player_teams (
    player_team_id SERIAL PRIMARY KEY,

    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    tournament_id INTEGER NOT NULL,

    FOREIGN KEY (player_id)
        REFERENCES players(player_id),

    FOREIGN KEY (team_id)
        REFERENCES teams(team_id),

    FOREIGN KEY (tournament_id)
        REFERENCES tournaments(tournament_id),

    UNIQUE (player_id, team_id, tournament_id)
);


CREATE TABLE matches (
    match_id SERIAL PRIMARY KEY,

    tournament_id INTEGER NOT NULL,
    match_date DATE NOT NULL,
    venue VARCHAR(150),
    status VARCHAR(20) NOT NULL,
    winner_id INTEGER,

    FOREIGN KEY (tournament_id)
        REFERENCES tournaments(tournament_id),

    FOREIGN KEY (winner_id)
        REFERENCES teams(team_id)
);


CREATE TABLE match_teams (
    match_team_id SERIAL PRIMARY KEY,

    match_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,

    FOREIGN KEY (match_id)
        REFERENCES matches(match_id),

    FOREIGN KEY (team_id)
        REFERENCES teams(team_id),

    UNIQUE (match_id, team_id)
);


CREATE TABLE player_performance (
    performance_id SERIAL PRIMARY KEY,

    match_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,

    runs INTEGER DEFAULT 0,
    balls_faced INTEGER DEFAULT 0,
    wickets INTEGER DEFAULT 0,
    overs_bowled VARCHAR(20),

    FOREIGN KEY (match_id)
        REFERENCES matches(match_id),

    FOREIGN KEY (player_id)
        REFERENCES players(player_id),

    UNIQUE (match_id, player_id)
);