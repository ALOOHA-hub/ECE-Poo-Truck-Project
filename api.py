from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import API_TITLE, STATIC_DIR
from helpers import (
    get_artists_view,
    get_festival_metadata,
    get_venues_view,
    load_festival,
)

app = FastAPI(title=API_TITLE)


@app.get("/api/festival")
def read_festival() -> dict:
    festival = load_festival()
    return get_festival_metadata(festival)


@app.get("/api/venues")
def list_venues() -> list[dict]:
    festival = load_festival()
    return get_venues_view(festival)


@app.get("/api/artists")
def list_artists() -> list[dict]:
    festival = load_festival()
    return get_artists_view(festival)


# Mount static frontend files at root (must be mounted after API routes)
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True))