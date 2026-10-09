from dataclasses import dataclass, field

from config import DATETIME_FORMAT, ArtistRole, PerformanceKind
from models.artist import Artist
from models.performances.base import Performance
from models.venue import Venue


@dataclass
class Lineup(Performance):
    host: str = ""
    acts: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.kind = PerformanceKind.LINEUP

    def artists_involved(self) -> set[str]:
        slugs = set(self.acts)
        if self.host:
            slugs.add(self.host)
        return slugs

    def role_of(self, artist_slug: str) -> ArtistRole | None:
        if self.host == artist_slug:
            return ArtistRole.HOST
        if artist_slug in self.acts:
            return ArtistRole.ACT
        return None

    def get_summary(self, artists_by_slug: dict[str, Artist]) -> str:
        host_obj = artists_by_slug.get(self.host)
        host_name = host_obj.name if host_obj else self.host
        act_names = [
            artists_by_slug[a].name if a in artists_by_slug else a for a in self.acts
        ]
        return f"hosted by {host_name}, with {', '.join(act_names)}"

    def validate_specific_rules(self, venue: Venue) -> None:
        if len(self.acts) < 2:
            raise ValueError(f"A lineup needs at least 2 acts, got {len(self.acts)}.")
        if len(self.acts) != len(set(self.acts)):
            raise ValueError("A lineup cannot have duplicate acts.")
        if self.host in self.acts:
            raise ValueError(f"The host '{self.host}' cannot also be an act.")

        min_time = len(self.acts) * 10 + (len(self.acts) - 1) * 3
        if self.duration_minutes < min_time:
            raise ValueError(
                f"Lineup with {len(self.acts)} acts requires at least {min_time} minutes, got {self.duration_minutes}."
            )

    def to_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "title": self.title,
            "venue": self.venue,
            "start": self.start.strftime(DATETIME_FORMAT),
            "duration_minutes": self.duration_minutes,
            "description": self.description,
            "host": self.host,
            "acts": list(self.acts),
        }

    def to_view(
        self,
        venues_by_slug: dict[str, Venue],
        artists_by_slug: dict[str, Artist],
    ) -> dict:
        view = super().to_view(venues_by_slug, artists_by_slug)
        view["host"] = self.host
        view["acts"] = self.acts
        return view