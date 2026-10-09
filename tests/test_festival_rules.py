from datetime import date, datetime

import pytest

from models import Artist, Festival, Lineup, Performance, SoloShow, Venue, Workshop


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
    existing_performance = SoloShow(
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


def test_cannot_instantiate_abstract_performance():
    """Verify that Performance is abstract and cannot be instantiated directly."""
    with pytest.raises(TypeError):
        Performance(  # type: ignore[abstract]
            title="Abstract Performance",
            venue="le-kiosque",
            start=datetime(2027, 6, 11, 10, 0),
            duration_minutes=60,
        )


def test_venue_busy_conflict(festival: Festival):
    """Refuse scheduling in the same venue within the 30-minute buffer."""
    overlapping = SoloShow(
        title="Conflict Show",
        venue="grand-casino",
        start=datetime(2027, 6, 11, 21, 15),  # 21:15 is inside the 30m buffer after 21:00
        duration_minutes=45,
        artist="max-pellerin",
    )
    with pytest.raises(ValueError, match="Grand Casino is busy"):
        festival.add_performance(overlapping)


def test_artist_busy_in_another_venue(festival: Festival):
    """Refuse scheduling an artist if they are already on another stage within buffer."""
    artist_conflict = SoloShow(
        title="Different Venue Same Artist",
        venue="le-kiosque",
        start=datetime(2027, 6, 11, 20, 30),
        duration_minutes=30,
        artist="nora-lebrun",
    )
    with pytest.raises(ValueError, match="Nora Lebrun is on stage"):
        festival.add_performance(artist_conflict)


def test_artist_busy_as_act_in_lineup(festival: Festival):
    """Refuse if artist is involved as an act in a lineup."""
    lineup = Lineup(
        title="Lineup Night",
        venue="le-kiosque",
        start=datetime(2027, 6, 11, 20, 0),
        duration_minutes=60,
        host="tom-vasseur",
        acts=["nora-lebrun", "max-pellerin"],
    )
    with pytest.raises(ValueError, match="Nora Lebrun is on stage"):
        festival.add_performance(lineup)


def test_show_at_one_am_belongs_to_previous_day():
    """A show starting at 01:00 on June 12 belongs to June 11's festival day."""
    perf = SoloShow(
        title="Late Show",
        venue="le-kiosque",
        start=datetime(2027, 6, 12, 1, 0),
        duration_minutes=60,
        artist="max-pellerin",
    )
    assert perf.festival_day == date(2027, 6, 11)


def test_day_outside_the_festival(festival: Festival):
    """Refuse scheduling a performance outside the festival dates."""
    outside_show = SoloShow(
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
    invalid_perf = SoloShow(
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
    unknown_venue = SoloShow(
        title="Bad Venue",
        venue="non-existent-hall",
        start=datetime(2027, 6, 11, 10, 0),
        duration_minutes=60,
        artist="max-pellerin",
    )
    with pytest.raises(ValueError, match="Unknown venue"):
        festival.add_performance(unknown_venue)

    unknown_artist = SoloShow(
        title="Bad Artist",
        venue="le-kiosque",
        start=datetime(2027, 6, 11, 10, 0),
        duration_minutes=60,
        artist="unknown-ghost",
    )
    with pytest.raises(ValueError, match="Unknown artist"):
        festival.add_performance(unknown_artist)


def test_solo_min_age_validation(festival: Festival):
    """Refuse solo shows with min_age outside 0-18."""
    with pytest.raises(ValueError, match="Minimum age must be between 0 and 18"):
        festival.add_performance(
            SoloShow(
                title="Bad Age Solo",
                venue="le-kiosque",
                start=datetime(2027, 6, 11, 10, 0),
                duration_minutes=60,
                artist="max-pellerin",
                min_age=25,
            )
        )


def test_lineup_minimum_acts(festival: Festival):
    """Refuse lineups with fewer than 2 acts."""
    with pytest.raises(ValueError, match="needs at least 2 acts"):
        festival.add_performance(
            Lineup(
                title="Too Few Acts",
                venue="le-kiosque",
                start=datetime(2027, 6, 11, 10, 0),
                duration_minutes=60,
                host="tom-vasseur",
                acts=["nora-lebrun"],
            )
        )


def test_lineup_timing_formula(festival: Festival):
    """A lineup with 3 acts requires: 3 * 10 + 2 * 3 = 36 minutes."""
    festival._artists["artist-3"] = Artist(name="Artist Three")

    lineup_35m = Lineup(
        title="3 Acts in 35m",
        venue="le-kiosque",
        start=datetime(2027, 6, 11, 10, 0),
        duration_minutes=35,
        host="tom-vasseur",
        acts=["nora-lebrun", "max-pellerin", "artist-3"],
    )
    with pytest.raises(ValueError, match="requires at least 36 minutes"):
        festival.add_performance(lineup_35m)

    lineup_36m = Lineup(
        title="3 Acts in 36m",
        venue="le-kiosque",
        start=datetime(2027, 6, 11, 10, 0),
        duration_minutes=36,
        host="tom-vasseur",
        acts=["nora-lebrun", "max-pellerin", "artist-3"],
    )
    festival.add_performance(lineup_36m)
    assert lineup_36m in festival.performances


def test_workshop_bounded_by_venue_capacity(festival: Festival):
    """Workshop available places are bounded by venue capacity."""
    grand_casino = festival.venues_by_slug["grand-casino"]  # capacity 650
    huge_workshop = Workshop(
        title="Huge Improv",
        venue="grand-casino",
        start=datetime(2027, 6, 12, 10, 0),
        duration_minutes=60,
        teacher="nora-lebrun",
        max_participants=999,
    )
    assert huge_workshop.effective_capacity(grand_casino) == 650


def test_workshop_at_least_one_place(festival: Festival):
    """A workshop must specify at least 1 participant place."""
    with pytest.raises(ValueError, match="at least 1 place"):
        festival.add_performance(
            Workshop(
                title="Zero Places",
                venue="le-kiosque",
                start=datetime(2027, 6, 11, 10, 0),
                duration_minutes=60,
                teacher="nora-lebrun",
                max_participants=0,
            )
        )