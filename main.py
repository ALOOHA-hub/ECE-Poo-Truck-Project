import sys

from helpers import (
    format_artist_schedule,
    format_now,
    format_programme,
    format_summary,
    format_usage,
    format_venues,
    load_festival,
    load_festival_aggregate,
    save_festival,
)
from helpers.time import parse_datetime
from models import Festival, SoloShow


def handle_add(festival: Festival) -> None:
    title = input("Title: ").strip()
    artist = input("Artist (slug): ").strip()
    venue = input("Venue (slug): ").strip()
    start_str = input("Start (YYYY-MM-DDTHH:MM): ").strip()
    raw_duration = input("Duration (minutes): ").strip()

    try:
        duration = int(raw_duration)
    except ValueError:
        raise ValueError(f"'{raw_duration}' is not a number of minutes.") from None

    start_dt = parse_datetime(start_str)

    new_show = SoloShow(
        title=title,
        venue=venue,
        start=start_dt,
        duration_minutes=duration,
        artist=artist,
    )

    festival.add_performance(new_show)
    save_festival(festival)

    print(f"Added: {new_show.id}")


def handle_cancel(festival: Festival, perf_id: str) -> None:
    cancelled = festival.cancel_performance(perf_id)
    save_festival(festival)
    print(f"Cancelled: {cancelled.title}")


def run() -> None:
    args = sys.argv[1:]

    if len(args) == 0:
        festival_dict = load_festival()
        print(format_summary(festival_dict))
    elif args[0] == "venues" and len(args) == 1:
        festival_dict = load_festival()
        print(format_venues(festival_dict))
    elif args[0] == "programme" and len(args) == 2:
        festival_dict = load_festival()
        print(format_programme(festival_dict, args[1]))
    elif args[0] == "artist" and len(args) == 2:
        festival_dict = load_festival()
        print(format_artist_schedule(festival_dict, args[1]))
    elif args[0] == "now" and len(args) == 2:
        festival_dict = load_festival()
        print(format_now(festival_dict, args[1]))
    elif args[0] == "add" and len(args) == 1:
        festival_agg = load_festival_aggregate()
        handle_add(festival_agg)
    elif args[0] == "cancel" and len(args) == 2:
        festival_agg = load_festival_aggregate()
        handle_cancel(festival_agg, args[1])
    else:
        print(format_usage())


def main() -> None:
    try:
        run()
    except (ValueError, KeyError) as error:
        print(f"Error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()