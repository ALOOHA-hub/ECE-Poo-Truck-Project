from datetime import date

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from config import API_TITLE, STATIC_DIR
from helpers import (
    get_festival_metadata,
    load_domain_objects,
)

app = FastAPI(title=API_TITLE)


@app.get("/api/festival")
def read_festival() -> dict:
    data = load_domain_objects()
    return get_festival_metadata(data.raw_data)


@app.get("/api/venues")
def list_venues() -> list[dict]:
    data = load_domain_objects()
    return [v.to_dict() for v in data.venues]


@app.get("/api/artists")
def list_artists() -> list[dict]:
    data = load_domain_objects()
    sorted_artists = sorted(data.artists, key=lambda a: a.slug)
    return [a.to_dict() for a in sorted_artists]


@app.get("/api/programme")
def read_programme(day: date | None = None, venue: str | None = None) -> list[dict]:
    data = load_domain_objects()

    if venue and venue not in data.venues_by_slug:
        raise HTTPException(status_code=404, detail=f"No venue '{venue}'.")

    matching = data.performances
    if day:
        matching = [p for p in matching if p.festival_day == day]
    if venue:
        matching = [p for p in matching if p.venue == venue]

    matching.sort(key=lambda p: (p.start, data.venues_by_slug[p.venue].name))
    return [p.to_view(data.venues_by_slug, data.artists_by_slug) for p in matching]


@app.get("/api/performances/{perf_id}")
def read_performance(perf_id: str) -> dict:
    data = load_domain_objects()
    perf = data.performances_by_id.get(perf_id)
    if not perf:
        raise HTTPException(status_code=404, detail=f"No performance '{perf_id}'.")
    return perf.to_view(data.venues_by_slug, data.artists_by_slug)


@app.get("/api/artists/{slug}")
def read_artist(slug: str) -> dict:
    data = load_domain_objects()
    artist = data.artists_by_slug.get(slug)
    if not artist:
        raise HTTPException(status_code=404, detail=f"No artist '{slug}'.")

    matching_perfs = [p for p in data.performances if p.involves(slug)]
    matching_perfs.sort(key=lambda p: p.start)

    result = artist.to_dict()
    result["performances"] = [
        p.to_view(data.venues_by_slug, data.artists_by_slug) for p in matching_perfs
    ]
    return result


# Mount static web frontend (must remain after all API routes)
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True))