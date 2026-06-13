from __future__ import annotations

import re
import threading
from pathlib import Path

from backend.rules import RuleRegistry
from backend.simulation.coordinator import SimulationCoordinator
from backend.simulation.persistence import SimulationStateStore

DEFAULT_SESSION_ID = "default"
SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


class SimulationSessionError(ValueError):
    """Raised when a simulation session id is malformed."""


def validate_session_id(session_id: str) -> str:
    if not SESSION_ID_PATTERN.fullmatch(session_id):
        raise SimulationSessionError(
            "Session id must be 1-80 characters of letters, numbers, '_' or '-'."
        )
    return session_id


class SimulationSessionRegistry:
    """Lazily creates and owns simulation coordinators by browser session id."""

    def __init__(self, *, rule_registry: RuleRegistry, instance_path: str | Path) -> None:
        self._rule_registry = rule_registry
        self._instance_path = Path(instance_path)
        self._lock = threading.Lock()
        self._sessions: dict[str, SimulationCoordinator] = {}

    def _state_store_for(self, session_id: str) -> SimulationStateStore:
        state_path = self._instance_path / "sessions" / f"{session_id}.json"
        return SimulationStateStore(state_path)

    def get(self, session_id: str) -> SimulationCoordinator:
        validated_session_id = validate_session_id(session_id)
        with self._lock:
            coordinator = self._sessions.get(validated_session_id)
            if coordinator is not None:
                return coordinator

            coordinator = SimulationCoordinator(
                rule_registry=self._rule_registry,
                state_store=self._state_store_for(validated_session_id),
            )
            coordinator.start_background_loop()
            self._sessions[validated_session_id] = coordinator
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
