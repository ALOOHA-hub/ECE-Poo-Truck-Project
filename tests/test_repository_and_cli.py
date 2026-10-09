import json
from pathlib import Path
import pytest

from cli.parser import build_parser, run_cli
from config import DEFAULT_DATA_PATH
from models import SoloShow
from repositories import FestivalRepository


@pytest.fixture
def temp_festival_file(tmp_path: Path) -> Path:
    """Create an isolated temporary copy of festival.json for test mutation."""
    dest = tmp_path / "test_fest.json"
    with open(DEFAULT_DATA_PATH, "r", encoding="utf-8") as src:
        content = src.read()
    dest.write_text(content, encoding="utf-8")
    return dest


def test_repository_loads_and_counts_entities():
    repo = FestivalRepository(DEFAULT_DATA_PATH)
    fest = repo.get_festival()
    assert len(fest.venues_by_slug) == 4
    assert len(fest.artists_by_slug) == 12
    assert len(fest.performances) > 0


def test_repository_missing_file_raises_value_error(tmp_path: Path):
    missing_path = tmp_path / "non_existent.json"
    repo = FestivalRepository(missing_path)
    with pytest.raises(ValueError, match="not found"):
        repo.get_festival()


def test_repository_corrupted_file_raises_value_error(tmp_path: Path):
    corrupted_path = tmp_path / "corrupted.json"
    corrupted_path.write_text("{ broken json content", encoding="utf-8")
    repo = FestivalRepository(corrupted_path)
    with pytest.raises(ValueError, match="is damaged"):
        repo.get_festival()


def test_repository_save_and_rehydrate(temp_festival_file: Path):
    repo = FestivalRepository(temp_festival_file)
    festival = repo.get_festival()

    initial_count = len(festival.performances)
    first_id = festival.performances[0].id

    # Cancel a performance and save to disk
    cancelled = festival.cancel_performance(first_id)
    assert cancelled.id == first_id
    repo.save_festival(festival)

    # Re-read from disk to ensure persistence
    reloaded_repo = FestivalRepository(temp_festival_file)
    reloaded_fest = reloaded_repo.get_festival()
    assert len(reloaded_fest.performances) == initial_count - 1
    assert first_id not in reloaded_fest.performances_by_id


def test_cli_parser_defaults():
    parser = build_parser()
    parsed = parser.parse_args([])
    assert parsed.data == DEFAULT_DATA_PATH
    assert parsed.subcommand is None


def test_cli_parser_custom_data_path(tmp_path: Path):
    custom_path = str(tmp_path / "custom.json")
    parser = build_parser()
    parsed = parser.parse_args(["--data", custom_path, "venues"])
    assert parsed.data == Path(custom_path)
    assert parsed.subcommand == "venues"


def test_cli_run_summary(capsys: pytest.CaptureFixture):
    run_cli([])
    captured = capsys.readouterr().out
    assert "Deauville Festival du Rire" in captured
    assert "venues" in captured


def test_cli_run_venues(capsys: pytest.CaptureFixture):
    run_cli(["venues"])
    captured = capsys.readouterr().out
    assert "grand-casino: Grand Casino, 650 seats" in captured
    assert "Total: 1130 seats" in captured

def test_cli_run_programme_with_time_cutoff(capsys: pytest.CaptureFixture):
    run_cli(["programme", "2027-06-11"])
    captured = capsys.readouterr().out
    assert "Programme for Friday 11 June:" in captured
    assert "After Hours" in captured


def test_cli_invalid_date_exits_with_error(capsys: pytest.CaptureFixture):
    with pytest.raises(SystemExit) as exc_info:
        run_cli(["programme", "Invalid-Date"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr().out
    assert "Error: 'Invalid-Date' is not a day, use YYYY-MM-DD." in captured