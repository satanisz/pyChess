from io import StringIO
from pathlib import Path

from pychess.config import load_config
from pychess.core import GameController
from pychess.engines import EngineContext
from pychess.models.uci import serve_scorer


def test_example_python_model_runs_using_paths_from_the_config(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[2] / "config" / "local.json"
    monkeypatch.chdir(tmp_path)
    game = GameController()
    game.push_uci("e2e4")
    context = EngineContext(
        game.fen(), game.turn, game.legal_moves(), game.move_history()
    )
    with load_config(path).open_engine("my-model") as engine:
        assert engine.choose_move(context).uci in context.legal_moves


def test_scorer_receives_history_clock_and_candidate_moves():
    class Scorer:
        name = "local scorer"

        def score_moves(self, context: EngineContext) -> dict[str, float]:
            assert context.time_left == 0.25
            assert context.move_history[0].uci == "e2e4"
            assert context.legal_moves == ("c7c5", "e7e5")
            return {"e7e5": 2, "e1e8": 100}

    incoming = StringIO(
        "uci\nisready\nposition startpos moves e2e4\n"
        "go movetime 250 searchmoves e7e5 c7c5\nquit\n"
    )
    output = StringIO()
    serve_scorer(Scorer(), stdin=incoming, stdout=output)
    assert output.getvalue().splitlines() == [
        "id name local scorer",
        "uciok",
        "readyok",
        "bestmove e7e5",
    ]
