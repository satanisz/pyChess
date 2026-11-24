import json
import sys

import pytest

from pychess.config import load_config


def write_config(directory, data):
    path = directory / "engines.json"
    path.write_text(json.dumps(data))
    return path


def test_builtin_defaults_and_relative_profile_paths(tmp_path):
    defaults = load_config()
    assert defaults.play.white == defaults.play.black == "none"
    assert (defaults.arena.white, defaults.arena.black) == ("random", "heuristic")
    with defaults.open_engine("random", seed=42) as engine:
        assert engine.name == "random"

    data = {
        "engines": {
            "můj model": {"command": ["{python}", "example.py"]},
            "local": {"command": ["./my engine", "--flag"], "cwd": "weights"},
            "system": {"command": ["stockfish"]},
        },
        "play": {"black": "můj model", "seed": -2},
        "arena": {"participants": ["local", "system"], "database": "results/lab.db"},
    }
    cfg = load_config(write_config(tmp_path, data))
    assert cfg.play.black == "můj model"
    assert cfg.engines["můj model"].command == (sys.executable, "example.py")
    assert cfg.engines["můj model"].cwd == tmp_path
    assert cfg.engines["local"].command == (str(tmp_path / "my engine"), "--flag")
    assert cfg.engines["local"].cwd == tmp_path / "weights"
    assert cfg.engines["system"].command == ("stockfish",)
    assert cfg.arena.database == tmp_path / "results" / "lab.db"
    assert cfg.arena.participants == ("local", "system")
    assert "random" in cfg.engine_names()


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ({"typo": 2}, "unknown fields"),
        ({"engines": {"random": {}}}, "reserved"),
        ({"engines": {"test": {"command": "ls"}}}, "command"),
        ({"engines": {"test": {"command": ["x"], "nodes": True}}}, "nodes"),
        ({"engines": {"test": {"command": ["x"], "timeout": 0}}}, "timeout"),
        (
            {"engines": {"test": {"command": ["x"], "move_time": float("inf")}}},
            "move_time",
        ),
        (
            {"engines": {"test": {"command": ["x"], "misspelling": True}}},
            "unknown fields",
        ),
        (
            {"engines": {"test": {"command": ["x"], "options": {"Hash": []}}}},
            "options.Hash",
        ),
        ({"arena": {"games": 1.5}}, "games"),
        ({"arena": {"participants": ["heuristic", "heuristic"]}}, "participants"),
        ({"play": {"black": "unknown"}}, "unknown engine"),
        ({"arena": {"white": "none"}}, "unknown engine"),
    ],
)
def test_invalid_configuration_is_rejected_before_launch(tmp_path, data, message):
    with pytest.raises(ValueError, match=message):
        load_config(write_config(tmp_path, data))


def test_duplicate_keys_and_unreadable_file_show_path(tmp_path):
    path = tmp_path / "lab.json"
    with pytest.raises(ValueError, match=r"lab\.json"):
        load_config(path)
    path.write_text('{"play": {"white": "none", "white": "random"}}')
    with pytest.raises(ValueError, match="duplicate JSON key: white"):
        load_config(path)
