"""Run a single-pass Python move scorer as a UCI player for local matches."""

from __future__ import annotations

import sys
from typing import TextIO

from pychess.core import GameController
from pychess.engines import EngineContext
from pychess.models.neural_engine import MoveScorer, NeuralEngine


def _position(tokens: list[str]) -> GameController:
    if "moves" in tokens:
        index = tokens.index("moves")
        setup, moves = tokens[:index], tokens[index + 1 :]
    else:
        setup, moves = tokens, []
    if setup == ["startpos"]:
        game = GameController()
    elif len(setup) == 7 and setup[0] == "fen":
        game = GameController.from_fen(" ".join(setup[1:]))
    else:
        raise ValueError("Expected 'position startpos' or 'position fen <FEN>'")
    for move in moves:
        game.push_uci(move)
    return game


def serve_scorer(
    scorer: MoveScorer, *, stdin: TextIO | None = None, stdout: TextIO | None = None
) -> None:
    """Serve one inference per move; load model weights before calling this function."""
    incoming = sys.stdin if stdin is None else stdin
    outgoing = sys.stdout if stdout is None else stdout
    engine = NeuralEngine(scorer)
    game = GameController()
    for line in incoming:
        tokens = line.split()
        if not tokens:
            continue
        command, *args = tokens
        if command == "uci":
            outgoing.write(f"id name {scorer.name}\nuciok\n")
        elif command == "isready":
            outgoing.write("readyok\n")
        elif command == "ucinewgame":
            game = GameController()
        elif command == "position":
            game = _position(args)
        elif command == "go":
            moves = game.legal_moves()
            if "searchmoves" in args:
                allowed = set(args[args.index("searchmoves") + 1 :])
                moves = tuple(m for m in moves if m in allowed)
            budget = None
            if "movetime" in args:
                budget = int(args[args.index("movetime") + 1]) / 1000
            context = EngineContext(
                game.fen(), game.turn, moves, game.move_history(), time_left=budget
            )
            best = engine.choose_move(context).uci if moves else "0000"
            outgoing.write(f"bestmove {best}\n")
        elif command == "quit":
            break
        outgoing.flush()
