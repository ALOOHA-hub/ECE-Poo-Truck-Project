from config import MAX_UPCOMING_PREVIEWS, ArtistRole
from helpers.data import get_venue_map
from helpers.slug import slugify
from helpers.time import (
    parse_date,
    parse_datetime,
    performance_end,
    performance_festival_day,
    performance_start,
)


def format_summary(festival: dict) -> str:
    name = festival["name"]
    first = festival["first_day"]
    last = festival["last_day"]
    venues = len(festival["venues"])
    artists = len(festival["artists"])
    performances = len(festival["performances"])
    return (
        f"{name}\n"
        f"From {first} to {last}\n"
        f"{venues} venues, {artists} artists, {performances} performances"
    )


def format_venues(festival: dict) -> str:
    lines = []
    total_seats = 0
    for venue in festival["venues"]:
        slug = slugify(venue["name"])
        seats = venue["capacity"]
        total_seats += seats
        lines.append(f"{slug}: {venue['name']}, {seats} seats")
    lines.append(f"Total: {total_seats} seats")
    return "\n".join(lines)


def format_programme(festival: dict, day_str: str) -> str:
    target_day = parse_date(day_str)
    venue_map = get_venue_map(festival)

    matching = [
        perf
        for perf in festival["performances"]
        if performance_festival_day(perf) == target_day
    ]
    matching.sort(key=performance_start)

    lines = [f"Programme for {target_day:%A %d %B}:"]
    for perf in matching:
        start = performance_start(perf)
        end = performance_end(perf)
        venue_name = venue_map.get(perf["venue"], perf["venue"])
        lines.append(
            f"{start:%H:%M}-{end:%H:%M} | {venue_name} | {perf['title']} ({perf['kind']})"
        )
    return "\n".join(lines)


def format_artist_schedule(festival: dict, artist_slug: str) -> str:
    artist_name = None
    for artist in festival["artists"]:
        if slugify(artist["name"]) == artist_slug:
            artist_name = artist["name"]
            break

    if artist_name is None:
        return f"No artist '{artist_slug}'."

    venue_map = get_venue_map(festival)
    lines = [artist_name]

    matching = []
    for perf in festival["performances"]:
        role = None
        if perf.get("artist") == artist_slug:
            role = ArtistRole.SOLO
        elif perf.get("host") == artist_slug:
            role = ArtistRole.HOST
        elif artist_slug in perf.get("acts", []):
            role = ArtistRole.ACT
        elif perf.get("teacher") == artist_slug:
            role = ArtistRole.TEACHER

        if role:
            matching.append((perf, role.value))

    matching.sort(key=lambda item: performance_start(item[0]))

    for perf, role_str in matching:
        start = performance_start(perf)
        end = performance_end(perf)
        day_date = performance_festival_day(perf)
        day_label = f"{day_date:%a} {day_date.day}"
        venue_name = venue_map.get(perf["venue"], perf["venue"])
        lines.append(
            f"{day_label} {start:%H:%M}-{end:%H:%M} | {venue_name} | {perf['title']} ({role_str})"
        )

    return "\n".join(lines)


def format_now(festival: dict, moment_str: str) -> str:
    at = parse_datetime(moment_str)
    venue_map = get_venue_map(festival)

    currently_playing = []
    upcoming = []

    for perf in festival["performances"]:
        start = performance_start(perf)
        end = performance_end(perf)
        if start <= at < end:
            currently_playing.append(perf)
        elif at <= start:
            upcoming.append(perf)

    upcoming.sort(key=performance_start)
    next_up = upcoming[:MAX_UPCOMING_PREVIEWS]

    lines = [f"On stage at {at:%Y-%m-%d %H:%M}:"]
    for perf in currently_playing:
        end = performance_end(perf)
        venue_name = venue_map.get(perf["venue"], perf["venue"])
        lines.append(f"- {perf['title']} at {venue_name}, until {end:%H:%M}")

    if next_up:
        lines.append("Up next:")
        for perf in next_up:
            start = performance_start(perf)
            end = performance_end(perf)
            venue_name = venue_map.get(perf["venue"], perf["venue"])
            lines.append(
                f"- {start:%H:%M}-{end:%H:%M} | {venue_name} | {perf['title']} ({perf['kind']})"
            )

    return "\n".join(lines)


def format_usage() -> str:
    return (
        "Usage:\n"
        "  uv run main.py\n"
        "  uv run main.py venues\n"
        "  uv run main.py programme <YYYY-MM-DD>\n"
        "  uv run main.py artist <artist-slug>\n"
        "  uv run main.py now <YYYY-MM-DDTHH:MM>\n"
        "  uv run main.py add\n"
        "  uv run main.py cancel <ID>"
    )