"""Feature encoders for neural chess models."""

from __future__ import annotations

from dataclasses import dataclass

import chess

from pychess.core import Side

PIECE_PLANES = (
    "white_pawn",
    "white_knight",
    "white_bishop",
    "white_rook",
    "white_queen",
    "white_king",
    "black_pawn",
    "black_knight",
    "black_bishop",
    "black_rook",
    "black_queen",
    "black_king",
)

_PLANE_BY_PIECE = {
    (chess.WHITE, chess.PAWN): 0,
    (chess.WHITE, chess.KNIGHT): 1,
    (chess.WHITE, chess.BISHOP): 2,
    (chess.WHITE, chess.ROOK): 3,
    (chess.WHITE, chess.QUEEN): 4,
    (chess.WHITE, chess.KING): 5,
    (chess.BLACK, chess.PAWN): 6,
    (chess.BLACK, chess.KNIGHT): 7,
    (chess.BLACK, chess.BISHOP): 8,
    (chess.BLACK, chess.ROOK): 9,
    (chess.BLACK, chess.QUEEN): 10,
    (chess.BLACK, chess.KING): 11,
}

Plane = tuple[tuple[int, ...], ...]


@dataclass(frozen=True, slots=True)
class EncodedPosition:
    """Dependency-free board tensor representation."""

    planes: tuple[Plane, ...]
    side_to_move: Side

    def flat(self) -> tuple[int, ...]:
        """Return planes flattened in plane-row-column order."""
        return tuple(value for plane in self.planes for row in plane for value in row)


def encode_position(fen: str) -> EncodedPosition:
    """Encode a FEN position into 12 piece planes from White's perspective."""
    board = chess.Board(fen)
    mutable_planes = [[[0 for _ in range(8)] for _ in range(8)] for _ in range(12)]

    for square, piece in board.piece_map().items():
        plane = _PLANE_BY_PIECE[(piece.color, piece.piece_type)]
        row = 7 - chess.square_rank(square)
        col = chess.square_file(square)
        mutable_planes[plane][row][col] = 1

    return EncodedPosition(
        planes=tuple(
            tuple(tuple(cell for cell in row) for row in plane)
            for plane in mutable_planes
        ),
        side_to_move=Side.from_chess_color(board.turn),
    )
