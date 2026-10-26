"""SQLite-backed storage repository implementing BaseFestivalRepository."""

import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from deauville.helpers.slug import slugify
from deauville.models.exceptions import NotFoundError
from deauville.repositories.festival_repository import (
    BaseFestivalRepository,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS venues (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    address TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS artists (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    bio TEXT NOT NULL,
    photo_url TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS performances (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    venue TEXT NOT NULL,
    start TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    description TEXT NOT NULL,
    artist TEXT,
    min_age INTEGER,
    host TEXT,
    acts TEXT,
    teacher TEXT,
    max_participants INTEGER,
    participants TEXT
);
"""

_INSERT_VENUE = "INSERT INTO venues (slug, name, capacity, address) VALUES (?, ?, ?, ?)"
_INSERT_ARTIST = "INSERT INTO artists (slug, name, bio, photo_url) VALUES (?, ?, ?, ?)"
_INSERT_PERF = (
    "INSERT INTO performances"
    " (id, kind, title, venue, start, duration_minutes,"
    " description, artist, min_age, host, acts,"
    " teacher, max_participants, participants)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)


class SqliteFestivalRepository(BaseFestivalRepository):
    """SQLite database repository for festival persistence."""

    def __init__(self, db_path: Path | str = "data/festival.db") -> None:
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.executescript(_SCHEMA)
        return conn

    # ── Read ──────────────────────────────────────────────

    def load_raw(self) -> dict[str, Any]:
        """Query tables and assemble the raw dict representation."""
        if not self.db_path.exists():
            raise NotFoundError(f"Database '{self.db_path}' not found.")

        conn = self._connect()
        try:
            return self._read_all(conn)
        finally:
            conn.close()

    def _read_all(self, conn: sqlite3.Connection) -> dict[str, Any]:
        meta = self._read_meta(conn)
        venues = self._read_venues(conn)
        artists = self._read_artists(conn)
        performances = self._read_performances(conn)

        first = date.fromisoformat(meta["first_day"])
        last = date.fromisoformat(meta["last_day"])
        n = (last - first).days + 1
        days = [(first + timedelta(days=i)).isoformat() for i in range(n)]

        return {
            "name": meta["name"],
            "first_day": meta["first_day"],
            "last_day": meta["last_day"],
            "days": days,
            "venues": venues,
            "artists": artists,
            "performances": performances,
        }

    @staticmethod
    def _read_meta(conn: sqlite3.Connection) -> dict[str, str]:
        rows = conn.execute("SELECT key, value FROM meta").fetchall()
        meta = {r["key"]: r["value"] for r in rows}
        required = ("name", "first_day", "last_day")
        if not all(k in meta for k in required):
            raise NotFoundError("Database is empty or uninitialised.")
        return meta

    @staticmethod
    def _read_venues(conn: sqlite3.Connection) -> list[dict]:
        rows = conn.execute(
            "SELECT name, capacity, address FROM venues"
        ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def _read_artists(conn: sqlite3.Connection) -> list[dict]:
        rows = conn.execute(
            "SELECT name, bio, photo_url FROM artists"
        ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def _read_performances(
        conn: sqlite3.Connection,
    ) -> list[dict[str, Any]]:
        rows = conn.execute("SELECT * FROM performances").fetchall()
        result: list[dict[str, Any]] = []
        for r in rows:
            item: dict[str, Any] = {
                "kind": r["kind"],
                "title": r["title"],
                "venue": r["venue"],
                "start": r["start"],
                "duration_minutes": r["duration_minutes"],
                "description": r["description"],
            }
            kind = r["kind"]
            if kind == "solo":
                item["artist"] = r["artist"] or ""
                item["min_age"] = r["min_age"] or 0
            elif kind == "lineup":
                item["host"] = r["host"] or ""
                raw_acts = r["acts"]
                item["acts"] = json.loads(raw_acts) if raw_acts else []
            elif kind == "workshop":
                item["teacher"] = r["teacher"] or ""
                item["max_participants"] = r["max_participants"] or 1
                raw_parts = r["participants"]
                item["participants"] = json.loads(raw_parts) if raw_parts else []
            result.append(item)
        return result

    # ── Write ─────────────────────────────────────────────

    def save_raw(self, payload: dict[str, Any]) -> None:
        """Serialize dict payload into relational tables atomically."""
        conn = self._connect()
        try:
            with conn:
                self._write_meta(conn, payload)
                self._write_venues(conn, payload)
                self._write_artists(conn, payload)
                self._write_performances(conn, payload)
        finally:
            conn.close()

    @staticmethod
    def _write_meta(conn: sqlite3.Connection, payload: dict[str, Any]) -> None:
        conn.execute("DELETE FROM meta")
        conn.executemany(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            [
                ("name", str(payload.get("name", ""))),
                ("first_day", str(payload.get("first_day", ""))),
                ("last_day", str(payload.get("last_day", ""))),
            ],
        )

    @staticmethod
    def _write_venues(
        conn: sqlite3.Connection,
        payload: dict[str, Any],
    ) -> None:
        conn.execute("DELETE FROM venues")
        rows = [
            (
                slugify(v["name"]),
                v["name"],
                v["capacity"],
                v["address"],
            )
            for v in payload.get("venues", [])
        ]
        conn.executemany(_INSERT_VENUE, rows)

    @staticmethod
    def _write_artists(
        conn: sqlite3.Connection,
        payload: dict[str, Any],
    ) -> None:
        conn.execute("DELETE FROM artists")
        rows = [
            (
                slugify(a["name"]),
                a["name"],
                a.get("bio", ""),
                a.get("photo_url", ""),
            )
            for a in payload.get("artists", [])
        ]
        conn.executemany(_INSERT_ARTIST, rows)

    @staticmethod
    def _write_performances(conn: sqlite3.Connection, payload: dict[str, Any]) -> None:
        conn.execute("DELETE FROM performances")
        rows = []
        for p in payload.get("performances", []):
            start_clean = p["start"].replace(":", "").replace("-", "")[:13]
            perf_id = f"{p['venue']}-{start_clean}"
            acts = json.dumps(p["acts"]) if "acts" in p else None
            parts = json.dumps(p["participants"]) if "participants" in p else None
            rows.append(
                (
                    perf_id,
                    p["kind"],
                    p["title"],
                    p["venue"],
                    p["start"],
                    p["duration_minutes"],
                    p.get("description", ""),
                    p.get("artist"),
                    p.get("min_age"),
                    p.get("host"),
                    acts,
                    p.get("teacher"),
                    p.get("max_participants"),
                    parts,
                )
            )
        conn.executemany(_INSERT_PERF, rows)
