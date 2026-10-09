import json
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