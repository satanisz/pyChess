from pychess.arena.archive import archive_standings, open_archive
from pychess.arena.history import GameRating, archive_history

INSERT_GAME = """
    INSERT INTO games
    (id, white, black, result, termination, seed, max_plies, plies, pgn)
    VALUES (?, ?, ?, ?, ?, '1', 512, 0, '')
"""


def test_history_uses_game_order_opponents_and_full_league_ranks(tmp_path):
    path = tmp_path / "league.db"
    with open_archive(path) as db, db:
        db.executemany(
            INSERT_GAME,
            [
                (9, "alpha", "gamma", "1/2-1/2", "normal"),
                (2, "beta", "alpha", "1/2-1/2", "normal"),
                (6, "gamma", "beta", "1-0", "timeout"),
            ],
        )
    with open_archive(path, read_only=True) as db:
        history = archive_history(db)
        final_scores = archive_standings(db)

    assert [row.game_id for row in history] == [2, 2, 6, 6, 9, 9]
    assert history[:4] == [
        GameRating(2, 1, "beta", "alpha", "white", "1/2-1/2", "normal", 1500, 1500, 2),
        GameRating(2, 1, "alpha", "beta", "black", "1/2-1/2", "normal", 1500, 1500, 1),
        GameRating(6, 1, "gamma", "beta", "white", "1-0", "timeout", 1500, 1516, 1),
        GameRating(6, 2, "beta", "gamma", "black", "1-0", "timeout", 1500, 1484, 3),
    ]
    alpha, gamma = history[-2:]
    assert (alpha.player_game, alpha.rank_after, alpha.elo_before) == (2, 2, 1500)
    assert (gamma.player_game, gamma.rank_after, gamma.elo_before) == (2, 1, 1516)
    assert 1500 < alpha.elo_after < 1501
    for name, score in final_scores.players.items():
        latest = next(row for row in reversed(history) if row.player == name)
        assert latest.elo_after == score.elo


def test_unfinished_games_and_self_play_count_once_and_preserve_rating(tmp_path):
    with open_archive(tmp_path / "league.db") as db:
        assert archive_history(db) == []
        db.executemany(
            INSERT_GAME,
            [
                (1, "a", "a", "1-0", "normal"),
                (2, "a", "b", "*", "max_plies"),
                (3, "a", "b", "1-0", "normal"),
                (4, "a", "a", "0-1", "normal"),
            ],
        )
        rows = [row for row in archive_history(db) if row.player == "a"]

    assert [row.color for row in rows] == ["self", "white", "white", "self"]
    assert [row.player_game for row in rows] == [1, 2, 3, 4]
    assert [row.rank_after for row in rows] == [None, None, 1, 1]
    assert [row.elo_before for row in rows] == [1500, 1500, 1500, 1516]
    assert [row.elo_after for row in rows] == [1500, 1500, 1516, 1516]
