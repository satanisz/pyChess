"""Command-line interface for headless matches, tournaments and archived games."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from collections.abc import Iterator
from contextlib import nullcontext
from itertools import combinations
from pathlib import Path

from pychess.arena import play_game
from pychess.arena.archive import archive_standings, export_pgn, open_archive, save_game
from pychess.config import AppConfig, load_config
from pychess.eval import MatchScore
from pychess.eval.standings import Standings


def _schedule(
    participants: tuple[str, ...], white: str, black: str, games: int
) -> Iterator[tuple[str, str]]:
    for repetition in range(games):
        if not participants:
            yield white, black
            continue
        for (i, first), (j, second) in combinations(enumerate(participants), 2):
            # Balance colors within one cycle, then reverse every pairing.
            if (j - i + repetition) % 2:
                yield first, second
            else:
                yield second, first


def _run_games(args: argparse.Namespace, cfg: AppConfig, database: Path | None) -> None:
    arena = cfg.arena
    has_pair = args.white is not None or args.black is not None
    if args.participants is not None and has_pair:
        raise ValueError("--participants and --white/--black select different modes")
    participants = arena.participants
    if args.participants is not None:
        participants = tuple(args.participants)
        if len(participants) < 2 or len(set(participants)) != len(participants):
            raise ValueError("--participants requires at least two distinct engine IDs")
    elif has_pair:
        participants = ()
    white = arena.white if args.white is None else args.white
    black = arena.black if args.black is None else args.black
    names = cfg.engine_names()
    for engine in participants or (white, black):
        if engine not in names:
            raise ValueError(
                f"Unknown engine {engine!r}. Available: {', '.join(names)}"
            )
    games = arena.games if args.games is None else args.games
    max_plies = arena.max_plies if args.max_plies is None else args.max_plies
    seed = arena.seed if args.seed is None else args.seed
    if games < 1 or max_plies < 1:
        raise ValueError("--games and --max-plies must both be positive")
    score = MatchScore()
    standings = Standings()
    schedule = _schedule(participants, white, black, games)
    with open_archive(database) if database else nullcontext() as connection:
        for index, (first, second) in enumerate(schedule):
            game_seed = seed + 2 * index
            with (
                cfg.open_engine(first, seed=game_seed) as white_engine,
                cfg.open_engine(second, seed=game_seed + 1) as black_engine,
            ):
                result = play_game(white_engine, black_engine, max_plies=max_plies)
            if connection is not None:
                save_game(connection, result, game_seed, max_plies)
            score.add(result)
            standings.record(result.white, result.black, result.result)
            detail = result.error or result.illegal_move
            sys.stdout.write(
                f"{index + 1}: {result.white} vs {result.black} "
                f"{result.result} ({result.termination}, {result.plies} plies)"
                + (f" — {detail}" if detail else "")
                + "\n"
            )
    sys.stdout.write(score.summary_line() + "\n" + standings.table() + "\n")


def _report(args: argparse.Namespace, database: Path | None) -> None:
    if database is None:
        raise ValueError("Archive reports require --database or arena.database in JSON")
    if any(
        value is not None
        for value in (
            args.white,
            args.black,
            args.participants,
            args.games,
            args.max_plies,
            args.seed,
        )
    ):
        raise ValueError("Run games and read archive reports in separate commands")
    if args.export_pgn is not None:
        sources = (database,) if args.config is None else (database, args.config)
        if any(args.export_pgn.resolve() == path.resolve() for path in sources):
            raise ValueError("PGN destination must differ from the database and config")
    with open_archive(database, read_only=True) as connection:
        if args.standings:
            standings = archive_standings(connection)
            sys.stdout.write(standings.table(by_elo=args.standings == "elo") + "\n")
        if args.export_pgn is not None:
            count = export_pgn(connection, args.export_pgn)
            sys.stdout.write(f"Exported {count} games to {args.export_pgn}\n")


def main(argv: list[str] | None = None) -> int:
    """Run games, or query the archive when a reporting flag is supplied."""
    parser = argparse.ArgumentParser(description="Run PyChess engine matches.")
    parser.add_argument("--config", type=Path, help="JSON engine and arena settings")
    parser.add_argument("--white", help="engine playing White in a fixed-color match")
    parser.add_argument("--black", help="engine playing Black in a fixed-color match")
    parser.add_argument(
        "--participants",
        nargs="+",
        metavar="ENGINE",
        help="round robin with alternating colors, two or more engines",
    )
    parser.add_argument("--games", type=int, help="number of games per pairing")
    parser.add_argument("--max-plies", type=int, help="limit half-moves in a game")
    parser.add_argument("--seed", type=int, help="initial seed for built-in engines")
    parser.add_argument("--database", type=Path, help="SQLite file for games and PGNs")
    reports = parser.add_mutually_exclusive_group()
    reports.add_argument(
        "--standings",
        action="store_const",
        const="points",
        help="report cumulative standings ordered by points and exit",
    )
    reports.add_argument(
        "--elo",
        dest="standings",
        action="store_const",
        const="elo",
        help="report the league ranking ordered by local Elo and exit",
    )
    parser.add_argument(
        "--export-pgn",
        type=Path,
        metavar="FILE",
        help="write all archived games to FILE and exit",
    )
    args = parser.parse_args(argv)
    try:
        cfg = load_config(args.config)
        database = args.database if args.database is not None else cfg.arena.database
        if args.standings or args.export_pgn is not None:
            _report(args, database)
        else:
            _run_games(args, cfg, database)
    except (ValueError, OSError, sqlite3.Error) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
