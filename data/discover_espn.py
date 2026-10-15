
import requests

DISCOVERY_URL = (
    "https://site.api.espn.com/apis/personalized/v2/"
    "scoreboard/header"
)

PARAMS = {
    "sport": "cricket",
    "region": "in",
    "tz": "Asia/Calcutta",
}


def discover_competitions():
    response = requests.get(
        DISCOVERY_URL,
        params=PARAMS,
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()
    sports = data.get("sports", [])

    if not sports:
        print("No cricket sports data returned.")
        print("Response keys:", list(data.keys()))
        return

    leagues = sports[0].get("leagues", [])

    if not leagues:
        print("No competitions found in the response.")
        return

    print(f"Competitions returned: {len(leagues)}\n")

    for league in leagues:
        league_id = league.get("id")
        name = league.get("name", "Unknown competition")
        events = league.get("events", [])

        print(f"Competition: {name}")
        print(f"League ID: {league_id}")
        print(f"Events returned: {len(events)}")

        for event in events[:5]:
            print(
                f"  Event ID: {event.get('id')} | "
                f"Match: {event.get('name', 'Name unavailable')}"
            )

        print("-" * 55)


if __name__ == "__main__":
    try:
        discover_competitions()
    except requests.RequestException as error:
        print(f"ESPN request failed: {error}")
    except (ValueError, KeyError, TypeError) as error:
        print(f"Unexpected response format: {error}")
