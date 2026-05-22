from __future__ import annotations

import chess
import pytest

from pychess.core import (
    GameAlreadyOverError,
    GameController,
    IllegalMoveError,
    MoveStackEmptyError,
    Side,
)


def play_fools_mate(game: GameController) -> None:
    game.push_uci("f2f3")
    game.push_uci("e7e5")
    game.push_uci("g2g4")
    game.push_uci("d8h4")


def test_new_game_exposes_starting_position() -> None:
    game = GameController()

    assert game.fen() == chess.STARTING_FEN
    assert game.turn == Side.WHITE
    assert len(game.legal_moves()) == 20
    assert "e2e4" in game.legal_moves()


def test_push_uci_records_state_and_undo_restores_position() -> None:
    game = GameController()
    starting_fen = game.fen()

    record = game.push_uci("e2e4")

    assert record.uci == "e2e4"
    assert record.san == "e4"
    assert record.side == Side.WHITE
    assert record.fullmove_number == 1
    assert record.fen_before == starting_fen
    assert record.fen_after == game.fen()
    assert game.turn == Side.BLACK

    undone = game.undo()

    assert undone == record
    assert game.fen() == starting_fen
    assert game.move_history() == ()


def test_push_san_applies_move() -> None:
    game = GameController()

    record = game.push_san("e4")

    assert record.uci == "e2e4"
    assert game.turn == Side.BLACK


def test_piece_at_and_legal_destinations_support_ui_input() -> None:
    game = GameController()

    piece = game.piece_at("e2")

    assert piece is not None
    assert piece.piece_type == "pawn"
    assert piece.color == Side.WHITE
    assert game.piece_at("e4") is None
    assert game.legal_destinations_from("e2") == ("e3", "e4")


def test_push_between_applies_mouse_style_move() -> None:
    game = GameController()

    record = game.push_between("e2", "e4")

    assert record.uci == "e2e4"
    assert record.san == "e4"


def test_push_between_promotes_to_queen_by_default() -> None:
    game = GameController.from_fen("8/P7/8/8/8/8/8/k6K w - - 0 1")

    record = game.push_between("a7", "a8")

    assert record.uci == "a7a8q"
    assert game.piece_at("a8").symbol == "Q"


def test_illegal_and_invalid_moves_are_rejected() -> None:
    game = GameController()

    assert not game.is_legal_uci("e2e5")
    assert not game.is_legal_uci("nope")

    with pytest.raises(IllegalMoveError):
        game.push_uci("e2e5")

    with pytest.raises(IllegalMoveError):
        game.push_uci("nope")


def test_undo_empty_stack_is_rejected() -> None:
    game = GameController()

    with pytest.raises(MoveStackEmptyError):
        game.undo()


def test_fen_roundtrip() -> None:
    fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"

    game = GameController.from_fen(fen)

    assert game.fen() == fen
    assert game.turn == Side.WHITE
    assert "g1f3" in game.legal_moves()


def test_piece_snapshot_is_serializable_for_ui_and_engines() -> None:
    game = GameController()

    pieces = game.pieces()

    assert len(pieces) == 32
    assert pieces[0].square == "a1"
    assert pieces[0].piece_type == "rook"
    assert pieces[0].color == Side.WHITE
    assert pieces[0].symbol == "R"


def test_checkmate_status_and_pgn_export() -> None:
    game = GameController()

    play_fools_mate(game)
    status = game.status()
    pgn = game.pgn({"Event": "Fool's Mate"})

    assert status.is_game_over
    assert status.is_check
    assert status.is_checkmate
    assert status.result == "0-1"
    assert '[Event "Fool\'s Mate"]' in pgn
    assert "1. f3 e5 2. g4 Qh4# 0-1" in pgn


def test_moves_after_terminal_result_are_rejected() -> None:
    game = GameController()
    play_fools_mate(game)

    with pytest.raises(GameAlreadyOverError):
        game.push_uci("a2a3")
