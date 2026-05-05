from __future__ import annotations

import logging
from collections.abc import Callable

from backend.payload_types import PersistedSimulationSnapshotV5
from backend.simulation.models import SimulationSnapshot
from backend.simulation.persistence import SimulationStateStore
from backend.simulation.persistence_coordinator import PersistenceCoordinator, TimerFactory


class SimulationCoordinatorPersistence:
    """Owns state-store save/load behavior and debounce-driven persistence."""

    def __init__(
        self,
        *,
        logger: logging.Logger,
        get_state: Callable[[], SimulationSnapshot],
        state_store: SimulationStateStore | None = None,
        debounce_ms: int = 100,
        timer_factory: TimerFactory | None = None,
    ) -> None:
        self._logger = logger
        self._get_state = get_state
        self._state_store = state_store
        self.coordinator = PersistenceCoordinator(
            self.save_to_store,
            debounce_ms=debounce_ms,
            timer_factory=timer_factory,
        )

    def save_to_store(self) -> None:
        if self._state_store is None:
            return
        try:
            self._state_store.save(self._get_state())
        except Exception as exc:
            self._logger.warning("Failed to persist simulation state: %s", exc)

    def persist_state(self) -> None:
        self.save_to_store()

    def load_persisted_payload(self) -> PersistedSimulationSnapshotV5 | None:
        if self._state_store is None:
            return None
        try:
            return self._state_store.load()
        except Exception as exc:
            self._logger.warning("Failed to restore persisted simulation state: %s", exc)
            return None

    def flush_immediately(self) -> None:
        self.coordinator.flush_immediately()

    def schedule_deferred_persist(self) -> None:
        self.coordinator.schedule_deferred_persist()

    def shutdown(self) -> None:
        self.coordinator.shutdown()
