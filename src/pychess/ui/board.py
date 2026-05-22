"""Board geometry helpers shared by rendering and input code."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

FILES = "abcdefgh"
RANKS = "12345678"


@dataclass(frozen=True, slots=True)
class BoardSquare:
    """A square with its screen-space rectangle."""

    name: str
    x: int
    y: int
    size: int
    is_light: bool


@dataclass(frozen=True, slots=True)
class BoardGeometry:
    """Translate chess squares to screen coordinates."""

    left: int
    top: int
    size: int

    @classmethod
    def from_screen(cls, width: int, height: int, *, margin: int = 0) -> BoardGeometry:
        """Create centered board geometry for a screen size."""
        available = max(0, min(width, height) - 2 * margin)
        board_size = (available // 8) * 8
        return cls(
            left=(width - board_size) // 2,
            top=(height - board_size) // 2,
            size=board_size,
        )

    @property
    def square_size(self) -> int:
        """Return one square's width and height."""
        return self.size // 8

    def square(self, name: str) -> BoardSquare:
        """Return screen geometry for a square name such as ``e4``."""
        file_index, rank = self._parse_square(name)
        rank_index_from_top = 8 - rank
        x = self.left + file_index * self.square_size
        y = self.top + rank_index_from_top * self.square_size
        return BoardSquare(
            name=name,
            x=x,
            y=y,
            size=self.square_size,
            is_light=(file_index + rank) % 2 == 1,
        )

    def square_at(self, x: int, y: int) -> str | None:
        """Return the square under screen coordinates, or ``None``."""
        if x < self.left or y < self.top:
            return None
        if x >= self.left + self.size or y >= self.top + self.size:
            return None

        file_index = (x - self.left) // self.square_size
        rank = 8 - ((y - self.top) // self.square_size)
        return f"{FILES[file_index]}{rank}"

    def squares(self) -> Iterator[BoardSquare]:
        """Yield squares in display order, top-left to bottom-right."""
        for rank in range(8, 0, -1):
            for file_name in FILES:
                yield self.square(f"{file_name}{rank}")

    @staticmethod
    def _parse_square(name: str) -> tuple[int, int]:
        if len(name) != 2 or name[0] not in FILES or name[1] not in RANKS:
            msg = f"Invalid square name: {name}"
            raise ValueError(msg)
        return FILES.index(name[0]), int(name[1])
