from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pygame
import pytest

import pychess.chess_set as chess_set
from pychess.chess_set import ChessSet


@dataclass(slots=True)
class FakeGame:
    screen: object = object()


class FakeSpriteSheet:
    def __init__(self, filename: Path, *, native_size: bool) -> None:
        self.filename = filename

    def load_grid_images(self, rows: int, cols: int) -> list[object]:
        return [object() for _ in range(rows * cols)]


def test_chess_set_loads_named_pieces(monkeypatch: Any, tmp_path: Path) -> None:
    monkeypatch.setattr(chess_set, "SpriteSheet", FakeSpriteSheet)

    pieces = ChessSet(FakeGame(), sheet_path=tmp_path / "sprites.bmp").pieces

    assert len(pieces) == 12
    assert [piece.color for piece in pieces[:6]] == ["white"] * 6
    assert [piece.color for piece in pieces[6:]] == ["black"] * 6
    assert [piece.name for piece in pieces[:6]] == [
        "king",
        "queen",
        "bishop",
        "knight",
        "rook",
        "pawn",
    ]


def test_resizing_reuses_only_images_at_the_current_size(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    pygame.display.init()
    try:
        pieces = ChessSet(FakeGame(screen=pygame.display.set_mode((1, 1))))
        assert pieces.image_for("white", "king").get_size() == (320, 320)
        original = pieces.scaled_image_for("white", "king", 80)
        assert pieces.scaled_image_for("white", "king", 80) is original
        assert pieces.scaled_image_for("black", "pawn", 200).get_size() == (200, 200)
        assert pieces.scaled_image_for("white", "king", 80) is not original
    finally:
        pygame.display.quit()
