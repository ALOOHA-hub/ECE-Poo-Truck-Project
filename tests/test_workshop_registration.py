from datetime import date, datetime

from fastapi.testclient import TestClient
import pytest

from api import app
from models import Artist, Festival, SoloShow, Venue, Workshop


@pytest.fixture
def workshop_festival() -> Festival:
    venue = Venue(name="La Cabane", capacity=15, address="Promenade")
    teacher = Artist(name="Nora Lebrun")
    workshop = Workshop(
        title="Improv 101",
        venue="la-cabane",
        start=datetime(2027, 6, 11, 10, 0),
        duration_minutes=90,
        teacher="nora-lebrun",
        max_participants=3,
        participants=["Alice"],
    )
    solo = SoloShow(
        title="Solo Night",
        venue="la-cabane",
        start=datetime(2027, 6, 11, 20, 0),
        duration_minutes=60,
        artist="nora-lebrun",
    )
    return Festival(
        name="Comedy Fest",
        first_day=date(2027, 6, 10),
        last_day=date(2027, 6, 13),
        venues=[venue],
        artists=[teacher],
        performances=[workshop, solo],
    )


def test_workshop_successful_registration(workshop_festival: Festival):
    workshop_id = "la-cabane-2027-06-11-1000"
    workshop = workshop_festival.register_workshop(workshop_id, "Bob")
    assert "Bob" in workshop.participants
    venue = workshop_festival.venues_by_slug["la-cabane"]
    assert workshop.places_left(venue) == 1


def test_workshop_rejects_empty_or_whitespace_name(workshop_festival: Festival):
    workshop_id = "la-cabane-2027-06-11-1000"
    with pytest.raises(ValueError, match="cannot be empty"):
        workshop_festival.register_workshop(workshop_id, "   ")


def test_workshop_rejects_duplicate_registration(workshop_festival: Festival):
    workshop_id = "la-cabane-2027-06-11-1000"
    with pytest.raises(ValueError, match="already registered"):
        workshop_festival.register_workshop(workshop_id, "Alice")


def test_workshop_rejects_when_full(workshop_festival: Festival):
    workshop_id = "la-cabane-2027-06-11-1000"
    workshop_festival.register_workshop(workshop_id, "Bob")
    workshop_festival.register_workshop(workshop_id, "Charlie")

    with pytest.raises(ValueError, match="Workshop is full"):
        workshop_festival.register_workshop(workshop_id, "David")


def test_workshop_unregister_success(workshop_festival: Festival):
    workshop = workshop_festival.performances_by_id["la-cabane-2027-06-11-1000"]
    assert isinstance(workshop, Workshop)
    workshop.unregister("Alice")
    assert "Alice" not in workshop.participants


def test_workshop_unregister_non_participant_raises(workshop_festival: Festival):
    workshop = workshop_festival.performances_by_id["la-cabane-2027-06-11-1000"]
    assert isinstance(workshop, Workshop)
    with pytest.raises(ValueError, match="not registered"):
        workshop.unregister("Ghost")


def test_register_for_non_workshop_raises_type_error(workshop_festival: Festival):
    solo_id = "la-cabane-2027-06-11-2000"
    with pytest.raises(TypeError, match="is not a workshop"):
        workshop_festival.register_workshop(solo_id, "Bob")


def test_register_for_unknown_performance_raises_key_error(workshop_festival: Festival):
    with pytest.raises(KeyError, match="non-existent"):
        workshop_festival.register_workshop("non-existent", "Bob")


def test_workshop_serialization_round_trip(workshop_festival: Festival):
    raw_dict = workshop_festival.to_dict()
    assert "performances" in raw_dict
    ws_data = next(p for p in raw_dict["performances"] if p["kind"] == "workshop")
    assert ws_data["teacher"] == "nora-lebrun"
    assert ws_data["max_participants"] == 3
    assert ws_data["participants"] == ["Alice"]


def test_api_register_endpoint_404():
    client = TestClient(app)
    response = client.post(
        "/api/performances/does-not-exist/register",
        json={"name": "Alice"},
    )
    assert response.status_code == 404
    assert "No performance" in response.json()["detail"]


def test_api_register_endpoint_not_a_workshop():
    client = TestClient(app)
    # Using an existing solo show from festival.json
    response = client.post(
        "/api/performances/grand-casino-2027-06-11-2030/register",
        json={"name": "Alice"},
    )
    assert response.status_code == 400
    assert "is not a workshop" in response.json()["detail"]