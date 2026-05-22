"""Shared engine contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from pychess.core import MoveRecord, Side


@dataclass(frozen=True, slots=True)
class EngineContext:
    """Immutable input passed to chess engines."""

    fen: str
    turn: Side
    legal_moves: tuple[str, ...]
    move_history: tuple[MoveRecord, ...] = ()
    time_left: float | None = None


@dataclass(frozen=True, slots=True)
class MoveDecision:
    """A move selected by an engine."""

    uci: str
    confidence: float = 0.0
    elapsed_seconds: float = 0.0
    reason: str | None = None


class NoLegalMovesError(RuntimeError):
    """Raised when an engine is asked to move from a terminal position."""


class PlayerEngine(Protocol):
    """Protocol implemented by all automated chess players."""

    name: str

    def choose_move(self, context: EngineContext) -> MoveDecision:
        """Choose one move from ``context.legal_moves``."""
