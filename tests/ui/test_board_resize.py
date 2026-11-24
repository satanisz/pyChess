from collections.abc import Iterator

import pygame
import pytest

from pychess.chess_game import DARK_SQUARE, ChessGame


@pytest.fixture
def game(monkeypatch: pytest.MonkeyPatch) -> Iterator[ChessGame]:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    monkeypatch.setattr(pygame.display, "get_desktop_sizes", lambda: [(1920, 1080)])
    game = ChessGame()
    try:
        game._update_screen()
        yield game
    finally:
        game.close()


def click(game: ChessGame, pos: tuple[int, int]) -> None:
    for kind in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        pygame.event.post(pygame.event.Event(kind, button=1, pos=pos))
    game._check_events()
    game._update_screen()


def square_center(game: ChessGame, name: str) -> tuple[int, int]:
    tile = game.board.square(name)
    return tile.x + tile.size // 2, tile.y + tile.size // 2


def resize(game: ChessGame, size: tuple[int, int]) -> None:
    game.window.size = size
    pygame.event.pump()
    game._check_events()
    game._update_screen()
    assert game.screen.get_size() == size


def press(game: ChessGame, key: int, times: int = 1) -> None:
    for _ in range(times):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
    game._check_events()
    game._update_screen()


def test_large_desktop_starts_with_a_larger_resizable_board(game: ChessGame) -> None:
    width, height = game.screen.get_size()
    assert 960 < width <= 1920
    assert 608 < height <= 1080
    assert game.board.size > 560
    assert game.window.resizable


def test_resize_preserves_selection_hit_testing_and_moves(game: ChessGame) -> None:
    resize(game, (640, 480))
    small_tile = game.board.square_size
    click(game, square_center(game, "a1"))
    assert game.selected_square == "a1"
    click(game, square_center(game, "h1"))
    assert game.selected_square == "h1"
    click(game, square_center(game, "e2"))

    resize(game, (1440, 960))
    assert game.board.square_size > small_tile
    assert game.selected_square == "e2"
    assert game.screen.get_at(square_center(game, "c3"))[:3] == DARK_SQUARE
    for name in ("a1", "a8", "h1", "h8"):
        center = square_center(game, name)
        assert game.screen.get_rect().collidepoint(center)
        assert game.board.square_at(*center) == name

    click(game, square_center(game, "e4"))
    resize(game, (640, 480))
    assert [move.uci for move in game.game.move_history()] == ["e2e4"]
    for button in game.panel.buttons.values():
        assert game.screen.get_rect().contains(button)


def test_manual_zoom_by_keyboard_and_panel_keeps_figure_selected(
    game: ChessGame,
) -> None:
    resize(game, (1280, 800))
    click(game, square_center(game, "e2"))
    start_tile = game.board.square_size
    press(game, pygame.K_MINUS)
    reduced_tile = game.board.square_size
    assert reduced_tile < start_tile
    click(game, game.panel.buttons["zoom_in"].center)
    assert game.board.square_size == start_tile
    click(game, game.panel.buttons["zoom_out"].center)
    assert game.board.square_size == reduced_tile
    press(game, pygame.K_PLUS)
    assert game.board.square_size == start_tile
    assert game.selected_square == "e2"
    click(game, square_center(game, "e4"))
    assert game.game.move_history()[0].uci == "e2e4"


def test_zoom_limits_keep_entire_board_visible(game: ChessGame) -> None:
    resize(game, (640, 480))
    press(game, pygame.K_MINUS, times=25)
    minimum = game.board.square_size
    press(game, pygame.K_MINUS)
    assert game.board.square_size == minimum > 0
    press(game, pygame.K_PLUS, times=25)
    maximum = game.board.square_size
    assert maximum > minimum
    press(game, pygame.K_PLUS)
    assert game.board.square_size == maximum
    board = pygame.Rect(game.board.left, game.board.top, maximum * 8, maximum * 8)
    assert game.screen.get_rect().contains(board)
    assert all(not board.colliderect(button) for button in game.panel.buttons.values())
