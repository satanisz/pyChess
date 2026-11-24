"""Read engine profiles and game settings from a local JSON file."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from pychess.engines import PlayerEngine, available_engine_names, build_engine
from pychess.engines.uci import UciEngine, UciSpec


@dataclass(frozen=True, slots=True)
class PlayConfig:
    white: str = "none"
    black: str = "none"
    seed: int = 1


@dataclass(frozen=True, slots=True)
class ArenaConfig:
    white: str = "random"
    black: str = "heuristic"
    games: int = 1
    max_plies: int = 512
    seed: int = 1
    participants: tuple[str, ...] = ()
    database: Path | None = None


@dataclass(frozen=True, slots=True)
class AppConfig:
    engines: dict[str, UciSpec]
    play: PlayConfig
    arena: ArenaConfig

    def engine_names(self) -> tuple[str, ...]:
        return (*available_engine_names(), *self.engines)

    @contextmanager
    def open_engine(self, name: str, *, seed: int = 1) -> Iterator[PlayerEngine]:
        if name in self.engines:
            engine = UciEngine(name, self.engines[name])
            try:
                yield engine
            finally:
                engine.close()
        else:
            yield build_engine(name, seed=seed)


def _object(value: object, field: str, keys: set[str] | None = None) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a JSON object")
    if keys is not None and (unknown := value.keys() - keys):
        raise ValueError(
            f"{field} contains unknown fields: {', '.join(sorted(unknown))}"
        )
    return value


def _text(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or any(c in value for c in ("\x00", "\r", "\n"))
    ):
        raise ValueError(f"{field} must be a non-empty single-line string")
    return value


def _integer(value: object, field: str, *, positive: bool = False) -> int:
    if type(value) is not int or (positive and value < 1):
        expected = "a positive integer" if positive else "an integer"
        raise ValueError(f"{field} must be {expected}")
    return value


def _seconds(value: object, field: str) -> float:
    if type(value) not in (float, int) or not 0 < value <= sys.float_info.max:
        raise ValueError(f"{field} must be a positive finite number of seconds")
    return float(value)


def _engine_spec(raw: object, name: str, base: Path) -> UciSpec:
    field = f"engines.{name}"
    data = _object(
        raw,
        field,
        {"type", "command", "cwd", "options", "move_time", "timeout", "nodes"},
    )
    if data.get("type", "uci") != "uci":
        raise ValueError(f"{field}.type must be 'uci'")
    command = data.get("command")
    if not isinstance(command, list) or not command:
        raise ValueError(f"{field}.command must be a non-empty array of arguments")
    argv = [
        sys.executable if arg == "{python}" else _text(arg, f"{field}.command")
        for arg in command
    ]
    # An explicit path is relative to the configuration. Bare names use PATH.
    if "/" in argv[0] or os.sep in argv[0] or argv[0].startswith("~"):
        # Preserve virtual-environment interpreter symlinks.
        argv[0] = str(base / Path(argv[0]).expanduser())
    cwd = (
        base / Path(_text(data.get("cwd", "."), f"{field}.cwd")).expanduser()
    ).resolve()
    options = _object(data.get("options", {}), f"{field}.options")
    for key, value in options.items():
        _text(key, f"{field}.options name")
        if value is not None and not isinstance(value, (str, bool, int)):
            raise ValueError(
                f"{field}.options.{key} must be a string, integer, boolean or null"
            )
        if isinstance(value, str) and any(c in value for c in ("\x00", "\r", "\n")):
            raise ValueError(f"{field}.options.{key} must fit on a single UCI line")
    return UciSpec(
        command=tuple(argv),
        cwd=cwd,
        options=options,
        move_time=_seconds(data.get("move_time", 0.1), f"{field}.move_time"),
        timeout=_seconds(data.get("timeout", 5), f"{field}.timeout"),
        nodes=_integer(data["nodes"], f"{field}.nodes", positive=True)
        if "nodes" in data
        else None,
    )


def _read_json(path: Path) -> dict:
    def unique_keys(pairs: list[tuple[str, object]]) -> dict:
        data = {}
        for key, value in pairs:
            if key in data:
                raise ValueError(f"duplicate JSON key: {key}")
            data[key] = value
        return data

    try:
        return _object(
            json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys),
            "configuration",
            {"engines", "play", "arena"},
        )
    except (OSError, ValueError) as exc:
        raise ValueError(f"{path}: {exc}") from exc


def load_config(path: Path | str | None = None) -> AppConfig:
    """Load profiles without launching processes or requiring installed engines."""
    if path is None:
        return AppConfig({}, PlayConfig(), ArenaConfig())
    path = Path(path).expanduser().resolve()
    data = _read_json(path)
    engines = {}
    builtins = available_engine_names()
    for name, spec in _object(data.get("engines", {}), "engines").items():
        _text(name, "engine name")
        if name in (*builtins, "none"):
            raise ValueError(f"engine name '{name}' is reserved")
        engines[name] = _engine_spec(spec, name, path.parent)

    def player(name: object, field: str, *, human: bool = False) -> str:
        name = _text(name, field)
        if (
            name not in engines
            and name not in builtins
            and not (human and name == "none")
        ):
            raise ValueError(f"{field}: unknown engine '{name}'")
        return name

    play_data = _object(data.get("play", {}), "play", {"white", "black", "seed"})
    play = PlayConfig(
        white=player(play_data.get("white", "none"), "play.white", human=True),
        black=player(play_data.get("black", "none"), "play.black", human=True),
        seed=_integer(play_data.get("seed", 1), "play.seed"),
    )
    arena_data = _object(
        data.get("arena", {}),
        "arena",
        {
            "white",
            "black",
            "seed",
            "games",
            "max_plies",
            "database",
            "participants",
        },
    )
    lineup = arena_data.get("participants", [])
    if not isinstance(lineup, list):
        raise ValueError("arena.participants must be an array of engine names")
    participants = tuple(player(name, "arena.participants") for name in lineup)
    if participants and (
        len(participants) < 2 or len(set(participants)) != len(participants)
    ):
        raise ValueError(
            "arena.participants requires at least two engines and no duplicates"
        )
    database = arena_data.get("database")
    arena = ArenaConfig(
        white=player(arena_data.get("white", "random"), "arena.white"),
        black=player(arena_data.get("black", "heuristic"), "arena.black"),
        games=_integer(arena_data.get("games", 1), "arena.games", positive=True),
        max_plies=_integer(
            arena_data.get("max_plies", 512), "arena.max_plies", positive=True
        ),
        seed=_integer(arena_data.get("seed", 1), "arena.seed"),
        participants=participants,
        database=None
        if database is None
        else (
            path.parent / Path(_text(database, "arena.database")).expanduser()
        ).resolve(),
    )
    return AppConfig(engines, play, arena)
