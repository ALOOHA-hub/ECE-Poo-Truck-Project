"""Storage abstractions and implementations for festival data persistence."""

from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import date, datetime
import json
from pathlib import Path
from typing import Any

from config import DEFAULT_DATA_PATH, PerformanceKind
from models import (
    Artist,
    Festival,
    Lineup,
    Performance,
    SoloShow,
    Venue,
    Workshop,
)
from models.exceptions import NotFoundError, ValidationError


class BaseFestivalRepository(ABC):
    """Abstract storage interface defining the persistence contract."""

    @abstractmethod
    def load_raw(self) -> dict[str, Any]:
        """Load the raw storage representation."""

    @abstractmethod
    def save_raw(self, payload: dict[str, Any]) -> None:
        """Persist the raw storage representation."""

    def get_festival(self) -> Festival:
        """Hydrate the Festival domain aggregate."""
        raw = self.load_raw()

        venues = [
            Venue(name=v["name"], capacity=v["capacity"], address=v["address"])
            for v in raw.get("venues", [])
        ]

        artists = [
            Artist(name=a["name"], bio=a.get("bio", ""), photo_url=a.get("photo_url", ""))
            for a in raw.get("artists", [])
        ]

        factories = {
            PerformanceKind.SOLO: lambda p: SoloShow(
                title=p["title"],
                venue=p["venue"],
                start=datetime.fromisoformat(p["start"]),
                duration_minutes=p["duration_minutes"],
                description=p.get("description", ""),
                artist=p.get("artist", ""),
                min_age=p.get("min_age", 0),
            ),
            PerformanceKind.LINEUP: lambda p: Lineup(
                title=p["title"],
                venue=p["venue"],
                start=datetime.fromisoformat(p["start"]),
                duration_minutes=p["duration_minutes"],
                description=p.get("description", ""),
                host=p.get("host", ""),
                acts=list(p.get("acts", [])),
            ),
            PerformanceKind.WORKSHOP: lambda p: Workshop(
                title=p["title"],
                venue=p["venue"],
                start=datetime.fromisoformat(p["start"]),
                duration_minutes=p["duration_minutes"],
                description=p.get("description", ""),
                teacher=p.get("teacher", ""),
                max_participants=p.get("max_participants", 1),
                participants=list(p.get("participants", [])),
            ),
        }

        performances: list[Performance] = []
        for p in raw.get("performances", []):
            kind = PerformanceKind(p["kind"])
            performances.append(factories[kind](p))

        return Festival(
            name=raw["name"],
            first_day=date.fromisoformat(raw["first_day"]),
            last_day=date.fromisoformat(raw["last_day"]),
            venues=venues,
            artists=artists,
            performances=performances,
        )

    def save_festival(self, festival: Festival) -> None:
        """Serialize and persist the Festival aggregate."""
        self.save_raw(festival.to_dict())


class JsonFestivalRepository(BaseFestivalRepository):
    """Filesystem-backed JSON repository implementation."""

    def __init__(self, data_path: Path | str = DEFAULT_DATA_PATH) -> None:
        self.data_path = Path(data_path)

    def load_raw(self) -> dict[str, Any]:
        try:
            with open(self.data_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            raise NotFoundError(f"Data file '{self.data_path}' not found.") from None
        except json.JSONDecodeError as err:
            raise ValidationError(f"{self.data_path} is damaged (line {err.lineno}).") from None

    def save_raw(self, payload: dict[str, Any]) -> None:
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)


class MemoryFestivalRepository(BaseFestivalRepository):
    """In-memory repository used for test isolation without disk side-effects."""

    def __init__(self, initial_state: dict[str, Any] | None = None) -> None:
        self._state: dict[str, Any] = deepcopy(initial_state) if initial_state else {}

    def load_raw(self) -> dict[str, Any]:
        return deepcopy(self._state)

    def save_raw(self, payload: dict[str, Any]) -> None:
        self._state = deepcopy(payload)


# Backwards compatibility alias for existing code and tests
FestivalRepository = JsonFestivalRepository