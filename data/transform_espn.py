import json
from pathlib import Path


RAW_FILE = Path(__file__).parent / "raw" / "1544864.json"


def load_raw_data():
    with RAW_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def transform_match(data):
    header = data["header"]
    competition = header["competitions"][0]

    match = {
        "external_match_id": header["id"],
        "name": header["name"],
        "date": competition["date"],
        "format": competition["class"]["generalClassCard"],
    }

    return match


def transform_teams(data):
    competition = data["header"]["competitions"][0]

    teams = []

    for competitor in competition["competitors"]:
        team = competitor["team"]

        teams.append({
            "external_team_id": team["id"],
            "name": team["displayName"],
            "country": team["location"],
        })

    return teams


def transform_players(data):
    players = {}
    rosters = data["rosters"]

    for roster in rosters:
        for entry in roster["roster"]:
            player = entry["athlete"]

            player_id = player["id"]

            players[player_id] = {
                "external_player_id": player_id,
                "name": player["displayName"],
            }

    return list(players.values())

def transform_player_teams(data):
    player_teams = []
    rosters = data["rosters"]

    for roster in rosters:
        team_id = roster["team"]["id"]

        for entry in roster["roster"]:
            player = entry["athlete"]

            player_teams.append({
                "external_player_id": player["id"],
                "external_team_id": team_id,
            })

    return player_teams

def transform_tournament(data):
    season=data["header"]["season"]
    competition=data["header"]["competitions"][0]

    tournament={
        "external_tournament_id":str(season["type"]),
        "name":season["slug"],
        "year":season["year"],
        "format":competition["class"]["generalClassCard"],
    }

    return tournament

def transform_innings(data):
    innings=[]

    competitors=data["header"]["competitions"][0]["competitors"]

    for competitor in competitors:
        team_id=competitor["team"]["id"]

        for linescore in competitor["linescores"]:
            innings.append({
                "external_team_id":team_id,
                "innings_number":linescore["period"],
                "runs":linescore["runs"],
                "wickets":linescore["wickets"],
                "overs":str(linescore["overs"]),
            })

    return innings 

def extract_player_statistics(statistics):
    stats={}

    for category in statistics.get("categories",[]):
        for stat in category.get("stats",[]):
            stats[stat["name"]]=stat.get("value")
    return stats 


if __name__ == "__main__":
    data = load_raw_data()

    match = transform_match(data)
    teams = transform_teams(data)
    players = transform_players(data)
    player_teams = transform_player_teams(data)
    tournament=transform_tournament(data)
    innings=transform_innings(data)

    
    print("TRANSFORMED MATCH:")
    print(json.dumps(match, indent=4))

    print("\nTRANSFORMED TEAMS:")
    print(json.dumps(teams, indent=4))

    print("\nTRANSFORMED PLAYERS:")
    print(json.dumps(players, indent=4))

    print("\nTRANSFORMED PLAYER TEAMS:")
    print(json.dumps(player_teams, indent=4))

    print("\n TRANSFORMED TOURNAMENT:")
    print(json.dumps(tournament,indent=4))

    print("\n TRANSFORMED INNINGS:")
    print(json.dumps(innings, indent=4))

if __name__ == "__main__":
    data = load_raw_data()

    sample_player = data["rosters"][1]["roster"][10]

    period = sample_player["linescores"][0]
    statistics = period["linescores"][0]["statistics"]

    extracted_stats = extract_player_statistics(statistics)

    print("EXTRACTED PLAYER STATISTICS:")
    print(json.dumps(extracted_stats, indent=4))