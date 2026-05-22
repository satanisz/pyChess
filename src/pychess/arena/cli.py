"""Command-line interface for the headless arena."""

from __future__ import annotations

import argparse
import sys

from pychess.arena import play_game
from pychess.engines import available_engine_names, build_engine
from pychess.eval import MatchScore


def main(argv: list[str] | None = None) -> int:
    """Run one or more headless arena games."""
    parser = argparse.ArgumentParser(description="Run PyChess engine matches.")
    parser.add_argument("--white", default="random", choices=available_engine_names())
    parser.add_argument(
        "--black",
        default="heuristic",
        choices=available_engine_names(),
    )
    parser.add_argument("--games", type=int, default=1)
    parser.add_argument("--max-plies", type=int, default=512)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args(argv)

    score = MatchScore()
    for game_index in range(args.games):
        white = build_engine(args.white, seed=args.seed + game_index * 2)
        black = build_engine(args.black, seed=args.seed + game_index * 2 + 1)
        result = play_game(white, black, max_plies=args.max_plies)
        score.add(result)
        sys.stdout.write(
            f"{game_index + 1}: {result.white} vs {result.black} "
            f"{result.result} ({result.termination}, {result.plies} plies)\n"
        )

    sys.stdout.write(f"{score.summary_line()}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
