from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from config import DEFAULT_DATA_PATH
from helpers.slug import slugify

if TYPE_CHECKING:
    from models import Festival


def load_festival(path: Path = DEFAULT_DATA_PATH) -> dict:
    from repositories import FestivalRepository

    return FestivalRepository(path).load_raw()


def save_festival(festival_or_dict: Any, path: Path = DEFAULT_DATA_PATH) -> None:
    from repositories import FestivalRepository

    FestivalRepository(path).save_festival(festival_or_dict)


def load_festival_aggregate(path: Path = DEFAULT_DATA_PATH) -> Festival:
    from repositories import FestivalRepository

    return FestivalRepository(path).get_festival()


def get_venue_map(festival: dict) -> dict[str, str]:
    return {slugify(venue["name"]): venue["name"] for venue in festival["venues"]}


def get_artist_map(festival: dict) -> dict[str, str]:
    return {slugify(artist["name"]): artist["name"] for artist in festival["artists"]}