"""Persist each finished game independently and replay the archive for reporting."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

from pychess.arena.match import ArenaGameResult
from pychess.eval.standings import Standings


@contextmanager
def open_archive(
    path: Path, *, read_only: bool = False
) -> Iterator[sqlite3.Connection]:
    if read_only:
        uri = path.resolve().as_uri() + "?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
    with closing(connection):
        if not read_only:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY,
                    played_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    white TEXT NOT NULL,
                    black TEXT NOT NULL,
                    result TEXT NOT NULL,
                    termination TEXT NOT NULL,
                    plies INTEGER NOT NULL,
                    seed TEXT NOT NULL,
                    max_plies INTEGER NOT NULL,
                    illegal_move TEXT,
                    error TEXT,
                    pgn TEXT NOT NULL
                )"""
            )
        yield connection


def save_game(
    connection: sqlite3.Connection, game: ArenaGameResult, seed: int, max_plies: int
) -> None:
    with connection:
        connection.execute(
            """INSERT INTO games
            (white, black, result, termination, plies, seed, max_plies,
             illegal_move, error, pgn) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                game.white,
                game.black,
                game.result,
                game.termination,
                game.plies,
                str(seed),
                max_plies,
                game.illegal_move,
                game.error,
                game.pgn,
            ),
        )


def archive_standings(connection: sqlite3.Connection) -> Standings:
    standings = Standings()
    for white, black, result in connection.execute(
        "SELECT white, black, result FROM games ORDER BY id"
    ):
        standings.record(white, black, result)
    return standings


def export_pgn(connection: sqlite3.Connection, destination: Path) -> int:
    """Replace the destination with a complete UTF-8 export of all archived games."""
    count = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=destination.parent, delete=False
    ) as output:
        staged = Path(output.name)
        try:
            for (pgn,) in connection.execute("SELECT pgn FROM games ORDER BY id"):
                output.write(pgn.rstrip() + "\n\n")
                count += 1
            output.close()
            staged.replace(destination)
        finally:
            staged.unlink(missing_ok=True)
    return count
