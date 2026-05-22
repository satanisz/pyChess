"""Chess game, for learning to grab images from a sprite sheet."""

from __future__ import annotations

import sys

import pygame

from pychess.chess_set import ChessSet
from pychess.core import GameController, IllegalMoveError, MoveRecord
from pychess.settings import Settings
from pychess.ui import BoardGeometry

LIGHT_SQUARE = (238, 238, 210)
DARK_SQUARE = (118, 150, 86)
SELECTED_SQUARE = (186, 202, 68)
LAST_MOVE_SQUARE = (246, 246, 105)
LEGAL_MOVE_DOT = (35, 35, 35)


class ChessGame:
    """Overall class to manage game assets and behavior."""

    def __init__(self) -> None:
        """Initialize the game, and create resources."""
        pygame.init()
        self.settings = Settings()

        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height)
        )
        pygame.display.set_caption("Chess")

        self.game = GameController()
        self.board = BoardGeometry.from_screen(
            self.settings.screen_width,
            self.settings.screen_height,
        )
        self.chess_set = ChessSet(self)
        self.selected_square: str | None = None
        self.last_move: MoveRecord | None = None

    def run_game(self) -> None:
        """Start the main loop for the game."""
        while True:
            self._check_events()
            self._update_screen()

    def _check_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_left_click(event.pos)

    def _update_screen(self) -> None:
        self.screen.fill(self.settings.bg_color)
        self._draw_board()
        self._draw_highlights()
        self._draw_pieces()
        pygame.display.flip()

    def _handle_left_click(self, position: tuple[int, int]) -> None:
        square = self.board.square_at(*position)
        if square is None:
            self.selected_square = None
            return

        if self.selected_square is None:
            self._select_square(square)
            return

        if square == self.selected_square:
            self.selected_square = None
            return

        clicked_piece = self.game.piece_at(square)
        if clicked_piece is not None and clicked_piece.color == self.game.turn:
            self._select_square(square)
            return

        try:
            self.last_move = self.game.push_between(self.selected_square, square)
        except IllegalMoveError:
            self.selected_square = None
            return

        self.selected_square = None

    def _select_square(self, square: str) -> None:
        piece = self.game.piece_at(square)
        if piece is not None and piece.color == self.game.turn:
            self.selected_square = square

    def _draw_board(self) -> None:
        for square in self.board.squares():
            color = LIGHT_SQUARE if square.is_light else DARK_SQUARE
            rect = pygame.Rect(square.x, square.y, square.size, square.size)
            pygame.draw.rect(self.screen, color, rect)

    def _draw_highlights(self) -> None:
        if self.last_move is not None:
            self._draw_square_fill(self.last_move.uci[:2], LAST_MOVE_SQUARE)
            self._draw_square_fill(self.last_move.uci[2:4], LAST_MOVE_SQUARE)

        if self.selected_square is None:
            return

        self._draw_square_fill(self.selected_square, SELECTED_SQUARE)
        for destination in self.game.legal_destinations_from(self.selected_square):
            square = self.board.square(destination)
            center = (square.x + square.size // 2, square.y + square.size // 2)
            radius = max(6, square.size // 8)
            pygame.draw.circle(self.screen, LEGAL_MOVE_DOT, center, radius)

    def _draw_square_fill(self, square_name: str, color: tuple[int, int, int]) -> None:
        square = self.board.square(square_name)
        rect = pygame.Rect(square.x, square.y, square.size, square.size)
        pygame.draw.rect(self.screen, color, rect)

    def _draw_pieces(self) -> None:
        for piece in self.game.pieces():
            square = self.board.square(piece.square)
            image = self.chess_set.scaled_image_for(
                piece.color.value,
                piece.piece_type,
                square.size,
            )
            self.screen.blit(image, (square.x, square.y))


def main() -> int:
    """Run the pygame demo."""
    chess_game = ChessGame()
    chess_game.run_game()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
