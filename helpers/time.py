from datetime import date, datetime, timedelta

FESTIVAL_DAY_OFFSET = timedelta(hours=6)


def parse_datetime(iso_str: str) -> datetime:
    """Parse ISO datetime string (e.g., '2027-06-11T20:30')."""
    return datetime.fromisoformat(iso_str)


def parse_date(iso_str: str) -> date:
    """Parse ISO date string (e.g., '2027-06-11')."""
    return date.fromisoformat(iso_str)


def performance_start(perf: dict) -> datetime:
    return parse_datetime(perf["start"])


def performance_end(perf: dict) -> datetime:
    return performance_start(perf) + timedelta(minutes=perf["duration_minutes"])


def performance_festival_day(perf: dict) -> date:
    """Festival day is the date of start minus 6 hours."""
    return (performance_start(perf) - FESTIVAL_DAY_OFFSET).date()