import chess

from pychess.core import Side
from pychess.models import PIECE_PLANES, encode_position


def test_encode_position_creates_12_piece_planes() -> None:
    encoded = encode_position(chess.STARTING_FEN)

    assert len(encoded.planes) == 12
    assert len(encoded.flat()) == 12 * 8 * 8
    assert encoded.side_to_move == Side.WHITE
    assert PIECE_PLANES[0] == "white_pawn"
    assert PIECE_PLANES[-1] == "black_king"


def test_encode_position_uses_white_perspective() -> None:
    encoded = encode_position(chess.STARTING_FEN)
    white_rook_plane = encoded.planes[3]
    black_king_plane = encoded.planes[11]

    assert white_rook_plane[7][0] == 1
    assert white_rook_plane[7][7] == 1
    assert black_king_plane[0][4] == 1


def test_encode_position_counts_starting_material() -> None:
    encoded = encode_position(chess.STARTING_FEN)

    assert sum(sum(row) for row in encoded.planes[0]) == 8
    assert sum(sum(row) for row in encoded.planes[6]) == 8
    assert sum(sum(row) for plane in encoded.planes for row in plane) == 32
