"""Reconstruct each player's rating and league place after each appearance."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from pychess.eval.standings import INITIAL_ELO, Standings


@dataclass(frozen=True, slots=True)
class GameRating:
    """Result uses PGN notation. Rank is absent until a player's first rated game."""

    game_id: int
    player_game: int
    player: str
    opponent: str
    color: str
    result: str
    termination: str
    elo_before: float
    elo_after: float
    rank_after: int | None


def archive_history(connection: sqlite3.Connection) -> list[GameRating]:
    """Replay the entire league in archive order, keeping full Elo precision."""
    standings = Standings()
    history: list[GameRating] = []
    games = connection.execute(
        "SELECT id, white, black, result, termination FROM games ORDER BY id"
    )
    for game_id, white, black, result, termination in games:
        before = {
            name: standings.players[name].elo
            for name in (white, black)
            if name in standings.players
        }
        standings.record(white, black, result)
        ranks = {
            player.name: place
            for place, player in enumerate(standings.ranked_by_elo(), start=1)
            if player.rated_games
        }
        if white == black:
            appearances = [(white, black, "self")]
        else:
            appearances = [(white, black, "white"), (black, white, "black")]
        for name, opponent, color in appearances:
            score = standings.players[name]
            history.append(
                GameRating(
                    game_id=game_id,
                    player_game=score.rated_games + score.unfinished + score.self_play,
                    player=name,
                    opponent=opponent,
                    color=color,
                    result=result,
                    termination=termination,
                    elo_before=before.get(name, INITIAL_ELO),
                    elo_after=score.elo,
                    rank_after=ranks.get(name),
                )
            )
    return history
