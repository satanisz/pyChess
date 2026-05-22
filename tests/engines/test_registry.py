import pytest

from pychess.engines import (
    HeuristicEngine,
    RandomEngine,
    available_engine_names,
    build_engine,
)


def test_registry_builds_known_engines() -> None:
    assert available_engine_names() == ("heuristic", "random")
    assert isinstance(build_engine("heuristic"), HeuristicEngine)
    assert isinstance(build_engine("random", seed=1), RandomEngine)


def test_registry_rejects_unknown_engine() -> None:
    with pytest.raises(ValueError):
        build_engine("missing")
