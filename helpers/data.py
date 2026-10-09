import json
from datetime import date, timedelta
from pathlib import Path

from config import DEFAULT_DATA_PATH
from helpers.slug import slugify


def load_festival(path: Path = DEFAULT_DATA_PATH) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise ValueError(f"Data file '{path}' not found.") from None
    except json.JSONDecodeError as err:
        raise ValueError(f"{path} is damaged (line {err.lineno}).") from None


def save_festival(festival: dict, path: Path = DEFAULT_DATA_PATH) -> None:
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(festival, file, ensure_ascii=False, indent=2)


def get_venue_map(festival: dict) -> dict[str, str]:
    return {slugify(venue["name"]): venue["name"] for venue in festival["venues"]}


def get_artist_map(festival: dict) -> dict[str, str]:
    return {slugify(artist["name"]): artist["name"] for artist in festival["artists"]}


# --- API Query Extractors ---


def get_festival_metadata(festival: dict) -> dict:
    """Return festival details including the complete array of ISO dates."""
    first_dt = date.fromisoformat(festival["first_day"])
    last_dt = date.fromisoformat(festival["last_day"])

    days: list[str] = []
    current = first_dt
    while current <= last_dt:
        days.append(current.isoformat())
        current += timedelta(days=1)

    return {
        "name": festival["name"],
        "first_day": festival["first_day"],
        "last_day": festival["last_day"],
        "days": days,
    }


def get_venues_view(festival: dict) -> list[dict]:
    """Return venues with their computed slugs in original file order."""
    return [
        {
            "slug": slugify(v["name"]),
            "name": v["name"],
            "capacity": v["capacity"],
            "address": v["address"],
        }
        for v in festival["venues"]
    ]


def get_artists_view(festival: dict) -> list[dict]:
    """Return all artists sorted alphabetically by their slug."""
    artists = [
        {
            "slug": slugify(a["name"]),
            "name": a["name"],
            "bio": a.get("bio", ""),
            "photo_url": a.get("photo_url", ""),
        }
        for a in festival["artists"]
    ]
    return sorted(artists, key=lambda a: a["slug"])