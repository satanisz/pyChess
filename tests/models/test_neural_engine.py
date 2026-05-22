from dataclasses import dataclass

import pytest

from pychess.core import GameController, Side
from pychess.engines import EngineContext, NoLegalMovesError
from pychess.models import NeuralEngine, NoScoredLegalMovesError


@dataclass(frozen=True, slots=True)
class FakeScorer:
    scores: dict[str, float]
    name: str = "fake"

    def score_moves(self, context: EngineContext) -> dict[str, float]:
        return self.scores


def context_from_game(game: GameController) -> EngineContext:
    return EngineContext(
        fen=game.fen(),
        turn=game.turn,
        legal_moves=game.legal_moves(),
        move_history=game.move_history(),
    )


def test_neural_engine_chooses_best_scored_legal_move() -> None:
    game = GameController()
    scorer = FakeScorer({"a1a8": 999.0, "e2e4": 0.8, "g1f3": 0.2})
    engine = NeuralEngine(scorer)

    decision = engine.choose_move(context_from_game(game))

    assert engine.name == "neural:fake"
    assert decision.uci == "e2e4"
    assert decision.confidence > 0


def test_neural_engine_rejects_terminal_context() -> None:
    context = EngineContext(
        fen=GameController().fen(),
        turn=Side.WHITE,
        legal_moves=(),
    )

    with pytest.raises(NoLegalMovesError):
        NeuralEngine(FakeScorer({})).choose_move(context)


def test_neural_engine_requires_at_least_one_scored_legal_move() -> None:
    game = GameController()
    scorer = FakeScorer({"a1a8": 999.0})

    with pytest.raises(NoScoredLegalMovesError):
        NeuralEngine(scorer).choose_move(context_from_game(game))
