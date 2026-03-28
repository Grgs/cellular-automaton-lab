from __future__ import annotations

import threading
from collections.abc import Callable


class PersistenceCoordinator:
    def __init__(
        self,
        persist_fn: Callable[[], None],
        *,
        debounce_ms: int = 100,
        timer_factory=None,
    ) -> None:
        self._persist_fn = persist_fn
        self._debounce_seconds = max(0.0, debounce_ms / 1000.0)
        self._timer_factory = timer_factory or self._default_timer_factory
        self._lock = threading.Lock()
        self._timer = None
        self._dirty = False
        self._token = 0

    def _default_timer_factory(self, delay_seconds, callback):
        timer = threading.Timer(delay_seconds, callback)
        timer.daemon = True
        return timer

    def schedule_deferred_persist(self) -> None:
        if self._debounce_seconds <= 0:
            self.flush_immediately()
            return

        with self._lock:
            self._dirty = True
            self._token += 1
            token = self._token
            previous_timer = self._timer
            timer = self._timer_factory(
                self._debounce_seconds,
                lambda: self._flush_deferred(token),
            )
            self._timer = timer

        if previous_timer is not None:
            previous_timer.cancel()
        timer.start()

    def _flush_deferred(self, token: int) -> None:
        with self._lock:
            if token != self._token or not self._dirty:
                return
            self._timer = None
            self._dirty = False

        self._persist_fn()

    def flush_immediately(self) -> None:
        with self._lock:
            self._token += 1
            timer = self._timer
            self._timer = None
            self._dirty = False

        if timer is not None:
            timer.cancel()
        self._persist_fn()

    def shutdown(self) -> None:
        self.flush_immediately()
