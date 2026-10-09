from dataclasses import dataclass, field

from config import DATETIME_FORMAT, ArtistRole, PerformanceKind
from models.artist import Artist
from models.performances.base import Performance
from models.venue import Venue


@dataclass
class Workshop(Performance):
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

    def places_left(self, venue: Venue) -> int:
        return max(0, self.effective_capacity(venue) - len(self.participants))

    def register(self, participant_name: str, venue: Venue) -> None:
        clean_name = participant_name.strip()
        if not clean_name:
            raise ValueError("Participant name cannot be empty.")
        if clean_name in self.participants:
            raise ValueError(f"'{clean_name}' is already registered for this workshop.")
        if self.places_left(venue) <= 0:
            raise ValueError("Workshop is full.")
        self.participants.append(clean_name)

    def unregister(self, participant_name: str) -> None:
        clean_name = participant_name.strip()
        if clean_name not in self.participants:
            raise ValueError(f"'{clean_name}' is not registered for this workshop.")
        self.participants.remove(clean_name)

    def validate_specific_rules(self, venue: Venue) -> None:
        if self.max_participants < 1:
            raise ValueError(
                f"A workshop must have at least 1 place, got {self.max_participants}."
            )

    def to_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "title": self.title,
            "venue": self.venue,
            "start": self.start.strftime(DATETIME_FORMAT),
            "duration_minutes": self.duration_minutes,
            "description": self.description,
            "teacher": self.teacher,
            "max_participants": self.max_participants,
            "participants": list(self.participants),
        }

    def to_view(
        self,
        venues_by_slug: dict[str, Venue],
        artists_by_slug: dict[str, Artist],
    ) -> dict:
        view = super().to_view(venues_by_slug, artists_by_slug)
        venue_obj = venues_by_slug.get(self.venue)
        places = self.places_left(venue_obj) if venue_obj else 0

        view["teacher"] = self.teacher
        view["max_participants"] = self.max_participants
        view["participants"] = list(self.participants)
        view["places_left"] = places
        return view