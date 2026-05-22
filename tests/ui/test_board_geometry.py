import pytest

from pychess.ui import BoardGeometry


def test_board_geometry_is_centered_and_uses_square_board() -> None:
    board = BoardGeometry.from_screen(1920, 640)

    assert board.left == 640
    assert board.top == 0
    assert board.size == 640
    assert board.square_size == 80


def test_square_coordinates_use_white_perspective() -> None:
    board = BoardGeometry(left=10, top=20, size=640)

    assert board.square("a8").x == 10
    assert board.square("a8").y == 20
    assert board.square("h1").x == 570
    assert board.square("h1").y == 580


def test_square_at_returns_square_or_none() -> None:
    board = BoardGeometry(left=10, top=20, size=640)

    assert board.square_at(10, 20) == "a8"
    assert board.square_at(649, 659) == "h1"
    assert board.square_at(9, 20) is None
    assert board.square_at(650, 660) is None


def test_invalid_square_is_rejected() -> None:
    board = BoardGeometry(left=0, top=0, size=640)

    with pytest.raises(ValueError):
        board.square("z9")
