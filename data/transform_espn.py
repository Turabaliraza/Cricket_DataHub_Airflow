import json
from pathlib import Path


RAW_FILE = Path(__file__).parent / "raw" / "1544864.json"


def load_raw_data():
    with RAW_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def transform_match(data):
    event = data["header"]["competitions"][0]

    match = {
        "external_match_id": event["id"],
        "match_date": event["date"],
        "venue": event.get("venue", {}).get("fullName"),
        "status": event.get("status", {}).get("type", {}).get("name"),
    }

    return match


def transform_teams(data):
    teams = []

    for competitor in data["header"]["competitions"][0]["competitors"]:
        team = competitor["team"]

        teams.append({
            "external_team_id": team["id"],
            "name": team["displayName"],
            "country": team.get("location"),
        })

    return teams


def transform_players(data):
    players = []

    for roster in data["rosters"]:
        for entry in roster["roster"]:
            player = entry["athlete"]

            players.append({
                "external_player_id": player["id"],
                "name": player["displayName"],
            })

    return players


def transform_player_teams(data):
    player_teams = []

    for roster in data["rosters"]:
        team_id = roster["team"]["id"]

        for entry in roster["roster"]:
            player = entry["athlete"]

            player_teams.append({
                "external_player_id": player["id"],
                "external_team_id": team_id,
            })

    return player_teams


def transform_tournament(data):
    league = data["header"]["league"]
    season = data["header"]["season"]

    tournament = {
        "external_tournament_id": league["id"],
        "name": league["name"],
        "year": season["year"],
        "format": league["abbreviation"],
    }

    return tournament


def transform_innings(data):
    innings = []

    competitors = data["header"]["competitions"][0]["competitors"]

    for competitor in competitors:
        team_id = competitor["team"]["id"]

        for linescore in competitor.get("linescores", []):
            innings.append({
                "external_team_id": team_id,
                "innings_number": linescore["period"],
                "runs": linescore.get("runs"),
                "wickets": linescore.get("wickets"),
                "overs": (
                    str(linescore.get("overs"))
                    if linescore.get("overs") is not None
                    else None
                ),
            })

    return innings


def extract_player_statistics(statistics):
    stats = {}

    for category in statistics.get("categories", []):
        for stat in category.get("stats", []):
            stats[stat["name"]] = stat.get("value")

    return stats


def transform_player_performance(data):
    performances = []

    for roster in data["rosters"]:
        team_id = roster["team"]["id"]

        # Find the opposing team
        opponent_team_id = None

        for other_roster in data["rosters"]:
            other_team_id = other_roster["team"]["id"]

            if other_team_id != team_id:
                opponent_team_id = other_team_id
                break

        for entry in roster["roster"]:
            player = entry["athlete"]
            player_id = player["id"]

            for period in entry.get("linescores", []):
                innings_number = period["period"]

                for linescore in period.get("linescores", []):
                    statistics = linescore.get("statistics", {})
                    stats = extract_player_statistics(statistics)

                    # -------------------------------
                    # Batting performance
                    # -------------------------------

                    if (
                        "ballsFaced" in stats
                        and stats.get("batted", 0) == 1
                    ):
                        batting = statistics.get("batting", {})
                        out_details = batting.get("outDetails", {})

                        performances.append({
                            "external_player_id": player_id,
                            "external_team_id": team_id,
                            "external_innings_team_id": team_id,
                            "innings_number": innings_number,
                            "runs": stats.get("runs", 0),
                            "balls_faced": stats.get("ballsFaced", 0),
                            "fours": stats.get("fours", 0),
                            "sixes": stats.get("sixes", 0),
                            "dismissal": out_details.get("shortText"),
                            "balls_bowled": None,
                            "maidens": None,
                            "runs_conceded": None,
                            "wickets": None,
                            "wides": None,
                            "no_balls": None,
                            "economy_rate": None,
                        })

                    # -------------------------------
                    # Bowling performance
                    # -------------------------------

                    if (
                        "balls" in stats
                        and stats.get("inningsBowled", 0) == 1
                    ):
                        performances.append({
                            "external_player_id": player_id,
                            "external_team_id": team_id,
                            "external_innings_team_id": opponent_team_id,
                            "innings_number": innings_number,
                            "runs": None,
                            "balls_faced": None,
                            "fours": None,
                            "sixes": None,
                            "dismissal": None,
                            "balls_bowled": stats.get("balls", 0),
                            "maidens": stats.get("maidens", 0),
                            "runs_conceded": stats.get("conceded", 0),
                            "wickets": stats.get("wickets", 0),
                            "wides": stats.get("wides", 0),
                            "no_balls": stats.get("noballs", 0),
                            "economy_rate": stats.get("economyRate", 0),
                        })

    return performances


def merge_player_performances(performances):
    merged = {}

    for performance in performances:

        key = (
            performance["external_player_id"],
            performance["external_innings_team_id"],
            performance["innings_number"],
        )

        if key not in merged:
            merged[key] = {
                "external_player_id": performance["external_player_id"],
                "external_team_id": performance["external_team_id"],
                "external_innings_team_id": (
                    performance["external_innings_team_id"]
                ),
                "innings_number": performance["innings_number"],

                # Batting
                "runs": None,
                "balls_faced": None,
                "fours": None,
                "sixes": None,
                "dismissal": None,

                # Bowling
                "balls_bowled": None,
                "maidens": None,
                "runs_conceded": None,
                "wickets": None,
                "wides": None,
                "no_balls": None,
                "economy_rate": None,
            }

        current = merged[key]

        # -------------------------------
        # Merge batting information
        # -------------------------------

        if performance["runs"] is not None:
            current["runs"] = performance["runs"]
            current["balls_faced"] = performance["balls_faced"]
            current["fours"] = performance["fours"]
            current["sixes"] = performance["sixes"]
            current["dismissal"] = performance["dismissal"]

        # -------------------------------
        # Merge bowling information
        # -------------------------------

        if performance["balls_bowled"] is not None:
            current["balls_bowled"] = performance["balls_bowled"]
            current["maidens"] = performance["maidens"]
            current["runs_conceded"] = performance["runs_conceded"]
            current["wickets"] = performance["wickets"]
            current["wides"] = performance["wides"]
            current["no_balls"] = performance["no_balls"]
            current["economy_rate"] = performance["economy_rate"]

    return list(merged.values())


if __name__ == "__main__":
    data = load_raw_data()

    print("\n========== MATCH ==========")
    print(transform_match(data))

    print("\n========== TEAMS ==========")
    print(transform_teams(data))

    print("\n========== PLAYERS ==========")
    print(transform_players(data))

    print("\n========== PLAYER TEAMS ==========")
    print(transform_player_teams(data))

    print("\n========== TOURNAMENT ==========")
    print(transform_tournament(data))

    print("\n========== INNINGS ==========")
    print(transform_innings(data))

    print("\n========== PLAYER PERFORMANCE ==========")

    performances = transform_player_performance(data)

    print(
        f"Total intermediate performance records: "
        f"{len(performances)}"
    )

    merged_performances = merge_player_performances(performances)

    print(
        f"Total merged performance records: "
        f"{len(merged_performances)}"
    )

    for performance in merged_performances:
        print(performance)