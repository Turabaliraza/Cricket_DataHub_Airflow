-- ============================================
-- Cricket DataHub Database Schema
-- ============================================

-- ============================================
-- 1. TOURNAMENTS
-- ============================================

CREATE TABLE tournaments (
    tournament_id SERIAL PRIMARY KEY,

    external_tournament_id VARCHAR(50) UNIQUE,
    name VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    format VARCHAR(20) NOT NULL
);


-- ============================================
-- 2. TEAMS
-- ============================================

CREATE TABLE teams (
    team_id SERIAL PRIMARY KEY,

    external_team_id VARCHAR(50) UNIQUE,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL
);


-- ============================================
-- 3. PLAYERS
-- ============================================

CREATE TABLE players (
    player_id SERIAL PRIMARY KEY,

    external_player_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL
);


-- ============================================
-- 4. PLAYER TEAMS
-- ============================================

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


-- ============================================
-- 5. MATCHES
-- ============================================

CREATE TABLE matches (
    match_id SERIAL PRIMARY KEY,

    external_match_id VARCHAR(50) UNIQUE NOT NULL,

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


-- ============================================
-- 6. MATCH TEAMS
-- ============================================

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


-- ============================================
-- 7. INNINGS
-- ============================================

CREATE TABLE innings (
    innings_id SERIAL PRIMARY KEY,

    match_id INTEGER NOT NULL,
    innings_number INTEGER NOT NULL,
    team_id INTEGER NOT NULL,

    runs INTEGER,
    wickets INTEGER,
    overs VARCHAR(20),

    FOREIGN KEY (match_id)
        REFERENCES matches(match_id),

    FOREIGN KEY (team_id)
        REFERENCES teams(team_id),

    UNIQUE (match_id, innings_number)
);


-- ============================================
-- 8. PLAYER PERFORMANCE
-- ============================================

CREATE TABLE player_performance (
    performance_id SERIAL PRIMARY KEY,

    innings_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,

    -- Batting
    runs INTEGER,
    balls_faced INTEGER,
    fours INTEGER,
    sixes INTEGER,
    dismissal VARCHAR(150),

    -- Bowling
    balls_bowled INTEGER,
    maidens INTEGER,
    runs_conceded INTEGER,
    wickets INTEGER,
    wides INTEGER,
    no_balls INTEGER,
    economy_rate NUMERIC(6,2),

    FOREIGN KEY (innings_id)
        REFERENCES innings(innings_id),

    FOREIGN KEY (player_id)
        REFERENCES players(player_id),

    UNIQUE (innings_id, player_id)
);