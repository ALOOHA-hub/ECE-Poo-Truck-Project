from helpers.data import get_venue_map
from helpers.slug import slugify


def format_summary(festival: dict) -> str:
    """Return the step 00 festival overview."""
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
    """Return formatted venue list and total seats."""
    lines = []
    total_seats = 0
    for venue in festival["venues"]:
        slug = slugify(venue["name"])
        seats = venue["capacity"]
        total_seats += seats
        lines.append(f"{slug}: {venue['name']}, {seats} seats")
    lines.append(f"Total: {total_seats} seats")
    return "\n".join(lines)


def format_programme(festival: dict, day: str) -> str:
    """Return the programme for a specific festival day."""
    venue_map = get_venue_map(festival)
    lines = [f"Programme for {day}:"]
    for perf in festival["performances"]:
        if perf["start"][:10] == day:
            time = perf["start"][11:]
            venue_name = venue_map.get(perf["venue"], perf["venue"])
            lines.append(f"{time} | {venue_name} | {perf['title']} ({perf['kind']})")
    return "\n".join(lines)


def format_artist_schedule(festival: dict, artist_slug: str) -> str:
    """Return scheduled performances and roles for an artist."""
    artist_name = None
    for artist in festival["artists"]:
        if slugify(artist["name"]) == artist_slug:
            artist_name = artist["name"]
            break

    if artist_name is None:
        return f"No artist '{artist_slug}'."

    venue_map = get_venue_map(festival)
    lines = [artist_name]

    for perf in festival["performances"]:
        role = None
        if perf.get("artist") == artist_slug:
            role = "solo"
        elif perf.get("host") == artist_slug:
            role = "host"
        elif artist_slug in perf.get("acts", []):
            role = "act"
        elif perf.get("teacher") == artist_slug:
            role = "teacher"

        if role:
            date_time = f"{perf['start'][:10]} {perf['start'][11:]}"
            venue_name = venue_map.get(perf["venue"], perf["venue"])
            lines.append(f"{date_time} | {venue_name} | {perf['title']} ({role})")

    return "\n".join(lines)


def format_usage() -> str:
    """Return CLI usage help."""
    return (
        "Usage:\n"
        "  uv run main.py\n"
        "  uv run main.py venues\n"
        "  uv run main.py programme <YYYY-MM-DD>\n"
        "  uv run main.py artist <artist-slug>"
    )