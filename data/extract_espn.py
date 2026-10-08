import json
from pathlib import Path

import requests

EVENT_ID="1544864"
LEAGUE_ID="8043"

ESPN_URL = (
    f"https://site.web.api.espn.com/apis/site/v2/sports/cricket/"
    f"{LEAGUE_ID}/summary?event={EVENT_ID}"
)

OUTPUT_FILE = Path(__file__).parent / "raw" / f"{EVENT_ID}.json"

def extract_match_data():
    response=requests.get(ESPN_URL,timeout=20)

    response.raise_for_status()

    data=response.json()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w",encoding="utf=8") as file:
        json.dump(data,file,indent=4,ensure_ascii=False)

    print(f"Match data extracted successfully.")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_match_data()


