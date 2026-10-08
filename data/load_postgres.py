import os

import psycopg2
from dotenv import load_dotenv

from transform_espn import (
    load_raw_data,
    transform_tournament,
    transform_teams,
    transform_players,
    transform_player_teams,
)


load_dotenv(dotenv_path=".env")


DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "database": os.getenv("POSTGRES_DATABASE"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def load_tournament(connection, tournament):
    query = """
        INSERT INTO tournaments (
            external_tournament_id,
            name,
            year,
            format
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (external_tournament_id)
        DO UPDATE SET
            name = EXCLUDED.name,
            year = EXCLUDED.year,
            format = EXCLUDED.format
        RETURNING tournament_id;
    """

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                tournament["external_tournament_id"],
                tournament["name"],
                tournament["year"],
                tournament["format"],
            ),
        )

        tournament_id = cursor.fetchone()[0]

    return tournament_id

def load_teams(connection, teams):
    query = """
        INSERT INTO teams (
            external_team_id,
            name,
            country
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (external_team_id)
        DO UPDATE SET
            name = EXCLUDED.name,
            country = EXCLUDED.country
        RETURNING team_id;
    """

    team_ids=[]

    with connection.cursor() as cursor:
        for team in teams:
            cursor.execute(
                query,
                (
                    team["external_team_id"],
                    team["name"],
                    team["country"],
                ),
            )

            team_id= cursor.fetchone()[0]

            team_ids.append({
                "external_team_id":team["external_team_id"],
                "team_id":team_id,
            })
        return team_ids

def load_players(connection, players):
    query = """
        INSERT INTO players (
            external_player_id,
            name
        )
        VALUES (%s, %s)
        ON CONFLICT (external_player_id)
        DO UPDATE SET
            name = EXCLUDED.name
        RETURNING player_id;
    """

    player_ids=[]

    with connection.cursor() as cursor:
        for player in players:
            cursor.execute(
                query,
                (
                    player["external_player_id"],
                    player["name"],
                ),
            )

            player_id=cursor.fetchone()[0]

            player_ids.append({
                "external_player_id":player["external_player_id"],
                "player_id":player_id,
            })
    return player_ids 

def load_player_teams(connection, player_teams, tournament_id, team_ids, player_ids):
    query = """
        INSERT INTO player_teams (
            player_id,
            team_id,
            tournament_id
        )
        VALUES (%s, %s, %s)
        ON CONFLICT (player_id, team_id, tournament_id)
        DO NOTHING;
    """

    player_id_map = {
        player["external_player_id"]: player["player_id"]
        for player in player_ids
    }

    team_id_map = {
        team["external_team_id"]: team["team_id"]
        for team in team_ids
    }

    loaded_count = 0

    with connection.cursor() as cursor:
        for player_team in player_teams:
            external_player_id = player_team["external_player_id"]
            external_team_id = player_team["external_team_id"]

            player_id = player_id_map[external_player_id]
            team_id = team_id_map[external_team_id]

            cursor.execute(
                query,
                (
                    player_id,
                    team_id,
                    tournament_id,
                ),
            )

            loaded_count += 1

    return loaded_count
    


if __name__ == "__main__":
    data = load_raw_data()

    tournament = transform_tournament(data)
    teams = transform_teams(data)

    connection = get_connection()

    try:
        tournament_id = load_tournament(connection, tournament)

        print("Tournament loaded successfully.")
        print("Internal tournament ID:", tournament_id)

        team_ids = load_teams(connection, teams)

        print("Teams loaded successfully.")

        for team in team_ids:
            print(
                f"External team ID: {team['external_team_id']} "
                f"-> Internal team ID: {team['team_id']}"
            )

        players=transform_players(data)

        player_ids=load_players(connection, players)

        print("Players loaded successfully.")
        print("Total players loaded:",len(player_ids))

        player_teams=transform_player_teams(data)

        player_team_count=load_player_teams(
            connection,
            player_teams,
            tournament_id,
            team_ids,
            player_ids,
        )

        print("Player-team relationships loaded successfully.")
        print("Total relationships loaded:",player_team_count)

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()