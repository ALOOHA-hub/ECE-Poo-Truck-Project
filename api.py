from datetime import date, datetime

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from config import API_TITLE, DATE_FORMAT, STATIC_DIR
from helpers import load_festival_aggregate

app = FastAPI(title=API_TITLE)


@app.get("/api/festival")
def read_festival() -> dict:
    festival = load_festival_aggregate()
    return {
        "name": festival.name,
        "first_day": festival.first_day.strftime(DATE_FORMAT),
        "last_day": festival.last_day.strftime(DATE_FORMAT),
        "days": [d.strftime(DATE_FORMAT) for d in festival.days],
    }


@app.get("/api/venues")
def list_venues() -> list[dict]:
    festival = load_festival_aggregate()
    return [v.to_dict() for v in festival.venues_by_slug.values()]


@app.get("/api/artists")
def list_artists() -> list[dict]:
    festival = load_festival_aggregate()
    sorted_artists = sorted(festival.artists_by_slug.values(), key=lambda a: a.slug)
    return [a.to_dict() for a in sorted_artists]


@app.get("/api/programme")
def read_programme(day: date | None = None, venue: str | None = None) -> list[dict]:
    festival = load_festival_aggregate()
    try:
        matching = festival.programme(day=day, venue_slug=venue)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err)) from None

    return [p.to_view(festival.venues_by_slug, festival.artists_by_slug) for p in matching]


@app.get("/api/now")
def read_now(at: datetime | None = None) -> dict:
    festival = load_festival_aggregate()
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


@app.get("/api/performances/{perf_id}")
def read_performance(perf_id: str) -> dict:
    festival = load_festival_aggregate()
    perf = festival.performances_by_id.get(perf_id)
    if not perf:
        raise HTTPException(status_code=404, detail=f"No performance '{perf_id}'.")
    return perf.to_view(festival.venues_by_slug, festival.artists_by_slug)


@app.get("/api/artists/{slug}")
def read_artist(slug: str) -> dict:
    festival = load_festival_aggregate()
    try:
        artist, schedule = festival.artist_schedule(slug)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err)) from None

    result = artist.to_dict()
    result["performances"] = [
        p.to_view(festival.venues_by_slug, festival.artists_by_slug)
        for p, _ in schedule
    ]
    return result


if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True))