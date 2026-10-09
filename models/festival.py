from datetime import date, datetime, timedelta

from config import (
    BUFFER_GAP,
    DATE_FORMAT,
    MAX_DURATION_MINUTES,
    MAX_UPCOMING_PREVIEWS,
    MIN_DURATION_MINUTES,
    ArtistRole,
)
from models.artist import Artist
from models.performances import Performance, Workshop
from models.venue import Venue


class Festival:
    def __init__(
        self,
        name: str,
        first_day: date,
        last_day: date,
        venues: list[Venue] | None = None,
        artists: list[Artist] | None = None,
        performances: list[Performance] | None = None,
    ) -> None:
        self.name = name
        self.first_day = first_day
        self.last_day = last_day
        self._venues: dict[str, Venue] = {v.slug: v for v in (venues or [])}
        self._artists: dict[str, Artist] = {a.slug: a for a in (artists or [])}
        self._performances: list[Performance] = []

        for p in performances or []:
            self.add_performance(p, enforce_rules=False)

    @property
    def venues_by_slug(self) -> dict[str, Venue]:
        return dict(self._venues)

    @property
    def artists_by_slug(self) -> dict[str, Artist]:
        return dict(self._artists)

    @property
    def performances(self) -> list[Performance]:
        return list(self._performances)

    @property
    def performances_by_id(self) -> dict[str, Performance]:
        return {p.id: p for p in self._performances}

    @property
    def days(self) -> list[date]:
        day_list = []
        current = self.first_day
        while current <= self.last_day:
            day_list.append(current)
            current += timedelta(days=1)
        return day_list

    def validate_new_performance(self, performance: Performance) -> None:
        if performance.venue not in self._venues:
            raise ValueError(f"Unknown venue '{performance.venue}'.")

        venue_obj = self._venues[performance.venue]

        for artist_slug in performance.artists_involved():
            if artist_slug not in self._artists:
                raise ValueError(f"Unknown artist '{artist_slug}'.")

        if not (MIN_DURATION_MINUTES <= performance.duration_minutes <= MAX_DURATION_MINUTES):
            raise ValueError(
                f"Duration must be between {MIN_DURATION_MINUTES} and {MAX_DURATION_MINUTES} minutes, got {performance.duration_minutes}."
            )

        if not (self.first_day <= performance.festival_day <= self.last_day):
            raise ValueError(f"{performance.festival_day} is not a day of the festival.")

        # Polymorphic check on specific rules
        performance.validate_specific_rules(venue_obj)

        new_start = performance.start
        new_end = performance.end
        new_artists = performance.artists_involved()

        for other in self._performances:
            conflict = (new_start < other.end + BUFFER_GAP) and (
                other.start < new_end + BUFFER_GAP
            )
            if not conflict:
                continue

            if other.venue == performance.venue:
                venue_name = venue_obj.name
                raise ValueError(
                    f"{venue_name} is busy with {other.title} "
                    f"({other.start:%Y-%m-%d %H:%M}-{other.end:%H:%M})."
                )

            shared_artists = new_artists.intersection(other.artists_involved())
            if shared_artists:
                artist_slug = next(iter(shared_artists))
                artist_name = self._artists[artist_slug].name
                raise ValueError(f"{artist_name} is on stage in {other.title}.")

    def add_performance(self, performance: Performance, enforce_rules: bool = True) -> None:
        if enforce_rules:
            self.validate_new_performance(performance)
        self._performances.append(performance)

    def cancel_performance(self, performance_id: str) -> Performance:
        for idx, perf in enumerate(self._performances):
            if perf.id == performance_id:
                return self._performances.pop(idx)
        raise ValueError(f"No performance with id '{performance_id}'.")

    def register_workshop(self, performance_id: str, participant_name: str) -> Workshop:
        perf = self.performances_by_id.get(performance_id)
        if not perf:
            raise KeyError(f"No performance '{performance_id}'.")
        if not isinstance(perf, Workshop):
            raise TypeError(f"Performance '{performance_id}' is not a workshop.")

        venue = self._venues.get(perf.venue)
        if not venue:
            raise ValueError(f"Unknown venue '{perf.venue}'.")

        perf.register(participant_name, venue)
        return perf

    def programme(
        self,
        day: date | None = None,
        venue_slug: str | None = None,
    ) -> list[Performance]:
        if venue_slug and venue_slug not in self._venues:
            raise ValueError(f"No venue '{venue_slug}'.")

        matching = self._performances
        if day:
            matching = [p for p in matching if p.festival_day == day]
        if venue_slug:
            matching = [p for p in matching if p.venue == venue_slug]

        return sorted(matching)

    def artist_schedule(self, artist_slug: str) -> tuple[Artist, list[tuple[Performance, ArtistRole]]]:
        if artist_slug not in self._artists:
            raise ValueError(f"No artist '{artist_slug}'.")

        artist = self._artists[artist_slug]
        schedule = []
        for p in self._performances:
            role = p.role_of(artist_slug)
            if role:
                schedule.append((p, role))

        schedule.sort(key=lambda item: item[0].start)
        return artist, schedule

    def now(self, moment: datetime) -> tuple[list[Performance], list[Performance]]:
        currently_playing = []
        upcoming = []

        for p in self._performances:
            if p.start <= moment < p.end:
                currently_playing.append(p)
            elif moment <= p.start:
                upcoming.append(p)

        upcoming.sort()
        return currently_playing, upcoming[:MAX_UPCOMING_PREVIEWS]

    def to_dict(self) -> dict:
        """Serialize complete festival state into JSON schema format."""
        return {
            "name": self.name,
            "first_day": self.first_day.strftime(DATE_FORMAT),
            "last_day": self.last_day.strftime(DATE_FORMAT),
            "venues": [v.to_dict() for v in self._venues.values()],
            "artists": [a.to_dict() for a in self._artists.values()],
            "performances": [p.to_dict() for p in self._performances],
        }