import json
import os
from concurrent.futures import ThreadPoolExecutor
from os import getpid
from time import monotonic, sleep

import pytest

from pychess.config import load_config
from pychess.core import GameController
from pychess.engines import EngineContext
from pychess.engines.uci import EngineFailure, EngineIllegalMove, EngineTimeout

# Small independent UCI peer. Its log verifies the actual bytes sent to a process.
PEER = """
import os, sys
from pathlib import Path

mode = sys.argv[1]
Path("pid").write_text(str(os.getpid()))
with Path("commands").open("w", buffering=1) as log:
    for line in sys.stdin:
        line = line.strip()
        print(line, file=log)
        if line == "uci" and mode != "stall_start":
            print("id name TestPeer")
            print("option name Hash type spin default 1 min 1 max 128")
            print("uciok", flush=True)
        elif line == "isready":
            print("readyok", flush=True)
        elif line.startswith("go") and mode != "stall_move":
            if mode == "crash":
                sys.exit(4)
            print("bestmove", mode, flush=True)
        elif line == "quit":
            break
"""


def peer_config(directory, mode, **kwargs):
    path = directory / "lab.json"
    (directory / "my engine.py").write_text(PEER)
    spec = {
        "command": ["{python}", "my engine.py", mode],
        "options": {"Hash": 4},
        "move_time": 0.02,
        "nodes": 1,
        **kwargs,
    }
    path.write_text(json.dumps({"engines": {"custom": spec}}))
    return load_config(path)


def context(game):
    return EngineContext(game.fen(), game.turn, game.legal_moves(), game.move_history())


def assert_reaped(directory):
    if os.name == "posix":
        pid = int((directory / "pid").read_text())
        assert pid != getpid()
        deadline = monotonic() + 3
        while monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            sleep(0.01)
        pytest.fail("external engine remained alive")


def test_uci_sends_options_search_limit_and_full_history(tmp_path):
    cfg = peer_config(tmp_path, "g1f3")
    game = GameController()
    game.push_uci("e2e4")
    game.push_uci("e7e5")
    with cfg.open_engine("custom") as engine:
        assert not (tmp_path / "pid").exists()
        move = engine.choose_move(context(game))
        assert move.uci == "g1f3"
    lines = (tmp_path / "commands").read_text().splitlines()
    assert "setoption name Hash value 4" in lines
    assert "position startpos moves e2e4 e7e5" in lines
    go = next(line for line in lines if line.startswith("go "))
    assert "nodes 1" in go and "movetime 20" in go
    assert lines[-1] == "quit"
    assert_reaped(tmp_path)


def test_uci_preserves_nonstandard_start_position(tmp_path):
    cfg = peer_config(tmp_path, "e8f8")
    game = GameController("4k3/8/8/8/8/8/3P4/4K3 w - - 0 7")
    start = game.fen()
    game.push_uci("d2d3")
    with cfg.open_engine("custom") as engine:
        assert engine.choose_move(context(game)).uci == "e8f8"
    assert f"position fen {start} moves d2d3" in (tmp_path / "commands").read_text()


@pytest.mark.parametrize("mode", ["stall_start", "stall_move"])
def test_engine_timeout_reaps_unresponsive_process(tmp_path, mode):
    cfg = peer_config(tmp_path, mode, timeout=0.4)
    with cfg.open_engine("custom") as engine:
        with pytest.raises(EngineTimeout):
            engine.choose_move(context(GameController()))
        assert_reaped(tmp_path)
        with pytest.raises(EngineFailure, match="session closed"):
            engine.choose_move(context(GameController()))


@pytest.mark.parametrize("mode,signal", [("stall_start", "uci"), ("stall_move", "go ")])
def test_close_from_another_thread_interrupts_engine(tmp_path, mode, signal):
    cfg = peer_config(tmp_path, mode, timeout=15)
    with ThreadPoolExecutor(max_workers=1) as worker:
        with cfg.open_engine("custom") as engine:
            pending = worker.submit(engine.choose_move, context(GameController()))
            log = tmp_path / "commands"
            deadline = monotonic() + 3
            while not (log.exists() and signal in log.read_text()):
                assert monotonic() < deadline
                sleep(0.01)
        with pytest.raises(EngineFailure):
            pending.result(timeout=3)
    assert_reaped(tmp_path)


@pytest.mark.parametrize("move", ["e2e5", "junk", "(none)", "0000"])
def test_illegal_move_is_reported_verbatim(tmp_path, move):
    cfg = peer_config(tmp_path, move)
    with (
        cfg.open_engine("custom") as engine,
        pytest.raises(EngineIllegalMove) as caught,
    ):
        engine.choose_move(context(GameController()))
    assert caught.value.move == move
    assert_reaped(tmp_path)


def test_missing_program_and_unsupported_option_are_failures(tmp_path):
    for kwargs in ({"command": ["./missing binary"]}, {"options": {"Unknown": 1}}):
        cfg = peer_config(tmp_path, "e2e4", **kwargs)
        with (
            cfg.open_engine("custom") as engine,
            pytest.raises(EngineFailure, match="custom"),
        ):
            engine.choose_move(context(GameController()))


def test_terminated_engine_is_reported(tmp_path):
    cfg = peer_config(tmp_path, "crash")
    with (
        cfg.open_engine("custom") as engine,
        pytest.raises(EngineFailure, match="custom"),
    ):
        engine.choose_move(context(GameController()))
    assert_reaped(tmp_path)
