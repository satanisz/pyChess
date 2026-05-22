"""Random baseline chess engine."""

from __future__ import annotations

from random import Random
from time import perf_counter

from pychess.engines.base import EngineContext, MoveDecision, NoLegalMovesError


class RandomEngine:
    """Choose a random legal move."""

    name = "random"

    def __init__(self, rng: Random | None = None) -> None:
        self._rng = rng or Random()

    def choose_move(self, context: EngineContext) -> MoveDecision:
        """Choose one move uniformly from legal moves."""
        if not context.legal_moves:
            msg = "RandomEngine cannot move without legal moves."
            raise NoLegalMovesError(msg)

        start = perf_counter()
        move = self._rng.choice(context.legal_moves)
        return MoveDecision(
            uci=move,
            confidence=1 / len(context.legal_moves),
            elapsed_seconds=perf_counter() - start,
            reason="uniform random legal move",
        )
