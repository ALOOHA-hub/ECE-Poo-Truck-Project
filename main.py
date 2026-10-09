import sys

from helpers import (
    format_artist_schedule,
    format_programme,
    format_summary,
    format_usage,
    format_venues,
    load_festival,
)


def main() -> None:
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
    else:
        print(format_usage())


if __name__ == "__main__":
    main()