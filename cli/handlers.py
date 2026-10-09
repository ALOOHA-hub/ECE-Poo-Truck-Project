import sys
import uvicorn

from config import DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT
from helpers.formatters import (
    format_artist_schedule,
    format_now,
    format_programme,
    format_summary,
    format_venues,
)
from helpers.time import parse_datetime
from models import SoloShow
from repositories import FestivalRepository


def handle_summary(repo: FestivalRepository) -> None:
    raw = repo.load_raw()
    print(format_summary(raw))


def handle_venues(repo: FestivalRepository) -> None:
    raw = repo.load_raw()
    print(format_venues(raw))


def handle_programme(repo: FestivalRepository, day: str) -> None:
    raw = repo.load_raw()
    print(format_programme(raw, day))


def handle_artist(repo: FestivalRepository, slug: str) -> None:
    raw = repo.load_raw()
    print(format_artist_schedule(raw, slug))


def handle_now(repo: FestivalRepository, moment: str) -> None:
    raw = repo.load_raw()
    print(format_now(raw, moment))


def handle_add(repo: FestivalRepository) -> None:
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

    festival = repo.get_festival()
    festival.add_performance(new_show)
    repo.save_festival(festival)

    print(f"Added: {new_show.id}")


def handle_cancel(repo: FestivalRepository, perf_id: str) -> None:
    festival = repo.get_festival()
    cancelled = festival.cancel_performance(perf_id)
    repo.save_festival(festival)
    print(f"Cancelled: {cancelled.title}")


def handle_serve(host: str = DEFAULT_SERVER_HOST, port: int = DEFAULT_SERVER_PORT) -> None:
    uvicorn.run("api:app", host=host, port=port, reload=True)