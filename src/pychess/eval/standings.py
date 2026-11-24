"""Local standings computed in game order, starting every engine at 1500 Elo."""

from __future__ import annotations

from dataclasses import dataclass, field

INITIAL_ELO = 1500.0


@dataclass(slots=True)
class PlayerScore:
    name: str
    wins: int = 0
    draws: int = 0
    losses: int = 0
    unfinished: int = 0
    self_play: int = 0
    elo: float = INITIAL_ELO

    @property
    def points(self) -> float:
        return self.wins + self.draws / 2

    @property
    def rated_games(self) -> int:
        return self.wins + self.draws + self.losses


@dataclass(slots=True)
class Standings:
    players: dict[str, PlayerScore] = field(default_factory=dict)

    def record(self, white: str, black: str, result: str) -> None:
        first = self.players.setdefault(white, PlayerScore(white))
        second = self.players.setdefault(black, PlayerScore(black))
        if white == black:
            first.self_play += 1
            return
        if result == "*":
            first.unfinished += 1
            second.unfinished += 1
            return
        if result == "1-0":
            first.wins += 1
            second.losses += 1
            score = 1.0
        elif result == "0-1":
            second.wins += 1
            first.losses += 1
            score = 0.0
        elif result == "1/2-1/2":
            first.draws += 1
            second.draws += 1
            score = 0.5
        else:
            raise ValueError(f"Unknown game result: {result}")

        expected = 1 / (1 + 10 ** ((second.elo - first.elo) / 400))
        change = 32 * (score - expected)
        first.elo += change
        second.elo -= change

    def ranked_by_elo(self) -> list[PlayerScore]:
        return sorted(
            self.players.values(), key=lambda p: (not p.rated_games, -p.elo, p.name)
        )

    def table(self, *, by_elo: bool = False) -> str:
        rows = ["engine\tW\tD\tL\tunfinished\tself-play\tpoints\tlocal Elo"]
        if by_elo:
            ranked = self.ranked_by_elo()
        else:
            ranked = sorted(
                self.players.values(), key=lambda p: (-p.points, -p.elo, p.name)
            )
        for player in ranked:
            rating = str(round(player.elo)) if player.rated_games else "-"
            rows.append(
                f"{player.name}\t{player.wins}\t{player.draws}\t{player.losses}\t"
                f"{player.unfinished}\t{player.self_play}\t{player.points:g}\t{rating}"
            )
        return "\n".join(rows)
