import json
from collections.abc import Iterator
from pathlib import Path
from threading import Event

import pygame
import pytest

from pychess.chess_game import ChessGame, main
from pychess.core import GameController, Side
from pychess.engines import EngineContext, HeuristicEngine, MoveDecision
from pychess.ui.panel import status_text


@pytest.fixture(autouse=True)
def dummy_display(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    yield
    pygame.quit()


def click_square(game: ChessGame, square: str) -> None:
    tile = game.board.square(square)
    pos = (tile.x + tile.size // 2, tile.y + tile.size // 2)
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    game._check_events()


def test_human_move_and_engine_reply() -> None:
    game = ChessGame(black_engine=HeuristicEngine())
    try:
        game._update_screen()
        click_square(game, "e2")
        click_square(game, "e4")
        game._maybe_play_engine_turn()
        assert game._pending is not None
        game._pending.result(timeout=2)
        game._maybe_play_engine_turn()
        game._update_screen()
        assert [m.uci for m in game.game.move_history()] == ["e2e4", "e7e5"]
        assert game.status.turn == Side.WHITE
    finally:
        game.close()


def test_promotion_can_be_cancelled_or_underpromoted() -> None:
    game = ChessGame()
    try:
        game.game = GameController("8/P6k/8/8/8/8/8/6K1 w - - 0 1")
        game.status = game.game.status()
        click_square(game, "a7")
        click_square(game, "a8")
        game._update_screen()
        assert game.promotion == ("a7", "a8")
        game._handle_key(pygame.K_ESCAPE)
        assert not game.game.move_history()
        click_square(game, "a7")
        click_square(game, "a8")
        game._handle_key(pygame.K_4)
        assert game.last_move.uci == "a7a8n"
        assert game.status.is_game_over
        assert "Remis" in status_text(game.status, False)
        click_square(game, "h7")
        assert game.selected_square is None
    finally:
        game.close()


def test_mouse_drag_moves_one_piece() -> None:
    game = ChessGame()
    try:
        click_square(game, "g1")
        tile = game.board.square("f3")
        event = pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(tile.x, tile.y))
        pygame.event.post(event)
        game._check_events()
        assert [move.san for move in game.game.move_history()] == ["Nf3"]
    finally:
        game.close()


def test_quit_during_slow_engine_move_joins_the_worker() -> None:
    started, cancelled = Event(), Event()

    class SlowEngine:
        name = "slow"

        def choose_move(self, context: EngineContext) -> MoveDecision:
            started.set()
            assert cancelled.wait(3), "Window must stop engine before waiting on worker"
            return MoveDecision(context.legal_moves[0])

    game = ChessGame(white_engine=SlowEngine(), release_engines=cancelled.set)
    game._maybe_play_engine_turn()
    assert started.wait(1)
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    assert game.run_game() is None
    assert cancelled.is_set()
    assert game._pending.done()
    assert not game.game.move_history()


def test_invalid_engine_move_stops_game_without_retry() -> None:
    class BrokenEngine:
        name = "broken"

        def choose_move(self, context: EngineContext) -> MoveDecision:
            return MoveDecision("e2e5")

    game = ChessGame(white_engine=BrokenEngine())
    try:
        game._maybe_play_engine_turn()
        game._pending.result(timeout=2)
        game._maybe_play_engine_turn()
        assert "e2e5" in game.failure
        game._maybe_play_engine_turn()
        game._update_screen()
        assert game._pending is None
        assert not game.game.move_history()
    finally:
        game.close()


def test_json_cli_override_and_new_game_menu(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "local.json"
    config.write_text(
        json.dumps({"play": {"white": "heuristic", "black": "heuristic"}})
    )
    seen = []

    def select_players(game: ChessGame) -> tuple[str, str] | None:
        seen.append(tuple(game.players.values()))
        if len(seen) == 1:
            game._handle_key(pygame.K_m)
            game._update_screen()
            pos = game.panel.buttons["white"].center
            pygame.event.post(
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
            )
            game._check_events()
            game._handle_key(pygame.K_RETURN)
        game.close()
        return game.next_players

    monkeypatch.setattr(ChessGame, "run_game", select_players)
    assert main(["--config", str(config), "--white-engine", "none"]) == 0
    assert seen == [("none", "heuristic"), ("heuristic", "heuristic")]
