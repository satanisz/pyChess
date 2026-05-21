"""Runtime settings for the pygame demo."""

from __future__ import annotations

from dataclasses import dataclass

Color = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class Settings:
    """Display and sprite scaling settings."""

    screen_width: int = 1920
    screen_height: int = 640
    scale: int = 3
    bg_color: Color = (110, 0, 110)

    @property
    def piece_width(self) -> int:
        """Scaled width of the complete sprite sheet."""
        return self.screen_width // self.scale

    @property
    def piece_height(self) -> int:
        """Scaled height of the complete sprite sheet."""
        return self.screen_height // self.scale
