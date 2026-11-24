"""Drive a local UCI process using python-chess's protocol implementation."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from time import perf_counter

import chess
import chess.engine

from pychess.engines.base import EngineContext, MoveDecision, NoLegalMovesError


class EngineFailure(RuntimeError):  # noqa: N818
    """A configured engine could not start or complete a move."""


class EngineTimeout(EngineFailure):
    """The UCI engine missed its response deadline."""


class EngineIllegalMove(EngineFailure):
    """The engine returned an invalid move while legal moves were available."""

    def __init__(self, name: str, move: str) -> None:
        super().__init__(f"{name} returned an illegal bestmove: {move}")
        self.move = move


@dataclass(frozen=True, slots=True)
class UciSpec:
    command: tuple[str, ...]
    cwd: Path
    options: dict[str, str | int | bool | None]
    move_time: float = 0.1
    timeout: float = 5.0
    nodes: int | None = None


class _UciProtocol(chess.engine.UciProtocol):
    """Remember the original token when python-chess rejects a bestmove."""

    bestmove: str = "(none)"

    def line_received(self, line: str) -> None:
        words = line.split(maxsplit=2)
        if words and words[0] == "bestmove":
            self.bestmove = words[1] if len(words) > 1 else "(none)"
        super().line_received(line)


class UciEngine:
    """One lazy UCI session per competitor per game."""

    def __init__(self, name: str, spec: UciSpec) -> None:
        self.name = name
        self.spec = spec
        self._runner = asyncio.Runner(loop_factory=asyncio.new_event_loop)
        self._transport: asyncio.SubprocessTransport | None = None
        self._protocol: _UciProtocol | None = None
        self._closed = False
        self._state_lock = Lock()
        self._move_lock = Lock()

    async def _play(self, board: chess.Board) -> str:
        if self._protocol is None:
            async with asyncio.timeout(self.spec.timeout):
                transport, protocol = await _UciProtocol.popen(
                    list(self.spec.command), cwd=self.spec.cwd
                )
                with self._state_lock:
                    self._transport, self._protocol = transport, protocol
                    if self._closed:
                        raise EngineFailure(f"{self.name}: session closed")
                await protocol.initialize()
                await protocol.configure(self.spec.options)
        limit = chess.engine.Limit(time=self.spec.move_time, nodes=self.spec.nodes)
        async with asyncio.timeout(self.spec.move_time + self.spec.timeout):
            try:
                result = await self._protocol.play(board, limit)
            except chess.engine.EngineError as exc:
                if exc.args and isinstance(
                    exc.args[0], (chess.InvalidMoveError, chess.IllegalMoveError)
                ):
                    raise EngineIllegalMove(self.name, self._protocol.bestmove) from exc
                raise
        return result.move.uci() if result.move is not None else "(none)"

    async def _stop(self, *, graceful: bool) -> None:
        if self._transport is None or self._protocol is None:
            return
        try:
            if graceful and not self._protocol.returncode.done():
                # Let an idle engine flush its state, with a bounded grace period.
                with suppress(TimeoutError, OSError, chess.engine.EngineError):
                    async with asyncio.timeout(min(self.spec.timeout, 0.5)):
                        await self._protocol.quit()
        finally:
            self._transport.close()
            await self._protocol.returncode

    def close(self, *, abort: bool = False) -> None:
        """Interrupt any search or handshake, then reap the process."""
        with self._state_lock:
            if self._closed:
                return
            self._closed = True
            busy = self._move_lock.locked()
            if (busy or abort) and self._transport is not None:
                # Signal the child directly. Its pipes wake the owning event loop.
                with suppress(ProcessLookupError):
                    self._transport.kill()
        with self._move_lock:
            try:
                if self._transport is not None:
                    self._runner.run(self._stop(graceful=not (busy or abort)))
            finally:
                self._runner.close()

    def _search(self, board: chess.Board) -> str:
        try:
            return self._runner.run(self._play(board))
        except TimeoutError as exc:
            raise EngineTimeout(f"{self.name}: UCI response timed out") from exc
        except (chess.engine.EngineError, OSError, ValueError) as exc:
            raise EngineFailure(f"{self.name}: {exc}") from exc

    def choose_move(self, context: EngineContext) -> MoveDecision:
        if not context.legal_moves:
            raise NoLegalMovesError(f"{self.name}: no legal moves")
        # Rebuild the stack as well as the FEN, so the engine sees repetitions.
        if context.move_history:
            board = chess.Board(context.move_history[0].fen_before)
            for record in context.move_history:
                board.push_uci(record.uci)
        else:
            board = chess.Board(context.fen)
        started = perf_counter()
        try:
            with self._move_lock:
                with self._state_lock:
                    if self._closed:
                        raise EngineFailure(f"{self.name}: session closed")
                move = self._search(board)
                if move not in context.legal_moves:
                    raise EngineIllegalMove(self.name, move)
        except EngineFailure:
            self.close(abort=True)
            raise
        return MoveDecision(uci=move, elapsed_seconds=perf_counter() - started)
