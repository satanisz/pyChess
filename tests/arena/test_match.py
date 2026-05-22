from __future__ import annotations

from dataclasses import dataclass
from random import Random

from pychess.arena import play_game
from pychess.engines import EngineContext, MoveDecision, RandomEngine


@dataclass(slots=True)
class IllegalEngine:
    name: str = "illegal"

    def choose_move(self, context: EngineContext) -> MoveDecision:
        return MoveDecision(uci="a1a8", reason="intentionally illegal")


def test_arena_runs_headless_game_until_max_plies() -> None:
    result = play_game(
        RandomEngine(Random(1)),
        RandomEngine(Random(2)),
        max_plies=4,
    )

    assert result.result == "*"
    assert result.termination == "max_plies"
    assert result.plies == 4
    assert len(result.moves) == 4
    assert '[Event "PyChess Arena"]' in result.pgn


def test_arena_detects_illegal_engine_move() -> None:
    result = play_game(IllegalEngine(), RandomEngine(Random(2)))

    assert result.result == "0-1"
    assert result.termination == "illegal_move"
    assert result.illegal_move == "a1a8"
    assert result.plies == 0
