"""Score aggregation for arena results."""

from __future__ import annotations

from dataclasses import dataclass

from pychess.arena import ArenaGameResult


@dataclass(slots=True)
class MatchScore:
    """Aggregate results for a batch of arena games."""

    white_wins: int = 0
    black_wins: int = 0
    draws: int = 0
    unfinished: int = 0
    illegal_moves: int = 0

    @property
    def games(self) -> int:
        """Return total counted games."""
        return self.white_wins + self.black_wins + self.draws + self.unfinished

    def add(self, result: ArenaGameResult) -> None:
        """Add one arena result to the score."""
        if result.result == "1-0":
            self.white_wins += 1
        elif result.result == "0-1":
            self.black_wins += 1
        elif result.result == "1/2-1/2":
            self.draws += 1
        else:
            self.unfinished += 1

        if result.termination == "illegal_move":
            self.illegal_moves += 1

    def summary_line(self) -> str:
        """Return a compact text report."""
        return (
            "score: "
            f"games={self.games}, "
            f"white={self.white_wins}, "
            f"black={self.black_wins}, "
            f"draw={self.draws}, "
            f"unfinished={self.unfinished}, "
            f"illegal={self.illegal_moves}"
        )
