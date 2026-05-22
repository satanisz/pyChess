"""Core chess game state and move validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

import chess
import chess.pgn


class Side(StrEnum):
    """Player side names used by the application."""

    WHITE = "white"
    BLACK = "black"

    @classmethod
    def from_chess_color(cls, color: chess.Color) -> Side:
        """Convert a python-chess color flag into a domain side."""
        return cls.WHITE if color == chess.WHITE else cls.BLACK


@dataclass(frozen=True, slots=True)
class PieceOnSquare:
    """A serializable piece snapshot for UI and engine inputs."""

    square: str
    piece_type: str
    color: Side
    symbol: str


@dataclass(frozen=True, slots=True)
class MoveRecord:
    """A move applied to a game, with before and after state."""

    uci: str
    san: str
    side: Side
    fullmove_number: int
    fen_before: str
    fen_after: str


@dataclass(frozen=True, slots=True)
class GameStatus:
    """Read-only status summary for UI, engines, and arena code."""

    fen: str
    turn: Side
    legal_moves: tuple[str, ...]
    is_check: bool
    is_checkmate: bool
    is_stalemate: bool
    is_insufficient_material: bool
    can_claim_draw: bool
    is_game_over: bool
    result: str | None


class IllegalMoveError(ValueError):
    """Raised when a requested move is invalid or illegal."""


class GameAlreadyOverError(RuntimeError):
    """Raised when trying to play a move after a terminal result."""


class MoveStackEmptyError(RuntimeError):
    """Raised when undo is requested without any applied move."""


class GameController:
    """Owns a chess game state and validates all moves."""

    def __init__(self, fen: str = chess.STARTING_FEN) -> None:
        self._board = chess.Board(fen)
        self._records: list[MoveRecord] = []

    @classmethod
    def from_fen(cls, fen: str) -> GameController:
        """Create a game from a FEN position."""
        return cls(fen)

    @property
    def turn(self) -> Side:
        """Return the side to move."""
        return Side.from_chess_color(self._board.turn)

    def board_copy(self) -> chess.Board:
        """Return a defensive copy of the current python-chess board."""
        return self._board.copy(stack=True)

    def fen(self) -> str:
        """Return the current FEN string."""
        return self._board.fen()

    def legal_moves(self) -> tuple[str, ...]:
        """Return legal moves in UCI notation."""
        return tuple(sorted(move.uci() for move in self._board.legal_moves))

    def legal_san_moves(self) -> tuple[str, ...]:
        """Return legal moves in SAN notation."""
        return tuple(sorted(self._board.san(move) for move in self._board.legal_moves))

    def pieces(self) -> tuple[PieceOnSquare, ...]:
        """Return a snapshot of pieces on the board."""
        return tuple(
            PieceOnSquare(
                square=chess.square_name(square),
                piece_type=chess.piece_name(piece.piece_type),
                color=Side.from_chess_color(piece.color),
                symbol=piece.symbol(),
            )
            for square, piece in sorted(self._board.piece_map().items())
        )

    def status(self, *, claim_draw: bool = True) -> GameStatus:
        """Return a read-only status summary."""
        result = self._board.result(claim_draw=claim_draw)
        return GameStatus(
            fen=self.fen(),
            turn=self.turn,
            legal_moves=self.legal_moves(),
            is_check=self._board.is_check(),
            is_checkmate=self._board.is_checkmate(),
            is_stalemate=self._board.is_stalemate(),
            is_insufficient_material=self._board.is_insufficient_material(),
            can_claim_draw=self._board.can_claim_draw(),
            is_game_over=self._board.is_game_over(claim_draw=claim_draw),
            result=None if result == "*" else result,
        )

    def move_history(self) -> tuple[MoveRecord, ...]:
        """Return the applied moves."""
        return tuple(self._records)

    def is_legal_uci(self, move_uci: str) -> bool:
        """Return whether a UCI move is legal in the current position."""
        try:
            move = chess.Move.from_uci(move_uci)
        except chess.InvalidMoveError:
            return False
        return move in self._board.legal_moves

    def push_uci(self, move_uci: str) -> MoveRecord:
        """Apply a legal UCI move and return its record."""
        try:
            move = chess.Move.from_uci(move_uci)
        except chess.InvalidMoveError as exc:
            msg = f"Invalid UCI move: {move_uci}"
            raise IllegalMoveError(msg) from exc
        return self._push_move(move)

    def push_san(self, move_san: str) -> MoveRecord:
        """Apply a legal SAN move and return its record."""
        try:
            move = self._board.parse_san(move_san)
        except ValueError as exc:
            msg = f"Invalid SAN move: {move_san}"
            raise IllegalMoveError(msg) from exc
        return self._push_move(move)

    def undo(self) -> MoveRecord:
        """Undo the last applied move and return the removed record."""
        if not self._records:
            msg = "Cannot undo because the move stack is empty."
            raise MoveStackEmptyError(msg)

        move = self._board.pop()
        record = self._records.pop()
        if move.uci() != record.uci:
            msg = "Board move stack and recorded move history are out of sync."
            raise RuntimeError(msg)
        return record

    def reset(self) -> None:
        """Reset the game to the standard starting position."""
        self._board.reset()
        self._records.clear()

    def pgn(self, headers: Mapping[str, str] | None = None) -> str:
        """Export the game as PGN."""
        game = chess.pgn.Game.from_board(self._board)
        if headers is not None:
            for key, value in headers.items():
                game.headers[key] = value
        game.headers["Result"] = self._board.result(claim_draw=False)

        exporter = chess.pgn.StringExporter(
            headers=True,
            variations=False,
            comments=False,
            columns=None,
        )
        return game.accept(exporter)

    def _push_move(self, move: chess.Move) -> MoveRecord:
        if self._board.is_game_over(claim_draw=False):
            msg = f"Cannot play {move.uci()} because the game is already over."
            raise GameAlreadyOverError(msg)

        if move not in self._board.legal_moves:
            msg = f"Illegal move in current position: {move.uci()}"
            raise IllegalMoveError(msg)

        fen_before = self.fen()
        side = self.turn
        fullmove_number = self._board.fullmove_number
        san = self._board.san(move)

        self._board.push(move)
        record = MoveRecord(
            uci=move.uci(),
            san=san,
            side=side,
            fullmove_number=fullmove_number,
            fen_before=fen_before,
            fen_after=self.fen(),
        )
        self._records.append(record)
        return record
