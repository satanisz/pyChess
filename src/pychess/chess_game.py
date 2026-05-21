"""Chess game, for learning to grab images from a sprite sheet."""

from __future__ import annotations

import sys

import pygame

from pychess.chess_set import ChessSet
from pychess.settings import Settings


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

        for index, piece in enumerate(self.chess_set.pieces[6:]):
            piece.x = index * 320
            piece.blitme()

        pygame.display.flip()


def main() -> int:
    """Run the pygame demo."""
    chess_game = ChessGame()
    chess_game.run_game()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
