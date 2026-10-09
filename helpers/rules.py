from config import (
    BUFFER_GAP,
    MAX_DURATION_MINUTES,
    MIN_DURATION_MINUTES,
    PERFORMANCE_ID_FORMAT,
    ArtistRole,
)
from helpers.data import get_artist_map, get_venue_map
from helpers.time import (
    parse_date,
    performance_end,
    performance_festival_day,
    performance_start,
)


def get_performance_id(perf: dict) -> str:
    start_dt = performance_start(perf)
    return f"{perf['venue']}-{start_dt.strftime(PERFORMANCE_ID_FORMAT)}"


def get_artists_in_performance(perf: dict) -> set[str]:
    involved = set()
    if perf.get(ArtistRole.SOLO):
        involved.add(perf[ArtistRole.SOLO])
    if perf.get(ArtistRole.HOST):
        involved.add(perf[ArtistRole.HOST])
    if "acts" in perf:
        involved.update(perf["acts"])
    if perf.get(ArtistRole.TEACHER):
        involved.add(perf[ArtistRole.TEACHER])
    return involved


def validate_performance(festival: dict, new_perf: dict) -> None:
    venues = get_venue_map(festival)
    artists = get_artist_map(festival)

    # 1. Venue & artist exist
    if new_perf["venue"] not in venues:
        raise ValueError(f"Unknown venue '{new_perf['venue']}'.")
    if new_perf.get("artist") and new_perf["artist"] not in artists:
        raise ValueError(f"Unknown artist '{new_perf['artist']}'.")

    # 2. Duration limits
    duration = new_perf["duration_minutes"]
    if not (MIN_DURATION_MINUTES <= duration <= MAX_DURATION_MINUTES):
        raise ValueError(
            f"Duration must be between {MIN_DURATION_MINUTES} and {MAX_DURATION_MINUTES} minutes, got {duration}."
        )

    # 3. Festival day bounds
    fest_day = performance_festival_day(new_perf)
    first_day = parse_date(festival["first_day"])
    last_day = parse_date(festival["last_day"])
    if not (first_day <= fest_day <= last_day):
        raise ValueError(f"{fest_day} is not a day of the festival.")

    # 4. Overlap & buffer checks
    new_start = performance_start(new_perf)
    new_end = performance_end(new_perf)
    new_artists = get_artists_in_performance(new_perf)

    for other in festival["performances"]:
        other_start = performance_start(other)
        other_end = performance_end(other)

        conflict = (new_start < other_end + BUFFER_GAP) and (
            other_start < new_end + BUFFER_GAP
        )
        if not conflict:
            continue

        if other["venue"] == new_perf["venue"]:
            venue_name = venues[new_perf["venue"]]
            raise ValueError(
                f"{venue_name} is busy with {other['title']} "
                f"({other_start:%Y-%m-%d %H:%M}-{other_end:%H:%M})."
            )

        other_artists = get_artists_in_performance(other)
        shared_artists = new_artists.intersection(other_artists)
        if shared_artists:
            artist_slug = next(iter(shared_artists))
            artist_name = artists.get(artist_slug, artist_slug)
            raise ValueError(f"{artist_name} is on stage in {other['title']}.")