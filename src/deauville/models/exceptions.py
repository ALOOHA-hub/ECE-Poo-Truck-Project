"""Domain exception hierarchy for the festival management platform."""


class FestivalError(Exception):
    """Base domain exception for all festival business errors."""


class NotFoundError(FestivalError, KeyError, ValueError):
    """Raised when an entity or resource is not found (maps to HTTP 404)."""


class ConflictError(FestivalError, ValueError):
    """Raised when an operation violates schedule or artist availability (409)."""


class ValidationError(FestivalError, ValueError):
    """Raised when entity parameters violate business bounds (maps to HTTP 422)."""


class InvalidPerformanceTypeError(ValidationError, TypeError):
    """Raised when an operation targets an incompatible performance kind (400)."""
