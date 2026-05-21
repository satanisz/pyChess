"""Module to represent a chess set, and individual pieces."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pygame

from pychess.assets import sprite_sheet_path
from pychess.spritesheet import SpriteSheet

PIECE_COLORS = ("white", "black")
PIECE_NAMES = ("king", "queen", "bishop", "knight", "rook", "pawn")


class HasScreen(Protocol):
    """A pygame object that exposes the display surface used by pieces."""

    screen: pygame.Surface


class ChessSet:
    """Represents a set of chess pieces.

    Each piece is an object of the Piece class.
    """

    def __init__(
        self,
        chess_game: HasScreen,
        *,
        sheet_path: str | Path | None = None,
    ) -> None:
        """Initialize attributes to represent the overall set of pieces."""
        self.chess_game = chess_game
        self.sheet_path = Path(sheet_path) if sheet_path is not None else None
        self.pieces: list[Piece] = self._load_pieces()

    def _load_pieces(self) -> list[Piece]:
        """Build the complete set from the bundled sprite sheet."""
        if self.sheet_path is not None:
            return self._load_from_sheet(self.sheet_path)

        with sprite_sheet_path() as path:
            return self._load_from_sheet(path)

    def _load_from_sheet(self, filename: Path) -> list[Piece]:
        sprite_sheet = SpriteSheet(filename)
        piece_images = sprite_sheet.load_grid_images(2, 6)

        pieces: list[Piece] = []
        for piece_num, (color, name) in enumerate(
            (color, name) for color in PIECE_COLORS for name in PIECE_NAMES
        ):
            pieces.append(
                Piece(
                    screen=self.chess_game.screen,
                    image=piece_images[piece_num],
                    name=name,
                    color=color,
                )
            )
        return pieces


@dataclass(slots=True)
class Piece:
    """Represents a chess piece."""

    screen: pygame.Surface
    image: pygame.Surface
    name: str
    color: str
    x: float = 0.0
    y: float = 0.0
    rect: pygame.Rect | None = None

    def blitme(self) -> None:
        """Draw the piece at its current location."""
        self.rect = self.image.get_rect()
        self.rect.topleft = self.x, self.y
        self.screen.blit(self.image, self.rect)
