import json
from pathlib import Path

from helpers.slug import slugify

DEFAULT_DATA_PATH = Path("data/festival.json")


def load_festival(path: Path = DEFAULT_DATA_PATH) -> dict:
    """Load and parse festival JSON data."""
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_venue_map(festival: dict) -> dict[str, str]:
    """Return a mapping of venue slug -> venue display name."""
    return {slugify(venue["name"]): venue["name"] for venue in festival["venues"]}