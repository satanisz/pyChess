"""Desktop chess for human and engine players."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import ExitStack
from pathlib import Path

import pygame

from pychess.chess_set import ChessSet
from pychess.config import load_config
from pychess.core import GameController, IllegalMoveError, MoveRecord, Side
from pychess.engines import EngineContext, MoveDecision, PlayerEngine
from pychess.ui import BoardGeometry
from pychess.ui.panel import BACKGROUND, MUTED, PROMOTIONS, GamePanel

LIGHT_SQUARE = (237, 232, 209)
DARK_SQUARE = (118, 150, 119)
SELECTED_SQUARE = (181, 203, 117)
LAST_MOVE_SQUARE = (209, 216, 146)
LEGAL_MOVE_DOT = (63, 84, 68)


class ChessGame:
    def __init__(
        self,
        *,
        white_engine: PlayerEngine | None = None,
        black_engine: PlayerEngine | None = None,
        engine_names: tuple[str, ...] = (),
        release_engines: Callable[[], None] | None = None,
        window_size: tuple[int, int] | None = None,
        zoom_percent: int = 90,
    ) -> None:
        pygame.init()
        self.clock = pygame.time.Clock()
        desktop_width, desktop_height = pygame.display.get_desktop_sizes()[0]
        width = min(1400, desktop_width - min(48, desktop_width // 10))
        height = min(960, desktop_height - min(64, desktop_height // 10))
        self.window = pygame.Window(
            "PyChess", size=window_size or (width, height), resizable=True
        )
        self.window.minimum_size = (min(640, width), min(480, height))
        self.screen = self.window.get_surface()
        self.window_size = self.screen.get_size()
        self.zoom_percent = max(50, min(100, zoom_percent))
        self.panel = GamePanel(self.screen, self._board_area_width())
        self._layout_board()
        self.chess_set = ChessSet(self)
        self.game = GameController()
        self.status = self.game.status()
        self.selected_square: str | None = None
        self._pressed_square: str | None = None
        self.last_move: MoveRecord | None = None
        self.promotion: tuple[str, str] | None = None
        self.engines = {Side.WHITE: white_engine, Side.BLACK: black_engine}
        self.players = {
            side: engine.name if engine else "none"
            for side, engine in self.engines.items()
        }
        self.choices = tuple(
            dict.fromkeys(("none", *engine_names, *self.players.values()))
        )
        self.menu: dict[Side, str] | None = None
        self.running = True
        self.next_players: tuple[str, str] | None = None
        self.failure: str | None = None
        self._release_engines = release_engines
        self._worker = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="pychess-move"
        )
        self._pending: Future[MoveDecision] | None = None
        self._next_engine_tick = 0

    def _board_area_width(self) -> int:
        width = self.window_size[0]
        panel_width = min(352, max(256, width // 4), width // 2)
        return width - panel_width

    def _layout_board(self) -> None:
        self.board = BoardGeometry.from_screen(
            self._board_area_width(),
            self.window_size[1],
            margin=max(24, self.panel.small.get_height() + 1),
            zoom_percent=self.zoom_percent,
        )
        self.panel.zoom_percent = self.zoom_percent

    def _resize_window(self) -> None:
        self.screen = self.window.get_surface()
        if self.screen.get_size() != self.window_size:
            self.window_size = self.screen.get_size()
            self.panel.resize(self.screen, self._board_area_width())
            self._layout_board()
            self._pressed_square = None
            # Refresh the buttons before any queued click is handled.
            self._update_screen()

    def run_game(self) -> tuple[str, str] | None:
        """Run until the player quits or launches a new game."""
        try:
            self._update_screen()
            while self.running:
                received_events = self._check_events()
                if self.running:
                    engine_finished = self._maybe_play_engine_turn()
                    if received_events or engine_finished:
                        self._update_screen()
                    self.clock.tick(30)
            return self.next_players
        finally:
            self.close()

    def close(self) -> None:
        """Stop external search before joining the engine worker."""
        self.running = False
        self.window.destroy()
        pygame.quit()
        try:
            release, self._release_engines = self._release_engines, None
            if release is not None:
                release()
        finally:
            self._worker.shutdown(wait=True, cancel_futures=True)

    def _check_events(self) -> bool:
        events = pygame.event.get()
        for event in events:
            if event.type in (pygame.QUIT, pygame.WINDOWCLOSE):
                self.running = False
            elif event.type in (pygame.WINDOWRESIZED, pygame.WINDOWSIZECHANGED):
                self._resize_window()
            elif event.type == pygame.KEYDOWN:
                self._handle_key(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._pressed_square = None
                action = self.panel.action_at(event.pos)
                if action:
                    self._action(action)
                elif self.menu is None:
                    self._handle_left_click(event.pos)
                    self._pressed_square = self.selected_square
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                square = self.board.square_at(*event.pos)
                if (
                    self.menu is None
                    and square
                    and self._pressed_square
                    and self._pressed_square == self.selected_square
                    and square != self._pressed_square
                ):
                    self._handle_left_click(event.pos)
                self._pressed_square = None
            elif event.type == pygame.MOUSEWHEEL and self.menu is None:
                self.panel.scroll += event.y
            if not self.running:
                break
        return bool(events)

    def _handle_key(self, key: int) -> None:
        if key == pygame.K_q:
            self._action("quit")
        elif key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self._action("zoom_in")
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self._action("zoom_out")
        elif self.menu is not None:
            if key == pygame.K_RETURN:
                self._action("start")
            elif key in (pygame.K_ESCAPE, pygame.K_m):
                self._action("back")
        elif key == pygame.K_m:
            self._action("menu")
        elif key == pygame.K_r:
            self._action("restart")
        elif key == pygame.K_ESCAPE:
            self.promotion = None
            self.selected_square = None
        elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            self._action(tuple(PROMOTIONS)[key - pygame.K_1])

    def _action(self, action: str) -> None:
        if action == "quit":
            self.running = False
        elif action in ("zoom_in", "zoom_out"):
            step = 10 if action == "zoom_in" else -10
            self.zoom_percent = max(50, min(100, self.zoom_percent + step))
            self._layout_board()
            self._pressed_square = None
        elif action == "menu":
            self.menu = self.players.copy()
        elif action == "back":
            self.menu = None
        elif action in ("start", "restart"):
            players = self.menu if action == "start" else self.players
            if players:
                self.next_players = (players[Side.WHITE], players[Side.BLACK])
                self.running = False
        elif self.menu is not None and action in ("white", "black"):
            side = Side(action)
            index = self.choices.index(self.menu[side])
            self.menu[side] = self.choices[(index + 1) % len(self.choices)]
        elif action in PROMOTIONS and self.promotion is not None:
            self._record_move(self.game.push_between(*self.promotion, promotion=action))
            self.promotion = None

    def _handle_left_click(self, position: tuple[int, int]) -> None:
        if (
            self.engines[self.game.turn]
            or self.status.is_game_over
            or self.failure
            or self.promotion
        ):
            return
        square = self.board.square_at(*position)
        if square is None or square == self.selected_square:
            self.selected_square = None
            return
        piece = self.game.piece_at(square)
        if piece is not None and piece.color == self.game.turn:
            self.selected_square = square
            return
        if self.selected_square is not None:
            if self.selected_square + square + "q" in self.status.legal_moves:
                self.promotion = self.selected_square, square
                return
            try:
                self._record_move(self.game.push_between(self.selected_square, square))
            except IllegalMoveError:
                self.selected_square = None

    def _record_move(self, record: MoveRecord) -> None:
        self.last_move = record
        self.selected_square = None
        self.status = self.game.status()
        self.panel.scroll = 0

    def _maybe_play_engine_turn(self) -> bool:
        if self.menu is not None or self.status.is_game_over or self.failure:
            return False
        engine = self.engines[self.game.turn]
        if engine is None:
            return False
        if self._pending is None:
            if pygame.time.get_ticks() < self._next_engine_tick:
                return False
            context = EngineContext(
                fen=self.status.fen,
                turn=self.game.turn,
                legal_moves=self.status.legal_moves,
                move_history=self.game.move_history(),
            )
            self._pending = self._worker.submit(engine.choose_move, context)
        elif self._pending.done():
            future = self._pending
            self._pending = None
            try:
                decision = future.result()
                self._record_move(self.game.push_uci(decision.uci))
            except Exception as exc:
                message = str(exc)
                self.failure = (
                    message
                    if message.startswith(f"{engine.name}:")
                    else f"{engine.name}: {message}"
                )
                sys.stderr.write(self.failure + "\n")
            if all(self.engines.values()):
                self._next_engine_tick = pygame.time.get_ticks() + 250
            return True
        return False

    def _update_screen(self) -> None:
        self.screen.fill(BACKGROUND)
        for square in self.board.squares():
            color = LIGHT_SQUARE if square.is_light else DARK_SQUARE
            if self.last_move and square.name in (
                self.last_move.uci[:2],
                self.last_move.uci[2:4],
            ):
                color = LAST_MOVE_SQUARE
            if square.name == self.selected_square:
                color = SELECTED_SQUARE
            pygame.draw.rect(
                self.screen, color, (square.x, square.y, square.size, square.size)
            )
        for piece in self.game.pieces():
            square = self.board.square(piece.square)
            image = self.chess_set.scaled_image_for(
                piece.color.value, piece.piece_type, square.size
            )
            self.screen.blit(image, (square.x, square.y))
        if self.selected_square is not None:
            for target in set(self.game.legal_destinations_from(self.selected_square)):
                sq = self.board.square(target)
                center = (sq.x + sq.size // 2, sq.y + sq.size // 2)
                if self.game.piece_at(target) is None:
                    pygame.draw.circle(
                        self.screen, LEGAL_MOVE_DOT, center, max(2, sq.size // 10)
                    )
                else:
                    pygame.draw.circle(
                        self.screen,
                        LEGAL_MOVE_DOT,
                        center,
                        max(1, sq.size // 2 - 2),
                        max(1, sq.size // 22),
                    )
        for i, file_name in enumerate("abcdefgh"):
            sq = self.board.square(f"{file_name}1")
            file_label = self.panel.small.render(file_name, True, MUTED)
            self.screen.blit(
                file_label,
                file_label.get_rect(midtop=(sq.x + sq.size // 2, sq.y + sq.size + 1)),
            )
            rank = str(i + 1)
            sq = self.board.square(f"a{rank}")
            rank_label = self.panel.small.render(rank, True, MUTED)
            self.screen.blit(
                rank_label,
                rank_label.get_rect(midright=(sq.x - 5, sq.y + sq.size // 2)),
            )
        if self.menu is not None:
            self.panel.draw_menu(self.menu)
        else:
            self.panel.draw_play(
                self.players,
                self.status,
                self.game.move_history(),
                self.failure,
                self.promotion is not None,
            )
        self.window.flip()


def main(argv: list[str] | None = None) -> int:
    """Launch a local desktop game with human or configured engine players."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="JSON configuration file")
    parser.add_argument("--white-engine", help="White player (none = human)")
    parser.add_argument("--black-engine", help="Black player (none = human)")
    parser.add_argument("--seed", type=int)
    parser.add_argument(
        "--list-engines", action="store_true", help="List selectable engines"
    )
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        names = config.engine_names()
        if args.list_engines:
            sys.stdout.write("\n".join(names) + "\n")
            return 0
        players = (
            args.white_engine or config.play.white,
            args.black_engine or config.play.black,
        )
        seed = config.play.seed if args.seed is None else args.seed
        for player in players:
            if player != "none" and player not in names:
                parser.error(
                    f"Unknown engine {player!r}. Available: none, {', '.join(names)}"
                )
        window_size = None
        zoom_percent = 90
        while players:
            with ExitStack() as stack:
                white, black = (
                    None
                    if name == "none"
                    else stack.enter_context(config.open_engine(name, seed=seed + i))
                    for i, name in enumerate(players)
                )
                game = ChessGame(
                    white_engine=white,
                    black_engine=black,
                    engine_names=names,
                    release_engines=stack.close,
                    window_size=window_size,
                    zoom_percent=zoom_percent,
                )
                players = game.run_game()
                window_size, zoom_percent = game.window_size, game.zoom_percent
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
