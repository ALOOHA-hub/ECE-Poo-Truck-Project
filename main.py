import sys

from config import PerformanceKind
from helpers import (
    format_artist_schedule,
    format_now,
    format_programme,
    format_summary,
    format_usage,
    format_venues,
    get_performance_id,
    load_festival,
    save_festival,
    validate_performance,
)


def handle_add(festival: dict) -> None:
    title = input("Title: ").strip()
    artist = input("Artist (slug): ").strip()
    venue = input("Venue (slug): ").strip()
    start = input("Start (YYYY-MM-DDTHH:MM): ").strip()
    raw_duration = input("Duration (minutes): ").strip()

    try:
        duration = int(raw_duration)
    except ValueError:
        raise ValueError(f"'{raw_duration}' is not a number of minutes.") from None

    new_perf = {
        "kind": PerformanceKind.SOLO.value,
        "title": title,
        "venue": venue,
        "start": start,
        "duration_minutes": duration,
        "description": "",
        "artist": artist,
        "min_age": 0,
    }

    validate_performance(festival, new_perf)
    festival["performances"].append(new_perf)
    save_festival(festival)

    perf_id = get_performance_id(new_perf)
    print(f"Added: {perf_id}")


def handle_cancel(festival: dict, perf_id: str) -> None:
    for idx, perf in enumerate(festival["performances"]):
        if get_performance_id(perf) == perf_id:
            cancelled = festival["performances"].pop(idx)
            save_festival(festival)
            print(f"Cancelled: {cancelled['title']}")
            return
    raise ValueError(f"No performance with id '{perf_id}'.")


def run() -> None:
    festival = load_festival()
    args = sys.argv[1:]

    if len(args) == 0:
        print(format_summary(festival))
    elif args[0] == "venues" and len(args) == 1:
        print(format_venues(festival))
    elif args[0] == "programme" and len(args) == 2:
        print(format_programme(festival, args[1]))
    elif args[0] == "artist" and len(args) == 2:
        print(format_artist_schedule(festival, args[1]))
    elif args[0] == "now" and len(args) == 2:
        print(format_now(festival, args[1]))
    elif args[0] == "add" and len(args) == 1:
        handle_add(festival)
    elif args[0] == "cancel" and len(args) == 2:
        handle_cancel(festival, args[1])
    else:
        print(format_usage())


def main() -> None:
    try:
        run()
    except ValueError as error:
        print(f"Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()