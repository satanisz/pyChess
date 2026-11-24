"""Replace score_moves with inference from your own model to play over UCI."""

import argparse
import json
from pathlib import Path

import chess

from pychess.engines import EngineContext
from pychess.models.uci import serve_scorer


class PositionalScorer:
    name = "Example positional model"

    def __init__(self, weights: dict[str, float]) -> None:
        self.weights = weights

    def score_moves(self, context: EngineContext) -> dict[str, float]:
        board = chess.Board(context.fen)
        scores = {}
        for uci in context.legal_moves:
            move = chess.Move.from_uci(uci)
            capture = board.is_capture(move)
            target = move.to_square
            center_distance = abs(chess.square_file(target) - 3.5) + abs(
                chess.square_rank(target) - 3.5
            )
            scores[uci] = (
                self.weights["capture"] * capture
                + self.weights["check"] * board.gives_check(move)
                - self.weights["center"] * center_distance
            )
        return scores


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("weights", type=Path)
    args = parser.parse_args()
    serve_scorer(PositionalScorer(json.loads(args.weights.read_text(encoding="utf-8"))))
