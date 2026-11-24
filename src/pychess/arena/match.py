"""Run headless games between engines."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from pychess.core import GameController, IllegalMoveError, MoveRecord, Side
from pychess.engines import EngineContext, PlayerEngine
from pychess.engines.uci import EngineFailure, EngineIllegalMove, EngineTimeout


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
    error: str | None = None


def play_game(
    white: PlayerEngine,
    black: PlayerEngine,
    *,
    initial_fen: str | None = None,
    max_plies: int = 512,
) -> ArenaGameResult:
    """Play a headless game between two engines."""
    if max_plies < 1:
        raise ValueError("max_plies must be positive")
    game = (
        GameController()
        if initial_fen is None
        else GameController.from_fen(initial_fen)
    )
    engines = {Side.WHITE: white, Side.BLACK: black}

    for _ in range(max_plies):
        if game.status().is_game_over:
            break
        context = _context_from_game(game)
        engine = engines[game.turn]
        forfeit = "0-1" if game.turn == Side.WHITE else "1-0"
        try:
            decision = engine.choose_move(context)
        except EngineIllegalMove as exc:
            return _result_from_game(
                game, white, black, forfeit, "illegal_move", illegal_move=exc.move
            )
        except EngineTimeout as exc:
            return _result_from_game(
                game, white, black, forfeit, "timeout", error=str(exc)
            )
        except EngineFailure as exc:
            return _result_from_game(
                game, white, black, forfeit, "engine_error", error=str(exc)
            )
        try:
            game.push_uci(decision.uci)
        except IllegalMoveError:
            return _result_from_game(
                game, white, black, forfeit, "illegal_move", illegal_move=decision.uci
            )

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


def _result_from_game(
    game: GameController,
    white: PlayerEngine,
    black: PlayerEngine,
    result: str,
    termination: str,
    *,
    illegal_move: str | None = None,
    error: str | None = None,
) -> ArenaGameResult:
    headers = {
        "Event": "PyChess Arena",
        "Date": datetime.now(UTC).strftime("%Y.%m.%d"),
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
        error=error,
    )
