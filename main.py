import json
from pathlib import Path


def main() -> None:
    data_path = Path("data/festival.json")
    with open(data_path, "r", encoding="utf-8") as file:
        festival = json.load(file)

    name = festival["name"]
    first_day = festival["first_day"]
    last_day = festival["last_day"]
    venues_count = len(festival["venues"])
    artists_count = len(festival["artists"])
    performances_count = len(festival["performances"])

    print(name)
    print(f"From {first_day} to {last_day}")
    print(f"{venues_count} venues, {artists_count} artists, {performances_count} performances")


if __name__ == "__main__":
    main()