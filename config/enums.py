from enum import StrEnum


class PerformanceKind(StrEnum):
    SOLO = "solo"
    LINEUP = "lineup"
    WORKSHOP = "workshop"


class ArtistRole(StrEnum):
    SOLO = "solo"
    HOST = "host"
    ACT = "act"
    TEACHER = "teacher"