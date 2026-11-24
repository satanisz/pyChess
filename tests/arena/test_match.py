from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from random import Random

import chess.pgn
import pytest

from pychess.arena import play_game
from pychess.engines import EngineContext, MoveDecision, RandomEngine
from pychess.engines.uci import EngineFailure, EngineTimeout


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
    assert '[Result "0-1"]' in result.pgn
    assert result.pgn.endswith("0-1")


@pytest.mark.parametrize(
    ("error", "reason"),
    [(EngineFailure("crashed"), "engine_error"), (EngineTimeout("late"), "timeout")],
)
def test_engine_forfeit_after_a_move(error: EngineFailure, reason: str) -> None:
    class BrokenEngine:
        name = "broken"

        def choose_move(self, context: EngineContext) -> MoveDecision:
            raise error

    result = play_game(RandomEngine(Random(1)), BrokenEngine())
    assert (result.result, result.termination, result.error) == (
        "1-0",
        reason,
        str(error),
    )
    assert result.plies == 1
    assert result.pgn.endswith("1-0")
    decoded = chess.pgn.read_game(StringIO(result.pgn))
    assert decoded is not None and not decoded.errors
    assert decoded.headers["Result"] == result.result
    assert tuple(m.uci() for m in decoded.mainline_moves()) == (result.moves[0].uci,)


def test_claimed_draw_survives_export_from_custom_fen() -> None:
    fen = "7k/8/8/8/8/8/8/KR6 w - - 100 51"
    result = play_game(IllegalEngine(), IllegalEngine(), initial_fen=fen)
    assert result.result == "1/2-1/2" and result.plies == 0
    assert result.pgn.endswith(result.result)
    assert f'[FEN "{fen}"]' in result.pgn
