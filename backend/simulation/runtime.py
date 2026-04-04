from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Protocol, TypeAlias


class RuntimeLoopService(Protocol):
    def runtime_plan(self) -> tuple[bool, float]: ...

    def step_if_running(self) -> bool: ...


class ThreadLike(Protocol):
    def start(self) -> None: ...

    def join(self, timeout: float | None = None) -> None: ...

    def is_alive(self) -> bool: ...


ThreadFactory: TypeAlias = Callable[..., ThreadLike]


class SimulationRuntime:
    """Owns the background loop that advances the simulation over time."""

    def __init__(
        self,
        service: RuntimeLoopService,
        *,
        sleep_fn: Callable[[float], None] = time.sleep,
        monotonic_fn: Callable[[], float] = time.monotonic,
        thread_factory: ThreadFactory = threading.Thread,
    ) -> None:
        self.service = service
        self.sleep_fn = sleep_fn
        self.monotonic_fn = monotonic_fn
        self.thread_factory = thread_factory
        self._stop_event = threading.Event()
        self._thread: ThreadLike | None = None

    def start_background_loop(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        if self._stop_event.is_set():
            self._stop_event = threading.Event()

        self._thread = self.thread_factory(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop_background_loop(self, timeout: float = 1.0) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout)
        self._thread = None

    def run_once(self) -> float:
        should_step, delay = self.service.runtime_plan()
        if should_step:
            started_at = self.monotonic_fn()
            self.service.step_if_running()
            elapsed = self.monotonic_fn() - started_at
            return max(0.0, delay - elapsed)
        return delay

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            delay = self.run_once()
            self.sleep_fn(delay)
