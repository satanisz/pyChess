"""Lightweight piece enums used by chess state experiments."""

from __future__ import annotations

from enum import IntEnum, IntFlag


class PieceType(IntEnum):
    """Integer identifiers for chess piece types."""

    EMPTY = 0
    KING = 1
    PAWN = 2
    KNIGHT = 3
    BISHOP = 4
    ROOK = 5
    QUEEN = 6


class PieceColor(IntFlag):
    """Bit flags for chess piece colors."""

    WHITE = 8
    BLACK = 16
