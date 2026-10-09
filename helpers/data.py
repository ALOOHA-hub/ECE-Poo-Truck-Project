import json
from datetime import date, datetime
from pathlib import Path

from config import DEFAULT_DATA_PATH, PerformanceKind
from helpers.slug import slugify


def load_festival(path: Path = DEFAULT_DATA_PATH) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise ValueError(f"Data file '{path}' not found.") from None
    except json.JSONDecodeError as err:
        raise ValueError(f"{path} is damaged (line {err.lineno}).") from None


def save_festival(festival_dict: dict, path: Path = DEFAULT_DATA_PATH) -> None:
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(festival_dict, file, ensure_ascii=False, indent=2)


def get_venue_map(festival: dict) -> dict[str, str]:
    return {slugify(venue["name"]): venue["name"] for venue in festival["venues"]}


def get_artist_map(festival: dict) -> dict[str, str]:
    return {slugify(artist["name"]): artist["name"] for artist in festival["artists"]}


def load_festival_aggregate(path: Path = DEFAULT_DATA_PATH):
    # Imported locally to avoid circular dependencies during module loading
    from models import Artist, Festival, Performance, Venue

    raw = load_festival(path)

    venues = [
        Venue(name=v["name"], capacity=v["capacity"], address=v["address"])
        for v in raw["venues"]
    ]

    artists = [
        Artist(name=a["name"], bio=a.get("bio", ""), photo_url=a.get("photo_url", ""))
        for a in raw["artists"]
    ]

    performances = []
    for p in raw["performances"]:
        performances.append(
            Performance(
                kind=PerformanceKind(p["kind"]),
                title=p["title"],
                venue=p["venue"],
                start=datetime.fromisoformat(p["start"]),
                duration_minutes=p["duration_minutes"],
                description=p.get("description", ""),
                artist=p.get("artist"),
                min_age=p.get("min_age"),
                host=p.get("host"),
                acts=p.get("acts", []),
                teacher=p.get("teacher"),
                max_participants=p.get("max_participants"),
                participants=p.get("participants", []),
            )
        )

    return Festival(
        name=raw["name"],
        first_day=date.fromisoformat(raw["first_day"]),
        last_day=date.fromisoformat(raw["last_day"]),
        venues=venues,
        artists=artists,
        performances=performances,
    )