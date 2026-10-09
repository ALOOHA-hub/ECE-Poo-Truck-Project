from datetime import date, datetime, timedelta

from config import FESTIVAL_DAY_OFFSET


def parse_datetime(iso_str: str) -> datetime:
    try:
        return datetime.fromisoformat(iso_str)
    except ValueError:
        raise ValueError(
            f"'{iso_str}' is not a valid timestamp, use YYYY-MM-DDTHH:MM."
        ) from None


def parse_date(iso_str: str) -> date:
    try:
        return date.fromisoformat(iso_str)
    except ValueError:
        raise ValueError(f"'{iso_str}' is not a day, use YYYY-MM-DD.") from None


def performance_start(perf: dict) -> datetime:
    return parse_datetime(perf["start"])


def performance_end(perf: dict) -> datetime:
    return performance_start(perf) + timedelta(minutes=perf["duration_minutes"])


def performance_festival_day(perf: dict) -> date:
    return (performance_start(perf) - FESTIVAL_DAY_OFFSET).date()