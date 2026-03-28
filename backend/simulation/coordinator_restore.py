from __future__ import annotations

import logging
from collections.abc import Callable

from backend.payload_types import PersistedSimulationSnapshotV5
from backend.simulation.service import SimulationService
from backend.simulation.state_restore import SimulationStateRestorer


class SimulationCoordinatorRestore:
    """Owns persisted-state restore flow around the simulation service."""

    def __init__(
        self,
        *,
        logger: logging.Logger,
        service: SimulationService,
        state_restorer: SimulationStateRestorer,
    ) -> None:
        self._logger = logger
        self._service = service
        self._state_restorer = state_restorer

    def restore_payload(self, payload: PersistedSimulationSnapshotV5) -> None:
        restored_state = self._state_restorer.restore(
            payload,
            fallback_state=self._service.state,
        )
        self._service.replace_state(restored_state)

    def restore_state(self, load_payload: Callable[[], PersistedSimulationSnapshotV5 | None]) -> None:
        payload = load_payload()
        if payload is None:
            return

        try:
            self.restore_payload(payload)
        except Exception as exc:
            self._logger.warning("Persisted simulation state was invalid: %s", exc)
