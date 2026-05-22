"""Adapter for neural move-scoring models."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from pychess.engines import EngineContext, MoveDecision, NoLegalMovesError


class MoveScorer(Protocol):
    """Protocol for neural models that score candidate moves."""

    name: str

    def score_moves(self, context: EngineContext) -> Mapping[str, float]:
        """Return scores keyed by UCI move."""


class NoScoredLegalMovesError(RuntimeError):
    """Raised when a model does not score any legal move."""


class NeuralEngine:
    """Choose the highest-scoring legal move from a neural model."""

    def __init__(self, scorer: MoveScorer) -> None:
        self.scorer = scorer
        self.name = f"neural:{scorer.name}"

    def choose_move(self, context: EngineContext) -> MoveDecision:
        """Score moves and choose the best legal move only."""
        if not context.legal_moves:
            msg = "NeuralEngine cannot move without legal moves."
            raise NoLegalMovesError(msg)

        legal_moves = set(context.legal_moves)
        legal_scores = {
            move: score
            for move, score in self.scorer.score_moves(context).items()
            if move in legal_moves
        }
        if not legal_scores:
            msg = f"{self.scorer.name} did not score any legal move."
            raise NoScoredLegalMovesError(msg)

        best_move, best_score = max(
            legal_scores.items(),
            key=lambda item: (item[1], item[0]),
        )
        return MoveDecision(
            uci=best_move,
            confidence=_confidence(best_score, tuple(legal_scores.values())),
            reason=f"model score {best_score}",
        )


def _confidence(best_score: float, scores: tuple[float, ...]) -> float:
    if len(scores) == 1:
        return 1.0

    worst_score = min(scores)
    if best_score == worst_score:
        return 1 / len(scores)

    return (best_score - worst_score) / max(1.0, abs(best_score) + abs(worst_score))
