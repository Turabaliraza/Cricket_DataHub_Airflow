
import os

import psycopg2
from dotenv import load_dotenv

from transform_espn import (
    load_raw_data,
    transform_tournament,
    transform_teams,
    transform_players,
    transform_player_teams,
    transform_innings,
    transform_player_performance,
    merge_player_performances,
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

    team_ids = []

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

            team_id = cursor.fetchone()[0]

            team_ids.append({
                "external_team_id": team["external_team_id"],
                "team_id": team_id,
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

    player_ids = []

    with connection.cursor() as cursor:
        for player in players:
            cursor.execute(
                query,
                (
                    player["external_player_id"],
                    player["name"],
                ),
            )

            player_id = cursor.fetchone()[0]

            player_ids.append({
                "external_player_id": player["external_player_id"],
                "player_id": player_id,
            })

    return player_ids


def load_player_teams(
    connection,
    player_teams,
    tournament_id,
    team_ids,
    player_ids,
):
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
            player_id = player_id_map[
                player_team["external_player_id"]
            ]
            team_id = team_id_map[
                player_team["external_team_id"]
            ]

            cursor.execute(
                query,
                (player_id, team_id, tournament_id),
            )

            loaded_count += 1

    return loaded_count


def load_matches(connection, data, tournament_id, team_ids):
    event = data["header"]["competitions"][0]

    winner_id = None

    for competitor in event.get("competitors", []):
        if competitor.get("winner") is True:
            external_winner_id = competitor["team"]["id"]

            for team in team_ids:
                if team["external_team_id"] == external_winner_id:
                    winner_id = team["team_id"]
                    break

            break

    match_date = event["date"][:10]

    status_info = event.get("status") or {}
    status_type = status_info.get("type") or {}
    status = status_type.get("description")

    venue_info = event.get("venue") or {}
    venue = venue_info.get("fullName")

    query = """
        INSERT INTO matches (
            external_match_id,
            tournament_id,
            match_date,
            venue,
            status,
            winner_id
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (external_match_id)
        DO UPDATE SET
            tournament_id = EXCLUDED.tournament_id,
            match_date = EXCLUDED.match_date,
            venue = EXCLUDED.venue,
            status = EXCLUDED.status,
            winner_id = EXCLUDED.winner_id
        RETURNING match_id;
    """

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                event["id"],
                tournament_id,
                match_date,
                venue,
                status,
                winner_id,
            ),
        )

        match_id = cursor.fetchone()[0]

    return match_id


def load_match_teams(connection, match_id, team_ids):
    query = """
        INSERT INTO match_teams (
            match_id,
            team_id
        )
        VALUES (%s, %s)
        ON CONFLICT (match_id, team_id)
        DO NOTHING;
    """

    loaded_count = 0

    with connection.cursor() as cursor:
        for team in team_ids:
            cursor.execute(
                query,
                (match_id, team["team_id"]),
            )
            loaded_count += 1

    return loaded_count


def load_innings(connection, innings_data, match_id, team_ids):
    query = """
        INSERT INTO innings (
            match_id,
            innings_number,
            team_id,
            runs,
            wickets,
            overs
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (match_id, team_id, innings_number)
        DO UPDATE SET
            runs = EXCLUDED.runs,
            wickets = EXCLUDED.wickets,
            overs = EXCLUDED.overs;
    """

    team_id_map = {
        team["external_team_id"]: team["team_id"]
        for team in team_ids
    }

    loaded_count = 0

    with connection.cursor() as cursor:
        for innings in innings_data:
            team_id = team_id_map[
                innings["external_team_id"]
            ]

            cursor.execute(
                query,
                (
                    match_id,
                    innings["innings_number"],
                    team_id,
                    innings["runs"],
                    innings["wickets"],
                    innings["overs"],
                ),
            )

            loaded_count += 1

    return loaded_count


def load_player_performances(
    connection,
    performance_data,
    match_id,
    player_ids,
    team_ids,
):
    performance_query = """
        INSERT INTO player_performance (
            innings_id,
            player_id,
            runs,
            balls_faced,
            fours,
            sixes,
            dismissal,
            balls_bowled,
            maidens,
            runs_conceded,
            wickets,
            wides,
            no_balls,
            economy_rate
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (innings_id, player_id)
        DO UPDATE SET
            runs = EXCLUDED.runs,
            balls_faced = EXCLUDED.balls_faced,
            fours = EXCLUDED.fours,
            sixes = EXCLUDED.sixes,
            dismissal = EXCLUDED.dismissal,
            balls_bowled = EXCLUDED.balls_bowled,
            maidens = EXCLUDED.maidens,
            runs_conceded = EXCLUDED.runs_conceded,
            wickets = EXCLUDED.wickets,
            wides = EXCLUDED.wides,
            no_balls = EXCLUDED.no_balls,
            economy_rate = EXCLUDED.economy_rate;
    """

    player_id_map = {
        player["external_player_id"]: player["player_id"]
        for player in player_ids
    }

    team_id_map = {
        team["external_team_id"]: team["team_id"]
        for team in team_ids
    }

    innings_id_map = {}

    with connection.cursor() as cursor:
        # Remove old performance records for this match.
        # The deletion is rolled back if the overall pipeline fails.
        cursor.execute(
            """
            DELETE FROM player_performance pp
            USING innings i
            WHERE pp.innings_id = i.innings_id
              AND i.match_id = %s;
            """,
            (match_id,),
        )

        # Map each innings using both team and innings number.
        cursor.execute(
            """
            SELECT innings_id, innings_number, team_id
            FROM innings
            WHERE match_id = %s;
            """,
            (match_id,),
        )

        for innings_id, innings_number, team_id in cursor.fetchall():
            innings_id_map[(team_id, innings_number)] = innings_id

        loaded_count = 0

        for performance in performance_data:
            external_player_id = performance["external_player_id"]
            external_team_id = performance["external_innings_team_id"]
            innings_number = performance["innings_number"]

            player_id = player_id_map[external_player_id]
            team_id = team_id_map[external_team_id]

            innings_key = (team_id, innings_number)

            if innings_key not in innings_id_map:
                raise ValueError(
                    "No matching innings found for "
                    f"team {external_team_id}, "
                    f"innings {innings_number}"
                )

            innings_id = innings_id_map[innings_key]

            cursor.execute(
                performance_query,
                (
                    innings_id,
                    player_id,
                    performance["runs"],
                    performance["balls_faced"],
                    performance["fours"],
                    performance["sixes"],
                    performance["dismissal"],
                    performance["balls_bowled"],
                    performance["maidens"],
                    performance["runs_conceded"],
                    performance["wickets"],
                    performance["wides"],
                    performance["no_balls"],
                    performance["economy_rate"],
                ),
            )

            loaded_count += 1

    return loaded_count


if __name__ == "__main__":
    data = load_raw_data()

    tournament = transform_tournament(data)
    teams = transform_teams(data)
    players = transform_players(data)
    player_teams = transform_player_teams(data)
    innings_data = transform_innings(data)

    performance_data = transform_player_performance(data)
    performance_data = merge_player_performances(performance_data)

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

        player_ids = load_players(connection, players)

        print("Players loaded successfully.")
        print("Total players loaded:", len(player_ids))

        player_team_count = load_player_teams(
            connection,
            player_teams,
            tournament_id,
            team_ids,
            player_ids,
        )

        print("Player-team relationships loaded successfully.")
        print("Total relationships processed:", player_team_count)

        match_id = load_matches(
            connection,
            data,
            tournament_id,
            team_ids,
        )

        print("Match loaded successfully.")
        print("Internal match ID:", match_id)

        match_team_count = load_match_teams(
            connection,
            match_id,
            team_ids,
        )

        print("Match-team relationships loaded successfully.")
        print(
            "Total match-team relationships processed:",
            match_team_count,
        )

        innings_count = load_innings(
            connection,
            innings_data,
            match_id,
            team_ids,
        )

        print("Innings loaded successfully.")
        print("Total innings processed:", innings_count)

        performance_count = load_player_performances(
            connection,
            performance_data,
            match_id,
            player_ids,
            team_ids,
        )

        print("Player performances loaded successfully.")
        print("Total performances processed:", performance_count)

        connection.commit()
        print("Database transaction committed successfully.")

    except Exception:
        connection.rollback()
        print("Database transaction rolled back.")
        raise

    finally:
        connection.close()
