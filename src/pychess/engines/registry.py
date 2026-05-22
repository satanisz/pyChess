"""Engine factory registry."""

from __future__ import annotations

from random import Random

from pychess.engines.base import PlayerEngine
from pychess.engines.heuristic import HeuristicEngine
from pychess.engines.random_engine import RandomEngine


def available_engine_names() -> tuple[str, ...]:
    """Return names of engines that can be built from configuration."""
    return ("heuristic", "random")


def build_engine(name: str, *, seed: int = 1) -> PlayerEngine:
    """Build an engine by registry name."""
    if name == "heuristic":
        return HeuristicEngine()
    if name == "random":
        return RandomEngine(Random(seed))

    msg = f"Unknown engine: {name}"
    raise ValueError(msg)
