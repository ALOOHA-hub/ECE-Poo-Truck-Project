"""FastAPI application factory exposing the complete REST API according to API.md."""

from datetime import date, datetime
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import (
    API_TITLE,
    DATE_FORMAT,
    STATIC_ADMIN_DIR,
    STATIC_DIR,
    PerformanceKind,
)
from models import (
    Artist,
    ConflictError,
    FestivalError,
    InvalidPerformanceTypeError,
    Lineup,
    NotFoundError,
    Performance,
    SoloShow,
    ValidationError,
    Workshop,
)
from repositories import (
    BaseFestivalRepository,
    FestivalRepository,
)
from schemas import (
    ArtistCreateRequest,
    PerformancePayload,
    WorkshopRegistrationRequest,
)


def instantiate_performance(payload: PerformancePayload) -> Performance:
    """Polymorphic factory building a performance entity from an inbound payload."""
    if payload.kind == PerformanceKind.SOLO:
        return SoloShow(
            title=payload.title,
            venue=payload.venue,
            start=payload.start,
            duration_minutes=payload.duration_minutes,
            description=payload.description,
            artist=payload.artist,
            min_age=payload.min_age,
        )
    if payload.kind == PerformanceKind.LINEUP:
        return Lineup(
            title=payload.title,
            venue=payload.venue,
            start=payload.start,
            duration_minutes=payload.duration_minutes,
            description=payload.description,
            host=payload.host,
            acts=list(payload.acts),
        )
    if payload.kind == PerformanceKind.WORKSHOP:
        return Workshop(
            title=payload.title,
            venue=payload.venue,
            start=payload.start,
            duration_minutes=payload.duration_minutes,
            description=payload.description,
            teacher=payload.teacher,
            max_participants=payload.max_participants,
            participants=[],
        )
    raise ValidationError(f"Unknown kind '{payload.kind}'.")


def create_app(repo: BaseFestivalRepository | None = None) -> FastAPI:
    """Application factory binding routes to a festival repository."""
    repository = repo or FestivalRepository()
    app = FastAPI(title=API_TITLE)

    @app.exception_handler(FestivalError)
    def handle_festival_error(_request: Request, exc: FestivalError) -> JSONResponse:
        code = 400
        if isinstance(exc, NotFoundError):
            code = 404
        elif isinstance(exc, ConflictError):
            code = 409
        elif isinstance(exc, InvalidPerformanceTypeError):
            code = 400
        elif isinstance(exc, ValidationError):
            code = 422

        return JSONResponse(status_code=code, content={"detail": str(exc)})

    # ==========================
    # READ ROUTES
    # ==========================

    @app.get("/api/festival")
    def get_festival() -> dict[str, Any]:
        festival = repository.get_festival()
        return {
            "name": festival.name,
            "first_day": festival.first_day.strftime(DATE_FORMAT),
            "last_day": festival.last_day.strftime(DATE_FORMAT),
            "days": [d.strftime(DATE_FORMAT) for d in festival.days],
        }

    @app.get("/api/venues")
    def list_venues() -> list[dict[str, Any]]:
        festival = repository.get_festival()
        return [v.to_view() for v in festival.venues_by_slug.values()]

    @app.get("/api/artists")
    def list_artists() -> list[dict[str, Any]]:
        festival = repository.get_festival()
        sorted_artists = sorted(festival.artists_by_slug.values(), key=lambda a: a.slug)
        return [a.to_view() for a in sorted_artists]

    @app.get("/api/artists/{slug}")
    def get_artist(slug: str) -> dict[str, Any]:
        festival = repository.get_festival()
        artist, schedule = festival.artist_schedule(slug)
        result = artist.to_view()
        result["performances"] = [
            p.to_view(festival.venues_by_slug, festival.artists_by_slug)
            for p, _ in schedule
        ]
        return result

    @app.get("/api/programme")
    def get_programme(
        day: date | None = None,
        venue: str | None = None,
    ) -> list[dict[str, Any]]:
        festival = repository.get_festival()
        matching = festival.programme(day=day, venue_slug=venue)
        return [
            p.to_view(festival.venues_by_slug, festival.artists_by_slug)
            for p in matching
        ]

    @app.get("/api/performances/{perf_id}")
    def get_performance(perf_id: str) -> dict[str, Any]:
        festival = repository.get_festival()
        perf = festival.performances_by_id.get(perf_id)
        if not perf:
            raise NotFoundError(f"No performance '{perf_id}'.")
        return perf.to_view(festival.venues_by_slug, festival.artists_by_slug)

    @app.get("/api/now")
    def get_now(at: datetime | None = None) -> dict[str, Any]:
        festival = repository.get_festival()
        query_time = at or datetime.now()
        now_playing, up_next = festival.now(query_time)
        return {
            "now_playing": [
                p.to_view(festival.venues_by_slug, festival.artists_by_slug)
                for p in now_playing
            ],
            "up_next": [
                p.to_view(festival.venues_by_slug, festival.artists_by_slug)
                for p in up_next
            ],
        }

    # ==========================
    # WRITE (ADMIN) ROUTES
    # ==========================

    @app.post("/api/artists", status_code=201)
    def create_artist(payload: ArtistCreateRequest) -> dict[str, Any]:
        festival = repository.get_festival()
        new_artist = Artist(name=payload.name, bio=payload.bio, photo_url=payload.photo_url)
        festival.add_artist(new_artist)
        repository.save_festival(festival)
        return new_artist.to_view()

    @app.post("/api/performances", status_code=201)
    def create_performance(payload: PerformancePayload) -> dict[str, Any]:
        festival = repository.get_festival()
        perf = instantiate_performance(payload)
        festival.add_performance(perf)
        repository.save_festival(festival)
        return perf.to_view(festival.venues_by_slug, festival.artists_by_slug)

    @app.put("/api/performances/{perf_id}", status_code=200)
    def edit_performance(perf_id: str, payload: PerformancePayload) -> dict[str, Any]:
        festival = repository.get_festival()
        updated_perf = instantiate_performance(payload)
        saved_perf = festival.update_performance(perf_id, updated_perf)
        repository.save_festival(festival)
        return saved_perf.to_view(festival.venues_by_slug, festival.artists_by_slug)

    @app.delete("/api/performances/{perf_id}", status_code=204)
    def delete_performance(perf_id: str) -> Response:
        festival = repository.get_festival()
        festival.cancel_performance(perf_id)
        repository.save_festival(festival)
        return Response(status_code=204)

    @app.post("/api/performances/{perf_id}/register", status_code=201)
    def register_workshop(
        perf_id: str,
        payload: WorkshopRegistrationRequest,
    ) -> dict[str, Any]:
        festival = repository.get_festival()
        workshop = festival.register_workshop(perf_id, payload.name)
        repository.save_festival(festival)
        return workshop.to_view(festival.venues_by_slug, festival.artists_by_slug)

    # Static mounts: admin must mount before public "/"
    if STATIC_ADMIN_DIR.is_dir():
        app.mount("/admin", StaticFiles(directory=STATIC_ADMIN_DIR, html=True))

    if STATIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=STATIC_DIR, html=True))

    return app


# Default app instance for ASGI servers
app = create_app()