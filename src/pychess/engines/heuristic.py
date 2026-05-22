"""Simple deterministic heuristic chess engine."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import chess

from pychess.engines.base import EngineContext, MoveDecision, NoLegalMovesError

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

CENTER_SQUARES = {
    chess.D4,
    chess.E4,
    chess.D5,
    chess.E5,
}


@dataclass(frozen=True, slots=True)
class ScoredMove:
    """Internal move score."""

    uci: str
    score: int


class HeuristicEngine:
    """Choose the best move according to a small static evaluation."""

    name = "heuristic"

    def choose_move(self, context: EngineContext) -> MoveDecision:
        """Choose the highest-scoring legal move."""
        if not context.legal_moves:
            msg = "HeuristicEngine cannot move without legal moves."
            raise NoLegalMovesError(msg)

        start = perf_counter()
        board = chess.Board(context.fen)
        scored_moves = [
            self._score_move(board, chess.Move.from_uci(move_uci))
            for move_uci in context.legal_moves
        ]
        best = max(scored_moves, key=lambda move: (move.score, move.uci))
        return MoveDecision(
            uci=best.uci,
            confidence=_confidence(best.score, scored_moves),
            elapsed_seconds=perf_counter() - start,
            reason=f"static evaluation score {best.score}",
        )

    def _score_move(self, board: chess.Board, move: chess.Move) -> ScoredMove:
        moving_color = board.turn
        captured_piece = board.piece_at(move.to_square)
        candidate = board.copy(stack=False)
        candidate.push(move)

        score = _material_score(candidate, moving_color)
        if captured_piece is not None:
            score += PIECE_VALUES[captured_piece.piece_type] // 10
        if move.to_square in CENTER_SQUARES:
            score += 15
        if candidate.is_checkmate():
            score += 100_000
        elif candidate.is_check():
            score += 75

        return ScoredMove(uci=move.uci(), score=score)


def _material_score(board: chess.Board, color: chess.Color) -> int:
    score = 0
    for piece in board.piece_map().values():
        value = PIECE_VALUES[piece.piece_type]
        score += value if piece.color == color else -value
    return score


def _confidence(best_score: int, scored_moves: list[ScoredMove]) -> float:
    if len(scored_moves) == 1:
        return 1.0

    worst_score = min(move.score for move in scored_moves)
    if best_score == worst_score:
        return 1 / len(scored_moves)

    return (best_score - worst_score) / max(1, abs(best_score) + abs(worst_score))
