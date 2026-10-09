import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from config import DEFAULT_DATA_PATH, PerformanceKind
from helpers.slug import slugify
from models import Artist, Performance, Venue


@dataclass
class FestivalData:
    raw_data: dict
    venues: list[Venue]
    artists: list[Artist]
    performances: list[Performance]

    @property
    def venues_by_slug(self) -> dict[str, Venue]:
        return {v.slug: v for v in self.venues}

    @property
    def artists_by_slug(self) -> dict[str, Artist]:
        return {a.slug: a for a in self.artists}

    @property
    def performances_by_id(self) -> dict[str, Performance]:
        return {p.id: p for p in self.performances}


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


def load_domain_objects(path: Path = DEFAULT_DATA_PATH) -> FestivalData:
    raw = load_festival(path)

    venues = [
        Venue(
            name=v["name"],
            capacity=v["capacity"],
            address=v["address"],
        )
        for v in raw["venues"]
    ]

    artists = [
        Artist(
            name=a["name"],
            bio=a.get("bio", ""),
            photo_url=a.get("photo_url", ""),
        )
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

    return FestivalData(
        raw_data=raw,
        venues=venues,
        artists=artists,
        performances=performances,
    )


def get_venue_map(festival: dict) -> dict[str, str]:
    return {slugify(venue["name"]): venue["name"] for venue in festival["venues"]}


def get_artist_map(festival: dict) -> dict[str, str]:
    return {slugify(artist["name"]): artist["name"] for artist in festival["artists"]}


def get_festival_metadata(festival: dict) -> dict:
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