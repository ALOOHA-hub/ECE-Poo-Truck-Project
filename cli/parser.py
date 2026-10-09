import argparse
from pathlib import Path
import sys

from cli.handlers import (
    handle_add,
    handle_artist,
    handle_cancel,
    handle_now,
    handle_programme,
    handle_serve,
    handle_summary,
    handle_venues,
)
from config import DEFAULT_DATA_PATH, DEFAULT_SERVER_HOST, DEFAULT_SERVER_PORT
from repositories import FestivalRepository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="festival",
        description="Deauville Festival du Rire management CLI.",
    )
    parser.add_argument(
        "-d",
        "--data",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help="Path to the festival JSON dataset (defaults to data/festival.json).",
    )

    subparsers = parser.add_subparsers(dest="subcommand", required=False)

    # venues
    subparsers.add_parser("venues", help="List all festival venues and total capacity.")

    # programme <day>
    prog_parser = subparsers.add_parser("programme", help="Show the day's schedule.")
    prog_parser.add_argument("day", help="Target date in YYYY-MM-DD format.")

    # artist <slug>
    artist_parser = subparsers.add_parser("artist", help="Show an artist's festival schedule.")
    artist_parser.add_argument("slug", help="Artist unique slug identifier.")

    # now <moment>
    now_parser = subparsers.add_parser("now", help="Show currently running and upcoming performances.")
    now_parser.add_argument("moment", help="ISO datetime timestamp (YYYY-MM-DDTHH:MM).")

    # add
    subparsers.add_parser("add", help="Interactively schedule a new solo performance.")

    # cancel <id>
    cancel_parser = subparsers.add_parser("cancel", help="Cancel a scheduled performance by its unique ID.")
    cancel_parser.add_argument("id", help="Performance ID (<venue>-<YYYY-MM-DD-HHMM>).")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Launch the web API server.")
    serve_parser.add_argument("--host", default=DEFAULT_SERVER_HOST, help="Host to bind to.")
    serve_parser.add_argument("--port", type=int, default=DEFAULT_SERVER_PORT, help="Port to bind to.")

    return parser


def run_cli(args: list[str] | None = None) -> None:
    parser = build_parser()
    parsed = parser.parse_args(args)

    repo = FestivalRepository(parsed.data)

    try:
        if parsed.subcommand is None:
            handle_summary(repo)
        elif parsed.subcommand == "venues":
            handle_venues(repo)
        elif parsed.subcommand == "programme":
            handle_programme(repo, parsed.day)
        elif parsed.subcommand == "artist":
            handle_artist(repo, parsed.slug)
        elif parsed.subcommand == "now":
            handle_now(repo, parsed.moment)
        elif parsed.subcommand == "add":
            handle_add(repo)
        elif parsed.subcommand == "cancel":
            handle_cancel(repo, parsed.id)
        elif parsed.subcommand == "serve":
            handle_serve(host=parsed.host, port=parsed.port)
    except (ValueError, KeyError) as err:
        print(f"Error: {err}")
        sys.exit(1)