from datetime import timedelta
from pathlib import Path

# Paths
DEFAULT_DATA_PATH = Path("data/festival.json")

# Business Rules & Buffer Offsets
FESTIVAL_DAY_CUTOFF_HOURS = 6
FESTIVAL_DAY_OFFSET = timedelta(hours=FESTIVAL_DAY_CUTOFF_HOURS)

BUFFER_MINUTES = 30
BUFFER_GAP = timedelta(minutes=BUFFER_MINUTES)

MIN_DURATION_MINUTES = 1
MAX_DURATION_MINUTES = 360

MAX_UPCOMING_PREVIEWS = 3

# String & Date Formats
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"
PERFORMANCE_ID_FORMAT = "%Y-%m-%d-%H%M"