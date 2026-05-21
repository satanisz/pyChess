from __future__ import annotations

from typing import Any

from pychess.spritesheet import SpriteSheet


class FakeRect:
    size = (120, 40)


class FakeSheet:
    def get_rect(self) -> FakeRect:
        return FakeRect()


def test_load_grid_images_builds_row_major_rectangles(monkeypatch: Any) -> None:
    sheet = SpriteSheet.__new__(SpriteSheet)
    sheet.sheet = FakeSheet()

    monkeypatch.setattr(sheet, "images_at", lambda rects: list(rects))

    assert sheet.load_grid_images(2, 6) == [
        (0.0, 0.0, 20.0, 20.0),
        (20.0, 0.0, 20.0, 20.0),
        (40.0, 0.0, 20.0, 20.0),
        (60.0, 0.0, 20.0, 20.0),
        (80.0, 0.0, 20.0, 20.0),
        (100.0, 0.0, 20.0, 20.0),
        (0.0, 20.0, 20.0, 20.0),
        (20.0, 20.0, 20.0, 20.0),
        (40.0, 20.0, 20.0, 20.0),
        (60.0, 20.0, 20.0, 20.0),
        (80.0, 20.0, 20.0, 20.0),
        (100.0, 20.0, 20.0, 20.0),
    ]
