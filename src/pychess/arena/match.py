"""Run headless games between engines."""

from __future__ import annotations

from dataclasses import dataclass

from pychess.core import GameController, IllegalMoveError, MoveRecord, Side
from pychess.engines import EngineContext, PlayerEngine


@dataclass(frozen=True, slots=True)
class ArenaGameResult:
    """Result of one headless arena game."""

    white: str
    black: str
    result: str
    termination: str
    plies: int
    moves: tuple[MoveRecord, ...]
    pgn: str
    illegal_move: str | None = None


def play_game(
    white: PlayerEngine,
    black: PlayerEngine,
    *,
    initial_fen: str | None = None,
    max_plies: int = 512,
) -> ArenaGameResult:
    """Play a headless game between two engines."""
    game = (
        GameController()
        if initial_fen is None
        else GameController.from_fen(initial_fen)
    )
    engines = {Side.WHITE: white, Side.BLACK: black}

    while not game.status().is_game_over and len(game.move_history()) < max_plies:
        context = _context_from_game(game)
        engine = engines[game.turn]
        decision = engine.choose_move(context)

        if decision.uci not in context.legal_moves:
            return _illegal_move_result(game, white, black, decision.uci)

        try:
            game.push_uci(decision.uci)
        except IllegalMoveError:
            return _illegal_move_result(game, white, black, decision.uci)

    status = game.status()
    termination = "normal" if status.is_game_over else "max_plies"
    return _result_from_game(game, white, black, status.result or "*", termination)


def _context_from_game(game: GameController) -> EngineContext:
    return EngineContext(
        fen=game.fen(),
        turn=game.turn,
        legal_moves=game.legal_moves(),
        move_history=game.move_history(),
    )


def _illegal_move_result(
    game: GameController,
    white: PlayerEngine,
    black: PlayerEngine,
    illegal_move: str,
) -> ArenaGameResult:
    result = "0-1" if game.turn == Side.WHITE else "1-0"
    return _result_from_game(
        game,
        white,
        black,
        result,
        "illegal_move",
        illegal_move=illegal_move,
    )


def _result_from_game(
    game: GameController,
    white: PlayerEngine,
    black: PlayerEngine,
    result: str,
    termination: str,
    *,
    illegal_move: str | None = None,
) -> ArenaGameResult:
    headers = {
        "Event": "PyChess Arena",
        "White": white.name,
        "Black": black.name,
        "Result": result,
        "Termination": termination,
    }
    return ArenaGameResult(
        white=white.name,
        black=black.name,
        result=result,
        termination=termination,
        plies=len(game.move_history()),
        moves=game.move_history(),
        pgn=game.pgn(headers),
        illegal_move=illegal_move,
    )
