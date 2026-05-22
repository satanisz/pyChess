"""Chess game, for learning to grab images from a sprite sheet."""

from __future__ import annotations

import sys

import pygame

from pychess.chess_set import ChessSet
from pychess.core import GameController
from pychess.settings import Settings
from pychess.ui import BoardGeometry

LIGHT_SQUARE = (238, 238, 210)
DARK_SQUARE = (118, 150, 86)


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

    def _update_screen(self) -> None:
        self.screen.fill(self.settings.bg_color)
        self._draw_board()
        self._draw_pieces()
        pygame.display.flip()

    def _draw_board(self) -> None:
        for square in self.board.squares():
            color = LIGHT_SQUARE if square.is_light else DARK_SQUARE
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
