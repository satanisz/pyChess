from pathlib import Path

from pychess.assets import sprite_sheet_path


def test_sprite_sheet_resource_exists() -> None:
    with sprite_sheet_path() as path:
        assert path.is_file()
        assert path.suffix == ".bmp"
        assert path.parent.name == "images"


def test_sprite_sheet_resource_is_inside_package() -> None:
    with sprite_sheet_path() as path:
        assert "pychess" in Path(path).parts
