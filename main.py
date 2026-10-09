import json
from pathlib import Path


def main() -> None:
    data_path = Path("data/festival.json")
    with open(data_path, "r", encoding="utf-8") as file:
        festival = json.load(file)

    # --- Step 00: Summary ---
    name = festival["name"]
    first_day = festival["first_day"]
    last_day = festival["last_day"]
    venues_count = len(festival["venues"])
    artists_count = len(festival["artists"])
    performances_count = len(festival["performances"])

    print(name)
    print(f"From {first_day} to {last_day}")
    print(f"{venues_count} venues, {artists_count} artists, {performances_count} performances\n")

    # --- Step 01: Questions ---

    # 1. Venues, seats, address, and total seats
    print("Venues:")
    total_seats = 0
    for venue in festival["venues"]:
        print(f"- {venue['name']}: {venue['capacity']} seats ({venue['address']})")
        total_seats += venue["capacity"]
    print(f"Total: {total_seats} seats\n")

    # 2. Performance count by kind
    kinds: dict[str, int] = {}
    for perf in festival["performances"]:
        kind = perf["kind"]
        kinds[kind] = kinds.get(kind, 0) + 1
    for kind, count in kinds.items():
        print(f"{kind}: {count}")
    print()

    # 3. Performances at Le Kiosque
    print("At Le Kiosque:")
    for perf in festival["performances"]:
        if perf["venue"] == "le-kiosque":
            print(f"- {perf['start']} {perf['title']}")
    print()

    # 4. Longest performance
    longest = max(festival["performances"], key=lambda p: p["duration_minutes"])
    print(f"Longest: {longest['title']} ({longest['duration_minutes']} min)\n")

    # 5. Workshop registrations
    for perf in festival["performances"]:
        if perf["kind"] == "workshop":
            day = perf["start"][:10]
            registered = len(perf["participants"])
            max_participants = perf["max_participants"]
            print(f"{perf['title']} on {day}: {registered}/{max_participants} registered")
    print()

    # 6. Artists on stage the most often
    artist_counts: dict[str, int] = {}
    for perf in festival["performances"]:
        on_stage: list[str] = []
        if "artist" in perf:
            on_stage.append(perf["artist"])
        if "host" in perf:
            on_stage.append(perf["host"])
        if "acts" in perf:
            on_stage.extend(perf["acts"])
        if "teacher" in perf:
            on_stage.append(perf["teacher"])

        for artist in on_stage:
            artist_counts[artist] = artist_counts.get(artist, 0) + 1

    max_appearances = max(artist_counts.values())
    top_artists = [artist for artist, count in artist_counts.items() if count == max_appearances]
    print(f"On stage {max_appearances} times: {', '.join(top_artists)}")


if __name__ == "__main__":
    main()