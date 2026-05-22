from __future__ import annotations

from random import Random

import pytest

from pychess.core import GameController, Side
from pychess.engines import (
    EngineContext,
    HeuristicEngine,
    NoLegalMovesError,
    RandomEngine,
)


def context_from_game(game: GameController) -> EngineContext:
    return EngineContext(
        fen=game.fen(),
        turn=game.turn,
        legal_moves=game.legal_moves(),
        move_history=game.move_history(),
    )


def test_random_engine_chooses_legal_move() -> None:
    game = GameController()
    engine = RandomEngine(Random(7))

    decision = engine.choose_move(context_from_game(game))

    assert decision.uci in game.legal_moves()
    assert decision.confidence == 1 / 20
    assert decision.elapsed_seconds >= 0


def test_random_engine_rejects_terminal_context() -> None:
    context = EngineContext(
        fen=GameController().fen(),
        turn=Side.WHITE,
        legal_moves=(),
    )

    with pytest.raises(NoLegalMovesError):
        RandomEngine(Random(1)).choose_move(context)


def test_heuristic_engine_finds_one_move_checkmate() -> None:
    game = GameController()
    game.push_uci("f2f3")
    game.push_uci("e7e5")
    game.push_uci("g2g4")
    engine = HeuristicEngine()

    decision = engine.choose_move(context_from_game(game))

    assert decision.uci == "d8h4"
    assert decision.confidence > 0
    assert "score" in decision.reason


def test_heuristic_engine_rejects_terminal_context() -> None:
    context = EngineContext(
        fen=GameController().fen(),
        turn=Side.WHITE,
        legal_moves=(),
    )

    with pytest.raises(NoLegalMovesError):
        HeuristicEngine().choose_move(context)
