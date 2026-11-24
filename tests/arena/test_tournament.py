from __future__ import annotations

import json
import sqlite3
from collections import Counter
from contextlib import closing

import chess.pgn
import pytest

from pychess.arena.cli import _schedule, main
from pychess.eval.standings import Standings


def test_round_robin_color_balance() -> None:
    players = ("alpha", "beta", "gamma", "delta", "epsilon")
    first = list(_schedule(players, "", "", 1))
    assert len(first) == 10
    assert len({frozenset(pair) for pair in first}) == 10
    assert Counter(w for w, _ in first) == Counter(b for _, b in first)
    both = list(_schedule(players, "", "", 2))
    assert both[10:] == [(b, w) for w, b in first]
    assert list(_schedule((), "a", "b", 2)) == [("a", "b"), ("a", "b")]


def test_archive_survives_engine_start_failure_and_exports_replayable_games(
    tmp_path, capsys
) -> None:
    database = tmp_path / "history.sqlite3"
    config = tmp_path / "match.json"
    config.write_text(
        json.dumps(
            {
                "engines": {"absent": {"type": "uci", "command": ["./absent"]}},
                "arena": {
                    "participants": ["absent", "random", "heuristic"],
                    "database": database.name,
                    "games": 2,
                    "max_plies": 2,
                },
            }
        )
    )
    assert main(["--config", str(config)]) == 0
    text = capsys.readouterr().out
    assert "games=6" in text and "engine_error" in text
    with closing(sqlite3.connect(database)) as connection:
        rows = connection.execute(
            "SELECT white,black,result,termination,error FROM games ORDER BY id"
        ).fetchall()
    assert len(rows) == 6
    for white, black, result, termination, error in rows:
        if "absent" in (white, black):
            assert (result, termination) == (
                "0-1" if white == "absent" else "1-0",
                "engine_error",
            )
            assert error
        else:
            assert (result, termination, error) == ("*", "max_plies", None)

    pgn = tmp_path / "games.pgn"
    assert (
        main(["--database", str(database), "--standings", "--export-pgn", str(pgn)])
        == 0
    )
    report = capsys.readouterr().out
    assert "absent\t0\t0\t4" in report and "Exported 6 games" in report
    with pgn.open(encoding="utf-8") as handle:
        for white, black, result, *_ in rows:
            game = chess.pgn.read_game(handle)
            assert game is not None and not game.errors
            assert (
                game.headers["White"],
                game.headers["Black"],
                game.headers["Result"],
            ) == (white, black, result)
        assert chess.pgn.read_game(handle) is None
    # Explicit pair on the command line takes precedence over a configured tournament.
    assert (
        main(
            [
                "--config",
                str(config),
                "--white",
                "random",
                "--black",
                "random",
                "--games",
                "1",
            ]
        )
        == 0
    )
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("SELECT count(*) FROM games").fetchone() == (7,)


def test_archive_reports_leave_source_database_intact(tmp_path) -> None:
    database = tmp_path / "games.db"
    with pytest.raises(SystemExit):
        main(["--database", str(database), "--standings"])
    assert not database.exists()
    assert main(["--database", str(database), "--max-plies", "1"]) == 0
    before = database.read_bytes()
    with pytest.raises(SystemExit):
        main(["--database", str(database), "--export-pgn", str(database)])
    assert before == database.read_bytes()


def test_standings_skip_unfinished_and_self_play_and_count_draws() -> None:
    scores = Standings()
    scores.record("a", "b", "1-0")
    assert scores.players["a"].elo == 1516
    scores.record("a", "b", "*")
    scores.record("a", "a", "1-0")
    assert scores.players["a"].elo == 1516
    scores.record("b", "a", "1/2-1/2")
    assert scores.players["a"].points == 1.5 and scores.players["b"].points == 0.5
    assert scores.players["a"].unfinished == scores.players["b"].unfinished == 1
    assert scores.players["a"].self_play == 1
