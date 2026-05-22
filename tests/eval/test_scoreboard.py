from pychess.arena import ArenaGameResult
from pychess.eval import MatchScore


def result(value: str, termination: str = "normal") -> ArenaGameResult:
    return ArenaGameResult(
        white="white",
        black="black",
        result=value,
        termination=termination,
        plies=0,
        moves=(),
        pgn="",
    )


def test_match_score_counts_results() -> None:
    score = MatchScore()

    score.add(result("1-0"))
    score.add(result("0-1", "illegal_move"))
    score.add(result("1/2-1/2"))
    score.add(result("*", "max_plies"))

    assert score.games == 4
    assert score.white_wins == 1
    assert score.black_wins == 1
    assert score.draws == 1
    assert score.unfinished == 1
    assert score.illegal_moves == 1


def test_match_score_summary_line() -> None:
    score = MatchScore(white_wins=1, black_wins=2, draws=3, unfinished=4)

    assert score.summary_line() == (
        "score: games=10, white=1, black=2, draw=3, unfinished=4, illegal=0"
    )
