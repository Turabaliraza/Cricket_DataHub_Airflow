import argparse
import json
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_FILE = Path(__file__).parent / "raw" / "1554418.json"

load_dotenv(PROJECT_ROOT / ".env")

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "database": os.getenv("POSTGRES_DATABASE"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}


# ---------------------------------------------------------
# File and database connections
# ---------------------------------------------------------

def load_raw_data():
    with RAW_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_connection():
    missing = [
        key for key, value in DB_CONFIG.items()
        if not value
    ]

    if missing:
        raise ValueError(
            "Missing PostgreSQL configuration: "
            + ", ".join(missing)
        )

    return psycopg2.connect(**DB_CONFIG)


# ---------------------------------------------------------
# Validation and normalization
# ---------------------------------------------------------

def extract_stats(statistics):
    return {
        stat.get("name"): stat.get("value")
        for category in statistics.get("categories", [])
        for stat in category.get("stats", [])
    }


def validate_match(data):
    header = data.get("header", {})
    event = header.get("competitions", [{}])[0]
    league = header.get("league", {})
    season = header.get("season", {})

    if not event.get("id"):
        raise ValueError("Missing external match ID.")

    if not league.get("id") or not league.get("name"):
        raise ValueError("Missing tournament ID or name.")

    if season.get("year") is None:
        raise ValueError("Missing tournament season year.")

    if not event.get("date"):
        raise ValueError("Missing match date.")

    competitors = event.get("competitors", [])

    if len(competitors) != 2:
        raise ValueError(
            f"Expected two teams, found {len(competitors)}."
        )

    teams = []

    for competitor in competitors:
        team = competitor.get("team", {})
        external_team_id = team.get("id")
        name = team.get("displayName")

        if external_team_id is None or not name:
            raise ValueError("A competitor is missing its team ID or name.")

        teams.append({
            "external_team_id": str(external_team_id),
            "name": name,
            "winner": (
                competitor.get("winner") is True
                or str(competitor.get("winner", "")).lower() == "true"
            ),
        })

    if sum(team["winner"] for team in teams) > 1:
        raise ValueError("More than one winning team was reported.")

    innings = []

    for competitor in competitors:
        team = competitor["team"]
        external_team_id = str(team["id"])

        for linescore in competitor.get("linescores", []):
            # Ignore the non-batting placeholder innings.
            if linescore.get("isBatting") is not True:
                continue

            runs = linescore.get("runs")
            wickets = linescore.get("wickets")
            period = linescore.get("period")
            overs = linescore.get("overs")

            if runs is None or wickets is None or period is None:
                raise ValueError(
                    f"Incomplete innings data for "
                    f"{team['displayName']}."
                )

            innings.append({
                "team_id": external_team_id,
                "team_name": team["displayName"],
                "innings_number": int(period),
                "runs": int(runs),
                "wickets": int(wickets),
                "overs": str(overs) if overs is not None else None,
            })

    if not innings:
        raise ValueError("No valid batting innings found.")

    innings_keys = [
        (item["team_id"], item["innings_number"])
        for item in innings
    ]

    if len(innings_keys) != len(set(innings_keys)):
        raise ValueError("Duplicate batting innings detected.")

    return {
        "match_id": str(event["id"]),
        "tournament_id": str(league["id"]),
        "tournament_name": league["name"],
        "season_year": int(season["year"]),
        "format": (league.get("abbreviation") or "Unknown")[:20],
        "match_date": event["date"][:10],
        "status": (
            event.get("status", {})
            .get("type", {})
            .get("description")
            or "Unknown"
        )[:20],
        "result": event.get("status", {}).get("summary"),
        "venue": (
            (event.get("venue") or {}).get("fullName")
        ),
        "teams": teams,
        "innings": innings,
    }


# ---------------------------------------------------------
# Player statistics extraction
# ---------------------------------------------------------

def extract_player_performances(data, match, team_ids, innings_ids):
    """
    Return separate batting and bowling records for each player.

    Batting is linked to the player's own team innings.
    Bowling is linked to the opposing team's batting innings.
    """
    performances = []
    competitors = data["header"]["competitions"][0]["competitors"]

    opponent_map = {}

    for competitor in competitors:
        team_id = str(competitor["team"]["id"])
        opponent_map[team_id] = next(
            str(other["team"]["id"])
            for other in competitors
            if str(other["team"]["id"]) != team_id
        )

    valid_innings = {
        (team_ids[item["team_id"]], item["innings_number"])
        for item in match["innings"]
    }

    for roster in data.get("rosters", []):
        external_team_id = str(roster["team"]["id"])

        if external_team_id not in team_ids:
            continue

        player_team_id = team_ids[external_team_id]
        opponent_external_id = opponent_map[external_team_id]
        opponent_team_id = team_ids[opponent_external_id]

        for entry in roster.get("roster", []):
            athlete = entry.get("athlete", {})
            external_player_id = athlete.get("id")

            if external_player_id is None:
                continue

            external_player_id = str(external_player_id)

            batting = None
            bowling = None

            for period in entry.get("linescores", []):
                innings_number = int(period["period"])

                for item in period.get("linescores", []):
                    stats = extract_stats(
                        item.get("statistics", {})
                    )

                    if stats.get("batted") == 1:
                        batting = {
                            "team_id": player_team_id,
                            "innings_number": innings_number,
                            "runs": stats.get("runs"),
                            "balls_faced": stats.get("ballsFaced"),
                            "fours": stats.get("fours"),
                            "sixes": stats.get("sixes"),
                            "dismissal": None,
                        }

                    if stats.get("inningsBowled") == 1:
                        bowling = {
                            "team_id": opponent_team_id,
                            "innings_number": innings_number,
                            "balls_bowled": stats.get("balls"),
                            "maidens": stats.get("maidens"),
                            "runs_conceded": stats.get("conceded"),
                            "wickets": stats.get("wickets"),
                            "wides": stats.get("wides"),
                            "no_balls": stats.get("noballs"),
                            "economy_rate": stats.get("economyRate"),
                        }

            if batting:
                key = (batting["team_id"], batting["innings_number"])

                if key not in valid_innings:
                    raise ValueError(
                        f"Batting stats for player {external_player_id} "
                        "refer to a missing innings."
                    )

                performances.append({
                    "external_player_id": external_player_id,
                    "innings_id": innings_ids[key],
                    "runs": batting["runs"],
                    "balls_faced": batting["balls_faced"],
                    "fours": batting["fours"],
                    "sixes": batting["sixes"],
                    "dismissal": batting["dismissal"],
                    "balls_bowled": None,
                    "maidens": None,
                    "runs_conceded": None,
                    "wickets": None,
                    "wides": None,
                    "no_balls": None,
                    "economy_rate": None,
                })

            if bowling:
                key = (bowling["team_id"], bowling["innings_number"])

                # A bowler may not have a corresponding batting innings
                # in this particular match format. Don't guess its mapping.
                if key not in valid_innings:
                    continue

                performances.append({
                    "external_player_id": external_player_id,
                    "innings_id": innings_ids[key],
                    "runs": None,
                    "balls_faced": None,
                    "fours": None,
                    "sixes": None,
                    "dismissal": None,
                    "balls_bowled": bowling["balls_bowled"],
                    "maidens": bowling["maidens"],
                    "runs_conceded": bowling["runs_conceded"],
                    "wickets": bowling["wickets"],
                    "wides": bowling["wides"],
                    "no_balls": bowling["no_balls"],
                    "economy_rate": bowling["economy_rate"],
                })

    # There should be at most one record per player per innings.
    seen = set()

    for performance in performances:
        key = (
            performance["innings_id"],
            performance["external_player_id"],
        )

        if key in seen:
            raise ValueError(
                f"Duplicate performance record detected: {key}"
            )

        seen.add(key)

    return performances


# ---------------------------------------------------------
# Database loading functions
# ---------------------------------------------------------

def load_tournament(connection, match):
    query = """
        INSERT INTO tournaments (
            external_tournament_id, name, year, format
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
        cursor.execute(query, (
            match["tournament_id"],
            match["tournament_name"],
            match["season_year"],
            match["format"],
        ))
        return cursor.fetchone()[0]


def load_teams(connection, match):
    query = """
        INSERT INTO teams (external_team_id, name, country)
        VALUES (%s, %s, %s)
        ON CONFLICT (external_team_id)
        DO UPDATE SET
            name = EXCLUDED.name,
            country = EXCLUDED.country
        RETURNING team_id;
    """

    result = {}

    with connection.cursor() as cursor:
        for team in match["teams"]:
            cursor.execute(query, (
                team["external_team_id"],
                team["name"],
                team["name"],
            ))
            result[team["external_team_id"]] = cursor.fetchone()[0]

    return result


def load_players(connection, data, tournament_id, team_ids):
    players = {}

    with connection.cursor() as cursor:
        for roster in data.get("rosters", []):
            external_team_id = str(roster["team"]["id"])

            if external_team_id not in team_ids:
                continue

            team_id = team_ids[external_team_id]

            for entry in roster.get("roster", []):
                athlete = entry.get("athlete", {})
                external_player_id = athlete.get("id")
                name = athlete.get("displayName")

                if external_player_id is None or not name:
                    continue

                external_player_id = str(external_player_id)

                cursor.execute("""
                    INSERT INTO players (external_player_id, name)
                    VALUES (%s, %s)
                    ON CONFLICT (external_player_id)
                    DO UPDATE SET name = EXCLUDED.name
                    RETURNING player_id;
                """, (external_player_id, name))

                player_id = cursor.fetchone()[0]
                players[external_player_id] = player_id

                cursor.execute("""
                    INSERT INTO player_teams (
                        player_id, team_id, tournament_id
                    )
                    VALUES (%s, %s, %s)
                    ON CONFLICT (player_id, team_id, tournament_id)
                    DO NOTHING;
                """, (player_id, team_id, tournament_id))

    return players


def load_match(connection, match, tournament_id, team_ids):
    winner_id = next(
        (
            team_ids[team["external_team_id"]]
            for team in match["teams"]
            if team["winner"]
        ),
        None,
    )

    query = """
        INSERT INTO matches (
            external_match_id, tournament_id, match_date,
            venue, status, winner_id
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
        cursor.execute(query, (
            match["match_id"],
            tournament_id,
            match["match_date"],
            match["venue"],
            match["status"],
            winner_id,
        ))

        match_id = cursor.fetchone()[0]

        for team_id in team_ids.values():
            cursor.execute("""
                INSERT INTO match_teams (match_id, team_id)
                VALUES (%s, %s)
                ON CONFLICT (match_id, team_id)
                DO NOTHING;
            """, (match_id, team_id))

    return match_id


def load_innings(connection, match, match_id, team_ids):
    innings_ids = {}

    with connection.cursor() as cursor:
        for innings in match["innings"]:
            team_id = team_ids[innings["team_id"]]

            cursor.execute("""
                INSERT INTO innings (
                    match_id, innings_number, team_id,
                    runs, wickets, overs
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (match_id, team_id, innings_number)
                DO UPDATE SET
                    runs = EXCLUDED.runs,
                    wickets = EXCLUDED.wickets,
                    overs = EXCLUDED.overs
                RETURNING innings_id;
            """, (
                match_id,
                innings["innings_number"],
                team_id,
                innings["runs"],
                innings["wickets"],
                innings["overs"],
            ))

            innings_ids[
                (team_id, innings["innings_number"])
            ] = cursor.fetchone()[0]

    return innings_ids


def load_performances(connection, performances, players, match_id):
    # Remove stale performances for this match before inserting the
    # freshly validated set. The caller's transaction can roll this back.
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM player_performance pp
            USING innings i
            WHERE pp.innings_id = i.innings_id
              AND i.match_id = %s;
        """, (match_id,))

        query = """
            INSERT INTO player_performance (
                innings_id, player_id, runs, balls_faced,
                fours, sixes, dismissal, balls_bowled,
                maidens, runs_conceded, wickets, wides,
                no_balls, economy_rate
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s);
        """

        for performance in performances:
            player_id = players[performance["external_player_id"]]

            cursor.execute(query, (
                performance["innings_id"],
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
            ))

    return len(performances)


# ---------------------------------------------------------
# Pipeline
# ---------------------------------------------------------

def run_validation(data):
    match = validate_match(data)

    # Validate player mappings against the real innings without
    # opening a database connection.
    team_ids = {
        team["external_team_id"]: index + 1
        for index, team in enumerate(match["teams"])
    }

    innings_ids = {
        (team_ids[item["team_id"]], item["innings_number"]):
        index + 1
        for index, item in enumerate(match["innings"])
    }

    performances = extract_player_performances(
        data, match, team_ids, innings_ids
    )

    print("\n========== INTERNATIONAL MATCH VALIDATION ==========")
    print("Match ID:", match["match_id"])
    print("Tournament:", match["tournament_name"])
    print("Tournament ID:", match["tournament_id"])
    print("Season year:", match["season_year"])
    print("Match date:", match["match_date"])
    print("Status:", match["status"])
    print("Result:", match["result"])

    print("\nTeams:")
    for team in match["teams"]:
        print(
            f"- {team['name']} | "
            f"External ID: {team['external_team_id']} | "
            f"Winner: {team['winner']}"
        )

    print("\nBatting innings:")
    for innings in match["innings"]:
        print(
            f"- {innings['team_name']}: "
            f"{innings['runs']}/{innings['wickets']} "
            f"({innings['overs']} overs), "
            f"innings {innings['innings_number']}"
        )

    batting_count = sum(
        p["runs"] is not None for p in performances
    )
    bowling_count = sum(
        p["balls_bowled"] is not None for p in performances
    )

    print("\nPlayer-statistics validation:")
    print("Batting records:", batting_count)
    print("Bowling records:", bowling_count)
    print("Total performance records:", len(performances))
    print("\nValidation successful. No database changes made.")


def run_database_load(data):
    match = validate_match(data)

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT match_id
                FROM matches
                WHERE external_match_id = %s;
            """, (match["match_id"],))

            existing_match = cursor.fetchone()

        # Existing match data is refreshed transactionally.
        # Its performance rows are deleted and reinserted.
        tournament_id = load_tournament(connection, match)
        team_ids = load_teams(connection, match)

        players = load_players(
            connection, data, tournament_id, team_ids
        )

        match_id = load_match(
            connection, match, tournament_id, team_ids
        )

        innings_ids = load_innings(
            connection, match, match_id, team_ids
        )

        performances = extract_player_performances(
            data, match, team_ids, innings_ids
        )

        performance_count = load_performances(
            connection, performances, players, match_id
        )

        connection.commit()

        print("\nDatabase transaction committed successfully.")
        print("Tournament ID:", tournament_id)
        print("Match ID:", match_id)
        print("Teams loaded:", len(team_ids))
        print("Players loaded:", len(players))
        print("Batting innings loaded:", len(innings_ids))
        print("Player-performance records:", performance_count)
        print(
            "Existing match refreshed:"
            if existing_match
            else "New match inserted:"
        )

    except Exception:
        connection.rollback()
        print("Database transaction rolled back.")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate or load an ESPN international cricket match."
    )
    parser.add_argument(
        "--load",
        action="store_true",
        help="Write validated data to PostgreSQL. Without this flag, "
             "the script only validates and prints a summary.",
    )
    args = parser.parse_args()

    raw_data = load_raw_data()

    if args.load:
        run_database_load(raw_data)
    else:
        run_validation(raw_data)
