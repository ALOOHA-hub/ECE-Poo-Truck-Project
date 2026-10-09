"""HTTP API contract verification suite (E12)."""

from datetime import date, datetime
import pytest
from fastapi.testclient import TestClient

from api import create_app
from models import Artist, Festival, SoloShow, Venue, Workshop
from repositories import MemoryFestivalRepository


@pytest.fixture
def client() -> TestClient:
    venue1 = Venue(name="Grand Casino", capacity=650, address="Seafront")
    venue2 = Venue(name="Le Kiosque", capacity=120, address="Promenade")

    artist1 = Artist(name="Nora Lebrun")
    artist2 = Artist(name="Max Pellerin")

    solo = SoloShow(
        title="Opening Solo",
        venue="grand-casino",
        start=datetime(2027, 6, 11, 20, 0),
        duration_minutes=60,
        artist="nora-lebrun",
    )
    workshop = Workshop(
        title="Improv 101",
        venue="le-kiosque",
        start=datetime(2027, 6, 12, 10, 0),
        duration_minutes=90,
        teacher="nora-lebrun",
        max_participants=2,
        participants=["Alice"],
    )

    fest = Festival(
        name="Contract Fest",
        first_day=date(2027, 6, 10),
        last_day=date(2027, 6, 13),
        venues=[venue1, venue2],
        artists=[artist1, artist2],
        performances=[solo, workshop],
    )

    memory_repo = MemoryFestivalRepository(fest.to_dict())
    return TestClient(create_app(memory_repo))


def test_festival_endpoint(client: TestClient):
    res = client.get("/api/festival")
    assert res.status_code == 200
    assert res.json()["name"] == "Contract Fest"


def test_programme_venue_filtering(client: TestClient):
    res = client.get("/api/programme?venue=grand-casino")
    assert res.status_code == 200
    assert len(res.json()) == 1

    res_unknown = client.get("/api/programme?venue=unknown-hall")
    assert res_unknown.status_code == 404


def test_add_artist_duplicate_conflict_409(client: TestClient):
    res1 = client.post("/api/artists", json={"name": "Zoé Tanguy"})
    assert res1.status_code == 201

    res2 = client.post("/api/artists", json={"name": "zoe tanguy"})
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_schedule_performance_conflict_409(client: TestClient):
    res = client.post(
        "/api/performances",
        json={
            "kind": "solo",
            "title": "Conflicting Show",
            "venue": "grand-casino",
            "start": "2027-06-11T20:30",
            "duration_minutes": 45,
            "artist": "max-pellerin",
        },
    )
    assert res.status_code == 409
    assert "Grand Casino is busy" in res.json()["detail"]


def test_put_shifts_id_and_atomic_failure(client: TestClient):
    orig_id = "grand-casino-2027-06-11-2000"

    # Successful move
    res = client.put(
        f"/api/performances/{orig_id}",
        json={
            "kind": "solo",
            "title": "Opening Solo",
            "venue": "grand-casino",
            "start": "2027-06-11T18:00",
            "duration_minutes": 60,
            "artist": "nora-lebrun",
        },
    )
    assert res.status_code == 200
    new_id = res.json()["id"]
    assert new_id == "grand-casino-2027-06-11-1800"

    # Conflicting move -> 409, original show untouched
    conflict_res = client.put(
        f"/api/performances/{new_id}",
        json={
            "kind": "solo",
            "title": "Opening Solo",
            "venue": "grand-casino",
            "start": "2027-06-12T10:15",
            "duration_minutes": 60,
            "artist": "nora-lebrun",
        },
    )
    assert conflict_res.status_code == 409

    # Check persistence of previous valid state
    fetch = client.get(f"/api/performances/{new_id}")
    assert fetch.status_code == 200
    assert fetch.json()["start"] == "2027-06-11T18:00"


def test_delete_contract(client: TestClient):
    perf_id = "grand-casino-2027-06-11-2000"
    assert client.delete(f"/api/performances/{perf_id}").status_code == 204
    assert client.delete(f"/api/performances/{perf_id}").status_code == 404


def test_workshop_registration_contract(client: TestClient):
    ws_id = "le-kiosque-2027-06-12-1000"

    # 1. Successful registration
    assert client.post(f"/api/performances/{ws_id}/register", json={"name": "Bob"}).status_code == 201

    # 2. Duplicate registration -> 409
    res_dup = client.post(f"/api/performances/{ws_id}/register", json={"name": "Bob"})
    assert res_dup.status_code == 409
    assert "already registered" in res_dup.json()["detail"]

    # 3. Full workshop -> 409
    res_full = client.post(f"/api/performances/{ws_id}/register", json={"name": "Charlie"})
    assert res_full.status_code == 409
    assert "Workshop is full" in res_full.json()["detail"]

    # 4. Wrong kind -> 400
    res_bad = client.post("/api/performances/grand-casino-2027-06-11-2000/register", json={"name": "Bob"})
    assert res_bad.status_code == 400
    assert "is not a workshop" in res_bad.json()["detail"]