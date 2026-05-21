from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pychess.chess_set as chess_set
from pychess.chess_set import ChessSet


@dataclass(slots=True)
class FakeGame:
    screen: object = object()


class FakeSpriteSheet:
    def __init__(self, filename: Path) -> None:
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
