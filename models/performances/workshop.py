from dataclasses import dataclass, field

from config import ArtistRole, PerformanceKind
from models.artist import Artist
from models.performances.base import Performance
from models.venue import Venue


@dataclass
class Workshop(Performance):
    """Interactive class taught by an artist with participant limits."""

    teacher: str = ""
    max_participants: int = 0
    participants: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.kind = PerformanceKind.WORKSHOP

    def artists_involved(self) -> set[str]:
        return {self.teacher} if self.teacher else set()

    def role_of(self, artist_slug: str) -> ArtistRole | None:
        return ArtistRole.TEACHER if self.teacher == artist_slug else None

    def get_summary(self, artists_by_slug: dict[str, Artist]) -> str:
        teacher_obj = artists_by_slug.get(self.teacher)
        teacher_name = teacher_obj.name if teacher_obj else self.teacher
        return f"with {teacher_name}, {len(self.participants)}/{self.max_participants} places taken"

    def effective_capacity(self, venue: Venue) -> int:
        return min(self.max_participants, venue.capacity)

    def validate_specific_rules(self, venue: Venue) -> None:
        if self.max_participants < 1:
            raise ValueError(
                f"A workshop must have at least 1 place, got {self.max_participants}."
            )

    def to_view(
        self,
        venues_by_slug: dict[str, Venue],
        artists_by_slug: dict[str, Artist],
    ) -> dict:
        view = super().to_view(venues_by_slug, artists_by_slug)
        venue_obj = venues_by_slug.get(self.venue)
        venue_cap = venue_obj.capacity if venue_obj else 0
        real_capacity = min(self.max_participants, venue_cap)
        places_left = max(0, real_capacity - len(self.participants))

        view["teacher"] = self.teacher
        view["max_participants"] = self.max_participants
        view["participants"] = self.participants
        view["places_left"] = places_left
        return view