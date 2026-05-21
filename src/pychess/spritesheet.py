"""Sprite-sheet loading helpers for pygame surfaces."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pygame

from pychess.settings import Settings

type RectLike = tuple[float, float, float, float]
type ColorKey = pygame.Color | tuple[int, int, int] | int | None


class SpriteSheetLoadError(RuntimeError):
    """Raised when pygame cannot load a sprite sheet image."""


class SpriteSheet:
    """Load single images, strips, and grids from a sprite sheet."""

    def __init__(
        self, filename: str | Path, *, settings: Settings | None = None
    ) -> None:
        self.filename = Path(filename)
        self.settings = settings or Settings()

        try:
            sheet = pygame.image.load(str(self.filename)).convert_alpha()
        except pygame.error as exc:
            msg = f"Unable to load spritesheet image: {self.filename}"
            raise SpriteSheetLoadError(msg) from exc

        self.sheet = pygame.transform.scale(
            sheet,
            (self.settings.piece_width, self.settings.piece_height),
        )

    def image_at(
        self, rectangle: RectLike, colorkey: ColorKey = None
    ) -> pygame.Surface:
        """Load a specific image from a rectangle."""
        rect = pygame.Rect(rectangle)
        image = pygame.Surface(rect.size, pygame.SRCALPHA, 32)
        image.blit(self.sheet, (0, 0), rect)

        if colorkey is not None:
            if colorkey == -1:
                colorkey = image.get_at((0, 0))
            image.set_colorkey(colorkey, pygame.RLEACCEL)

        return image

    def images_at(
        self,
        rects: Iterable[RectLike],
        colorkey: ColorKey = None,
    ) -> list[pygame.Surface]:
        """Load images for a collection of rectangles."""
        return [self.image_at(rect, colorkey) for rect in rects]

    def load_strip(
        self,
        rect: RectLike,
        image_count: int,
        colorkey: ColorKey = None,
    ) -> list[pygame.Surface]:
        """Load a horizontal strip of images."""
        rects = [
            (rect[0] + rect[2] * index, rect[1], rect[2], rect[3])
            for index in range(image_count)
        ]
        return self.images_at(rects, colorkey)

    def load_grid_images(
        self,
        num_rows: int,
        num_cols: int,
        *,
        x_margin: int = 0,
        x_padding: int = 0,
        y_margin: int = 0,
        y_padding: int = 0,
    ) -> list[pygame.Surface]:
        """Load images from a grid in row-major order."""
        sheet_width, sheet_height = self.sheet.get_rect().size

        x_sprite_size = (
            sheet_width - 2 * x_margin - (num_cols - 1) * x_padding
        ) / num_cols
        y_sprite_size = (
            sheet_height - 2 * y_margin - (num_rows - 1) * y_padding
        ) / num_rows

        sprite_rects: list[RectLike] = []
        for row_num in range(num_rows):
            for col_num in range(num_cols):
                x = x_margin + col_num * (x_sprite_size + x_padding)
                y = y_margin + row_num * (y_sprite_size + y_padding)
                sprite_rects.append((x, y, x_sprite_size, y_sprite_size))

        return self.images_at(sprite_rects)
