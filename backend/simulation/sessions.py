from __future__ import annotations

import re
import threading
from collections import OrderedDict
from pathlib import Path

from backend.rules import RuleRegistry
from backend.simulation.coordinator import SimulationCoordinator
from backend.simulation.persistence import SimulationStateStore

DEFAULT_SESSION_ID = "default"
SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
DEFAULT_MAX_SESSIONS = 64


class SimulationSessionError(ValueError):
    """Raised when a simulation session id is malformed."""


def validate_session_id(session_id: str) -> str:
    if not SESSION_ID_PATTERN.fullmatch(session_id):
        raise SimulationSessionError(
            "Session id must be 1-80 characters of letters, numbers, '_' or '-'."
        )
    return session_id


class SimulationSessionRegistry:
    """Lazily creates and owns simulation coordinators by browser session id.

    The registry is bounded: it keeps at most ``max_sessions`` live
    coordinators and evicts the least-recently-used one when a new session
    pushes past the cap. Eviction shuts the coordinator's background loop
    down and flushes its state to ``sessions/<id>.json``; because every
    coordinator restores from that file on construction, a re-accessed
    evicted session resumes losslessly. The cap bounds the number of live
    background threads and resident coordinators regardless of how many
    distinct session ids arrive.
    """

    def __init__(
        self,
        *,
        rule_registry: RuleRegistry,
        instance_path: str | Path,
        max_sessions: int = DEFAULT_MAX_SESSIONS,
    ) -> None:
        if max_sessions < 1:
            raise ValueError("max_sessions must be at least 1.")
        self._rule_registry = rule_registry
        self._instance_path = Path(instance_path)
        self._max_sessions = max_sessions
        self._lock = threading.Lock()
        self._sessions: OrderedDict[str, SimulationCoordinator] = OrderedDict()

    def _state_store_for(self, session_id: str) -> SimulationStateStore:
        state_path = self._instance_path / "sessions" / f"{session_id}.json"
        return SimulationStateStore(state_path)

    def get(self, session_id: str) -> SimulationCoordinator:
        validated_session_id = validate_session_id(session_id)
        evicted: SimulationCoordinator | None = None
        with self._lock:
            coordinator = self._sessions.get(validated_session_id)
            if coordinator is not None:
                self._sessions.move_to_end(validated_session_id)
                return coordinator

            coordinator = SimulationCoordinator(
                rule_registry=self._rule_registry,
                state_store=self._state_store_for(validated_session_id),
            )
            coordinator.start_background_loop()
            self._sessions[validated_session_id] = coordinator
            if len(self._sessions) > self._max_sessions:
                _, evicted = self._sessions.popitem(last=False)

        # Shut the evicted coordinator down outside the lock: shutdown() joins
        # its background thread (up to a timeout), and holding the registry
        # lock during that join would stall every concurrent session lookup.
        if evicted is not None:
            evicted.shutdown()
        return coordinator

    def shutdown(self) -> None:
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for coordinator in sessions:
            coordinator.shutdown()

    def stop_background_loops(self) -> None:
        with self._lock:
            sessions = list(self._sessions.values())
        for coordinator in sessions:
            coordinator.stop_background_loop()
