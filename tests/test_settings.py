from pychess.settings import Settings


def test_default_sprite_sheet_dimensions_are_scaled() -> None:
    settings = Settings()

    assert settings.piece_width == 640
    assert settings.piece_height == 213


def test_settings_can_be_overridden() -> None:
    settings = Settings(screen_width=900, screen_height=600, scale=3)

    assert settings.piece_width == 300
    assert settings.piece_height == 200
