from datetime import datetime
from pydantic import BaseModel, Field

from config import PerformanceKind


class PerformancePayload(BaseModel):
    kind: PerformanceKind
    title: str = Field(..., min_length=1)
    venue: str = Field(..., min_length=1)
    start: datetime
    duration_minutes: int
    description: str = Field(default="")
    # Solo
    artist: str = Field(default="")
    min_age: int = Field(default=0)
    # Lineup
    host: str = Field(default="")
    acts: list[str] = Field(default_factory=list)
    # Workshop
    teacher: str = Field(default="")
    max_participants: int = Field(default=1)