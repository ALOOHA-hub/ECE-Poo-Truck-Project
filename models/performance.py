from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from dataclasses import dataclass
from helpers.slug import slugify


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
class Performance:
    kind: PerformanceKind
    title: str
    venue: str  # venue slug
    start: datetime
    duration_minutes: int
    description: str = ""

    # Solo fields
    artist: str | None = None
    min_age: int | None = None

    # Lineup fields
    host: str | None = None
    acts: list[str] = field(default_factory=list)

    # Workshop fields
    teacher: str | None = None
    max_participants: int | None = None
    participants: list[str] = field(default_factory=list)

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
        """Sort by start time, then by venue slug."""
        return (self.start, self.venue) < (other.start, other.venue)

    def __str__(self) -> str:
        return f"{self.start:%H:%M}-{self.end:%H:%M} | {self.venue} | {self.title} ({self.kind.value})"

    def involves(self, artist_slug: str) -> bool:
        if self.artist == artist_slug or self.host == artist_slug or self.teacher == artist_slug:
            return True
        return artist_slug in self.acts

    def role_of(self, artist_slug: str) -> ArtistRole | None:
        if self.artist == artist_slug:
            return ArtistRole.SOLO
        if self.host == artist_slug:
            return ArtistRole.HOST
        if artist_slug in self.acts:
            return ArtistRole.ACT
        if self.teacher == artist_slug:
            return ArtistRole.TEACHER
        return None

    def artists_involved(self) -> set[str]:
        """Return all artist slugs involved in this performance in any role."""
        slugs = set()
        if self.artist:
            slugs.add(self.artist)
        if self.host:
            slugs.add(self.host)
        slugs.update(self.acts)
        if self.teacher:
            slugs.add(self.teacher)
        return slugs

    def get_summary(self, artists_by_slug: dict[str, Artist]) -> str:
        if self.kind == PerformanceKind.SOLO:
            artist_obj = artists_by_slug.get(self.artist or "")
            return artist_obj.name if artist_obj else (self.artist or "")

        if self.kind == PerformanceKind.LINEUP:
            host_obj = artists_by_slug.get(self.host or "")
            host_name = host_obj.name if host_obj else (self.host or "")
            act_names = [
                artists_by_slug[a].name if a in artists_by_slug else a for a in self.acts
            ]
            return f"hosted by {host_name}, with {', '.join(act_names)}"

        if self.kind == PerformanceKind.WORKSHOP:
            teacher_obj = artists_by_slug.get(self.teacher or "")
            teacher_name = teacher_obj.name if teacher_obj else (self.teacher or "")
            registered = len(self.participants)
            return f"with {teacher_name}, {registered}/{self.max_participants} places taken"

        return ""

    def to_view(
        self,
        venues_by_slug: dict[str, Venue],
        artists_by_slug: dict[str, Artist],
    ) -> dict:
        venue_obj = venues_by_slug.get(self.venue)
        venue_name = venue_obj.name if venue_obj else self.venue
        capacity = venue_obj.capacity if venue_obj else 0

        involved_artists = []
        if self.kind == PerformanceKind.SOLO and self.artist:
            artist_obj = artists_by_slug.get(self.artist)
            if artist_obj:
                involved_artists.append({"slug": artist_obj.slug, "name": artist_obj.name})
        elif self.kind == PerformanceKind.LINEUP:
            if self.host and self.host in artists_by_slug:
                involved_artists.append(
                    {"slug": self.host, "name": artists_by_slug[self.host].name}
                )
            for act_slug in self.acts:
                if act_slug in artists_by_slug:
                    involved_artists.append(
                        {"slug": act_slug, "name": artists_by_slug[act_slug].name}
                    )
        elif self.kind == PerformanceKind.WORKSHOP and self.teacher:
            teacher_obj = artists_by_slug.get(self.teacher)
            if teacher_obj:
                involved_artists.append({"slug": teacher_obj.slug, "name": teacher_obj.name})

        view: dict = {
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
            "artists": involved_artists,
        }

        if self.kind == PerformanceKind.SOLO:
            view["artist"] = self.artist
            view["min_age"] = self.min_age
        elif self.kind == PerformanceKind.LINEUP:
            view["host"] = self.host
            view["acts"] = self.acts
        elif self.kind == PerformanceKind.WORKSHOP:
            max_p = self.max_participants or 0
            places_left = max(0, min(max_p, capacity) - len(self.participants))
            view["teacher"] = self.teacher
            view["max_participants"] = self.max_participants
            view["participants"] = self.participants
            view["places_left"] = places_left

        return view