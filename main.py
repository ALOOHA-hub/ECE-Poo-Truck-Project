import json
from pathlib import Path


def main() -> None:
    data_path = Path("data/festival.json")
    with open(data_path, "r", encoding="utf-8") as file:
        festival = json.load(file)

    # --- Step 02: Venue slug mapping ---
    venue_names: dict[str, str] = {}
    for venue in festival["venues"]:
        # Generate slug by lowercasing, replacing accents, and substituting spaces
        slug = venue["name"].lower().replace("é", "e").replace(" ", "-")
        venue_names[slug] = venue["name"]

    # --- Extract unique sorted festival days ---
    days: list[str] = []
    for perf in festival["performances"]:
        perf_day = perf["start"][:10]
        if perf_day not in days:
            days.append(perf_day)
    days.sort()

    # --- Prompt user until valid ---
    day = input("Day (YYYY-MM-DD): ").strip()
    while day not in days:
        print(f"No performance on '{day}'. Days: {', '.join(days)}")
        day = input("Day (YYYY-MM-DD): ").strip()

    # --- Display programme for the chosen day ---
    print(f"Programme for {day}:")
    for perf in festival["performances"]:
        if perf["start"][:10] == day:
            time = perf["start"][11:]
            venue_name = venue_names.get(perf["venue"], perf["venue"])
            title = perf["title"]
            kind = perf["kind"]
            print(f"{time} | {venue_name} | {title} ({kind})")


if __name__ == "__main__":
    main()