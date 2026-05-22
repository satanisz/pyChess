"""Chess game, for learning to grab images from a sprite sheet."""

from __future__ import annotations

import argparse
import sys

import pygame

from pychess.chess_set import ChessSet
from pychess.core import GameController, IllegalMoveError, MoveRecord, Side
from pychess.engines import (
    EngineContext,
    PlayerEngine,
    available_engine_names,
    build_engine,
)
from pychess.settings import Settings
from pychess.ui import BoardGeometry

LIGHT_SQUARE = (238, 238, 210)
DARK_SQUARE = (118, 150, 86)
SELECTED_SQUARE = (186, 202, 68)
LAST_MOVE_SQUARE = (246, 246, 105)
LEGAL_MOVE_DOT = (35, 35, 35)


class ChessGame:
    """Overall class to manage game assets and behavior."""

    def __init__(
        self,
        *,
        white_engine: PlayerEngine | None = None,
        black_engine: PlayerEngine | None = None,
    ) -> None:
        """Initialize the game, and create resources."""
        pygame.init()
        self.settings = Settings()
        self.clock = pygame.time.Clock()

        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height)
        )
        pygame.display.set_caption("Chess")

        self.game = GameController()
        self.board = BoardGeometry.from_screen(
            self.settings.screen_width,
            self.settings.screen_height,
        )
        self.chess_set = ChessSet(self)
        self.selected_square: str | None = None
        self.last_move: MoveRecord | None = None
        self.engines = {
            Side.WHITE: white_engine,
            Side.BLACK: black_engine,
        }

    def run_game(self) -> None:
        """Start the main loop for the game."""
        while True:
            self._check_events()
            self._maybe_play_engine_turn()
            self._update_screen()
            self.clock.tick(60)

    def _check_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_left_click(event.pos)

    def _update_screen(self) -> None:
        self.screen.fill(self.settings.bg_color)
        self._draw_board()
        self._draw_highlights()
        self._draw_pieces()
        pygame.display.flip()

    def _handle_left_click(self, position: tuple[int, int]) -> None:
        if self.engines[self.game.turn] is not None:
            return

        square = self.board.square_at(*position)
        if square is None:
            self.selected_square = None
            return

        if self.selected_square is None:
            self._select_square(square)
            return

        if square == self.selected_square:
            self.selected_square = None
            return

        clicked_piece = self.game.piece_at(square)
        if clicked_piece is not None and clicked_piece.color == self.game.turn:
            self._select_square(square)
            return

        try:
            self.last_move = self.game.push_between(self.selected_square, square)
        except IllegalMoveError:
            self.selected_square = None
            return

        self.selected_square = None

    def _maybe_play_engine_turn(self) -> None:
        if self.game.status().is_game_over:
            return

        engine = self.engines[self.game.turn]
        if engine is None:
            return

        context = EngineContext(
            fen=self.game.fen(),
            turn=self.game.turn,
            legal_moves=self.game.legal_moves(),
            move_history=self.game.move_history(),
        )
        decision = engine.choose_move(context)
        if decision.uci not in context.legal_moves:
            return

        self.last_move = self.game.push_uci(decision.uci)
        self.selected_square = None

    def _select_square(self, square: str) -> None:
        piece = self.game.piece_at(square)
        if piece is not None and piece.color == self.game.turn:
            self.selected_square = square

    def _draw_board(self) -> None:
        for square in self.board.squares():
            color = LIGHT_SQUARE if square.is_light else DARK_SQUARE
            rect = pygame.Rect(square.x, square.y, square.size, square.size)
            pygame.draw.rect(self.screen, color, rect)

    def _draw_highlights(self) -> None:
        if self.last_move is not None:
            self._draw_square_fill(self.last_move.uci[:2], LAST_MOVE_SQUARE)
            self._draw_square_fill(self.last_move.uci[2:4], LAST_MOVE_SQUARE)

        if self.selected_square is None:
            return

        self._draw_square_fill(self.selected_square, SELECTED_SQUARE)
        for destination in self.game.legal_destinations_from(self.selected_square):
            square = self.board.square(destination)
            center = (square.x + square.size // 2, square.y + square.size // 2)
            radius = max(6, square.size // 8)
            pygame.draw.circle(self.screen, LEGAL_MOVE_DOT, center, radius)

    def _draw_square_fill(self, square_name: str, color: tuple[int, int, int]) -> None:
        square = self.board.square(square_name)
        rect = pygame.Rect(square.x, square.y, square.size, square.size)
        pygame.draw.rect(self.screen, color, rect)

    def _draw_pieces(self) -> None:
        for piece in self.game.pieces():
            square = self.board.square(piece.square)
            image = self.chess_set.scaled_image_for(
                piece.color.value,
                piece.piece_type,
                square.size,
            )
            self.screen.blit(image, (square.x, square.y))


def main(argv: list[str] | None = None) -> int:
    """Run the pygame demo."""
    parser = argparse.ArgumentParser(description="Run PyChess.")
    engine_choices = ("none", *available_engine_names())
    parser.add_argument("--white-engine", default="none", choices=engine_choices)
    parser.add_argument("--black-engine", default="none", choices=engine_choices)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args(argv)

    chess_game = ChessGame(
        white_engine=_build_optional_engine(args.white_engine, seed=args.seed),
        black_engine=_build_optional_engine(args.black_engine, seed=args.seed + 1),
    )
    chess_game.run_game()
    return 0


def _build_optional_engine(name: str, *, seed: int) -> PlayerEngine | None:
    if name == "none":
        return None
    return build_engine(name, seed=seed)


if __name__ == "__main__":
    raise SystemExit(main())
