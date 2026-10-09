from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from config import (
    DATE_FORMAT,
    FESTIVAL_DAY_OFFSET,
    PERFORMANCE_ID_FORMAT,
    TIME_FORMAT,
    ArtistRole,
    PerformanceKind,
)
from models.artist import Artist
from models.venue import Venue


@dataclass
class Performance(ABC):
    """Abstract base class for all festival performance kinds."""

    title: str
    venue: str  # venue slug
    start: datetime
    duration_minutes: int
    description: str = ""

    kind: PerformanceKind = field(init=False)

    def __post_init__(self) -> None:
        if type(self) is Performance:
            raise TypeError("Cannot instantiate abstract class Performance directly.")

    @property
    def end(self) -> datetime:
        return self.start + timedelta(minutes=self.duration_minutes)

    @property
    def festival_day(self) -> date:
        return (self.start - FESTIVAL_DAY_OFFSET).date()

    @property
    def id(self) -> str:
        return f"{self.venue}-{self.start.strftime(PERFORMANCE_ID_FORMAT)}"

    def __lt__(self, other: "Performance") -> bool:
        return (self.start, self.venue) < (other.start, other.venue)

    def __str__(self) -> str:
        return f"{self.start:%H:%M}-{self.end:%H:%M} | {self.venue} | {self.title} ({self.kind.value})"

    @abstractmethod
    def artists_involved(self) -> set[str]:
        """Return all artist slugs involved in this performance."""

    @abstractmethod
    def role_of(self, artist_slug: str) -> ArtistRole | None:
        """Return the role of a given artist in this performance."""

    @abstractmethod
    def get_summary(self, artists_by_slug: dict[str, Artist]) -> str:
        """Format the summary string using polymorphism."""

    @abstractmethod
    def validate_specific_rules(self, venue: Venue) -> None:
        """Check validation constraints unique to this performance kind."""

    def to_view(
        self,
        venues_by_slug: dict[str, Venue],
        artists_by_slug: dict[str, Artist],
    ) -> dict:
        venue_obj = venues_by_slug.get(self.venue)
        venue_name = venue_obj.name if venue_obj else self.venue
        capacity = venue_obj.capacity if venue_obj else 0

        return {
            "id": self.id,
            "kind": self.kind.value,
            "title": self.title,
            "venue": self.venue,
            "venue_name": venue_name,
            "start": self.start.strftime(f"{DATE_FORMAT}T{TIME_FORMAT}"),
            "end": self.end.strftime(f"{DATE_FORMAT}T{TIME_FORMAT}"),
            "duration_minutes": self.duration_minutes,
            "festival_day": self.festival_day.strftime(DATE_FORMAT),
            "description": self.description,
            "summary": self.get_summary(artists_by_slug),
            "capacity": capacity,
            "artists": [
                {"slug": s, "name": artists_by_slug[s].name}
                for s in self.artists_involved()
                if s in artists_by_slug
            ],
        }