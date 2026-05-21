"""Helpers for loading files bundled with the package."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path


@contextmanager
def sprite_sheet_path() -> Iterator[Path]:
    """Expose the bundled chess sprite sheet as a real filesystem path."""
    resource = files("pychess").joinpath("images", "chess_pieces_sprite.bmp")
    with as_file(resource) as path:
        yield path
