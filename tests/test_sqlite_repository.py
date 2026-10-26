"""Tests for SqliteFestivalRepository persistence."""

from pathlib import Path

import pytest

from deauville.config import DEFAULT_DATA_PATH
from deauville.repositories import FestivalRepository, SqliteFestivalRepository


@pytest.fixture
def json_festival():
    """Load the reference festival from the JSON data file."""
    return FestivalRepository(DEFAULT_DATA_PATH).get_festival()


@pytest.fixture
def sqlite_repo(tmp_path: Path):
    """Create an ephemeral SQLite repository."""
    return SqliteFestivalRepository(tmp_path / "test.db")


def test_sqlite_save_and_reload(json_festival, sqlite_repo):
    """Round-trip: save a festival to SQLite, reload, verify entities."""
    sqlite_repo.save_festival(json_festival)
    reloaded = sqlite_repo.get_festival()

    assert reloaded.name == json_festival.name
    assert len(reloaded.venues_by_slug) == len(json_festival.venues_by_slug)
    assert len(reloaded.artists_by_slug) == len(json_festival.artists_by_slug)
    assert len(reloaded.performances) == len(json_festival.performances)


def test_sqlite_preserves_performance_kinds(json_festival, sqlite_repo):
    """Check that solo, lineup, and workshop kinds survive the round-trip."""
    sqlite_repo.save_festival(json_festival)
    reloaded = sqlite_repo.get_festival()

    original_kinds = {p.kind for p in json_festival.performances}
    reloaded_kinds = {p.kind for p in reloaded.performances}
    assert reloaded_kinds == original_kinds


def test_sqlite_cancel_and_persist(json_festival, sqlite_repo):
    """Cancel a performance, persist via SQLite, and verify on reload."""
    first_id = json_festival.performances[0].id
    json_festival.cancel_performance(first_id)
    sqlite_repo.save_festival(json_festival)

    reloaded = sqlite_repo.get_festival()
    assert first_id not in reloaded.performances_by_id
    assert len(reloaded.performances) == len(json_festival.performances)


def test_sqlite_missing_db_raises(tmp_path: Path):
    """Loading from a non-existent .db file raises NotFoundError/ValueError."""
    repo = SqliteFestivalRepository(tmp_path / "missing.db")
    with pytest.raises((ValueError, KeyError), match="not found"):
        repo.get_festival()
