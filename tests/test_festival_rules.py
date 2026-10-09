from datetime import date, datetime

import pytest

from config import PerformanceKind
from models import Artist, Festival, Performance, Venue


@pytest.fixture
def festival() -> Festival:
    venues = [
        Venue(name="Grand Casino", capacity=650, address="Seafront"),
        Venue(name="Le Kiosque", capacity=120, address="Promenade"),
    ]
    artists = [
        Artist(name="Nora Lebrun"),
        Artist(name="Max Pellerin"),
        Artist(name="Tom Vasseur"),
    ]
    existing_performance = Performance(
        kind=PerformanceKind.SOLO,
        title="Opening Solo",
        venue="grand-casino",
        start=datetime(2027, 6, 11, 20, 0),
        duration_minutes=60,
        artist="nora-lebrun",
    )
    return Festival(
        name="Test Festival",
        first_day=date(2027, 6, 10),
        last_day=date(2027, 6, 13),
        venues=venues,
        artists=artists,
        performances=[existing_performance],
    )


def test_venue_busy_conflict(festival: Festival):
    """Refuse scheduling in the same venue within the 30-minute buffer."""
    overlapping = Performance(
        kind=PerformanceKind.SOLO,
        title="Conflict Show",
        venue="grand-casino",
        start=datetime(2027, 6, 11, 21, 15),  # Existing ends at 21:00; 21:15 is inside 30m buffer
        duration_minutes=45,
        artist="max-pellerin",
    )
    with pytest.raises(ValueError, match="Grand Casino is busy"):
        festival.add_performance(overlapping)


def test_artist_busy_in_another_venue(festival: Festival):
    """Refuse scheduling an artist if they are already on another stage within buffer."""
    artist_conflict = Performance(
        kind=PerformanceKind.SOLO,
        title="Different Venue Same Artist",
        venue="le-kiosque",
        start=datetime(2027, 6, 11, 20, 30),
        duration_minutes=30,
        artist="nora-lebrun",
    )
    with pytest.raises(ValueError, match="Nora Lebrun is on stage"):
        festival.add_performance(artist_conflict)


def test_artist_busy_as_act_in_lineup(festival: Festival):
    """Refuse if artist is involved as an act in another performance."""
    lineup = Performance(
        kind=PerformanceKind.LINEUP,
        title="Lineup Night",
        venue="le-kiosque",
        start=datetime(2027, 6, 11, 20, 0),
        duration_minutes=60,
        host="tom-vasseur",
        acts=["nora-lebrun"],
    )
    with pytest.raises(ValueError, match="Nora Lebrun is on stage"):
        festival.add_performance(lineup)


def test_show_at_one_am_belongs_to_previous_day():
    """A show starting at 01:00 on June 12 belongs to June 11's festival day."""
    perf = Performance(
        kind=PerformanceKind.SOLO,
        title="Late Show",
        venue="le-kiosque",
        start=datetime(2027, 6, 12, 1, 0),
        duration_minutes=60,
        artist="max-pellerin",
    )
    assert perf.festival_day == date(2027, 6, 11)


def test_day_outside_the_festival(festival: Festival):
    """Refuse scheduling a performance outside the festival dates."""
    outside_show = Performance(
        kind=PerformanceKind.SOLO,
        title="Too Late",
        venue="le-kiosque",
        start=datetime(2027, 6, 14, 10, 0),
        duration_minutes=60,
        artist="max-pellerin",
    )
    with pytest.raises(ValueError, match="not a day of the festival"):
        festival.add_performance(outside_show)


@pytest.mark.parametrize("duration", [0, 361])
def test_invalid_duration_limits(festival: Festival, duration: int):
    """Refuse duration < 1 or > 360."""
    invalid_perf = Performance(
        kind=PerformanceKind.SOLO,
        title="Bad Duration",
        venue="le-kiosque",
        start=datetime(2027, 6, 11, 10, 0),
        duration_minutes=duration,
        artist="max-pellerin",
    )
    with pytest.raises(ValueError, match="Duration must be between 1 and 360"):
        festival.add_performance(invalid_perf)


def test_unknown_venue_or_artist(festival: Festival):
    """Refuse unknown venue or artist slugs."""
    unknown_venue = Performance(
        kind=PerformanceKind.SOLO,
        title="Bad Venue",
        venue="non-existent-hall",
        start=datetime(2027, 6, 11, 10, 0),
        duration_minutes=60,
        artist="max-pellerin",
    )
    with pytest.raises(ValueError, match="Unknown venue"):
        festival.add_performance(unknown_venue)

    unknown_artist = Performance(
        kind=PerformanceKind.SOLO,
        title="Bad Artist",
        venue="le-kiosque",
        start=datetime(2027, 6, 11, 10, 0),
        duration_minutes=60,
        artist="unknown-ghost",
    )
    with pytest.raises(ValueError, match="Unknown artist"):
        festival.add_performance(unknown_artist)