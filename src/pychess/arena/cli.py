"""Command-line interface for the headless arena."""

from __future__ import annotations

import argparse
import sys
from random import Random

from pychess.arena import play_game
from pychess.engines import HeuristicEngine, PlayerEngine, RandomEngine


def main(argv: list[str] | None = None) -> int:
    """Run one or more headless arena games."""
    parser = argparse.ArgumentParser(description="Run PyChess engine matches.")
    parser.add_argument("--white", default="random", choices=sorted(_engine_names()))
    parser.add_argument("--black", default="heuristic", choices=sorted(_engine_names()))
    parser.add_argument("--games", type=int, default=1)
    parser.add_argument("--max-plies", type=int, default=512)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args(argv)

    score = {"1-0": 0, "0-1": 0, "1/2-1/2": 0, "*": 0}
    for game_index in range(args.games):
        white = _build_engine(args.white, seed=args.seed + game_index * 2)
        black = _build_engine(args.black, seed=args.seed + game_index * 2 + 1)
        result = play_game(white, black, max_plies=args.max_plies)
        score[result.result] = score.get(result.result, 0) + 1
        sys.stdout.write(
            f"{game_index + 1}: {result.white} vs {result.black} "
            f"{result.result} ({result.termination}, {result.plies} plies)\n"
        )

    sys.stdout.write(
        "score: "
        f"white={score.get('1-0', 0)}, "
        f"black={score.get('0-1', 0)}, "
        f"draw={score.get('1/2-1/2', 0)}, "
        f"unfinished={score.get('*', 0)}\n"
    )
    return 0


def _engine_names() -> set[str]:
    return {"heuristic", "random"}


def _build_engine(name: str, *, seed: int) -> PlayerEngine:
    if name == "heuristic":
        return HeuristicEngine()
    if name == "random":
        return RandomEngine(Random(seed))

    msg = f"Unknown engine: {name}"
    raise ValueError(msg)


if __name__ == "__main__":
    raise SystemExit(main())
