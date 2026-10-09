from dataclasses import dataclass

from config import ArtistRole, PerformanceKind
from models.artist import Artist
from models.performances.base import Performance
from models.venue import Venue


@dataclass
class SoloShow(Performance):
    """Solo stand-up performance by a single artist."""

    artist: str = ""
    min_age: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.kind = PerformanceKind.SOLO

    def artists_involved(self) -> set[str]:
        return {self.artist} if self.artist else set()

    def role_of(self, artist_slug: str) -> ArtistRole | None:
        return ArtistRole.SOLO if self.artist == artist_slug else None

    def get_summary(self, artists_by_slug: dict[str, Artist]) -> str:
        artist_obj = artists_by_slug.get(self.artist)
        return artist_obj.name if artist_obj else self.artist

    def validate_specific_rules(self, venue: Venue) -> None:
        if not (0 <= self.min_age <= 18):
            raise ValueError(f"Minimum age must be between 0 and 18, got {self.min_age}.")

    def to_view(
        self,
        venues_by_slug: dict[str, Venue],
        artists_by_slug: dict[str, Artist],
    ) -> dict:
        view = super().to_view(venues_by_slug, artists_by_slug)
        view["artist"] = self.artist
        view["min_age"] = self.min_age
        return view