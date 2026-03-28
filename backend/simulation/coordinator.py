from __future__ import annotations

import logging

from backend.payload_types import (
    PersistedSimulationSnapshotV5,
    TopologySpecInput,
    TopologySpecPatch,
)
from backend.rules import RuleRegistry
from backend.simulation.engine import SimulationEngine
from backend.simulation.persistence import SimulationStateStore
from backend.simulation.persistence_coordinator import PersistenceCoordinator
from backend.simulation.runtime import SimulationRuntime
from backend.simulation.service import SimulationService
from backend.simulation.state_restore import SimulationStateRestorer


class SimulationCoordinator:
    """Coordinates runtime, persistence, and restore around the simulation service."""

    def __init__(
        self,
        rule_registry: RuleRegistry,
        *,
        state_store: SimulationStateStore | None = None,
        persistence_debounce_ms: int = 100,
        timer_factory=None,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.rule_registry = rule_registry
        self.engine = SimulationEngine()
        self.service = SimulationService(rule_registry=rule_registry, engine=self.engine)
        self.runtime = SimulationRuntime(self.service)
        self.state_restorer = SimulationStateRestorer(rule_registry)
        self.state_store = state_store
        self.persistence = PersistenceCoordinator(
            self._save_state_to_store,
            debounce_ms=persistence_debounce_ms,
            timer_factory=timer_factory,
        )
        self.restore_state()

    def start_background_loop(self) -> None:
        self.runtime.start_background_loop()

    def stop_background_loop(self, timeout: float = 1.0) -> None:
        self.runtime.stop_background_loop(timeout)

    def shutdown(self, timeout: float = 1.0) -> None:
        self.runtime.stop_background_loop(timeout)
        self.persistence.shutdown()

    def _run_immediate_mutation(self, action, *args, **kwargs) -> None:
        action(*args, **kwargs)
        self.persistence.flush_immediately()

    def _run_deferred_mutation(self, action, *args, **kwargs) -> None:
        action(*args, **kwargs)
        self.persistence.schedule_deferred_persist()

    def _save_state_to_store(self) -> None:
        if self.state_store is None:
            return
        try:
            self.state_store.save(self.service.get_state())
        except Exception as exc:
            self.logger.warning("Failed to persist simulation state: %s", exc)

    def persist_state(self) -> None:
        self._save_state_to_store()

    def _load_persisted_payload(self) -> PersistedSimulationSnapshotV5 | None:
        if self.state_store is None:
            return None
        try:
            return self.state_store.load()
        except Exception as exc:
            self.logger.warning("Failed to restore persisted simulation state: %s", exc)
            return None

    def _restore_payload(self, payload: PersistedSimulationSnapshotV5) -> None:
        restored_state = self.state_restorer.restore(
            payload,
            fallback_state=self.service.state,
        )
        self.service.replace_state(restored_state)

    def restore_state(self) -> None:
        payload = self._load_persisted_payload()
        if payload is None:
            return

        try:
            self._restore_payload(payload)
        except Exception as exc:
            self.logger.warning("Persisted simulation state was invalid: %s", exc)

    def get_state(self):
        return self.service.get_state()

    def get_topology(self):
        return self.service.state.topology

    def get_topology_revision(self) -> str | None:
        topology = self.get_topology()
        return topology.topology_revision if topology is not None else None

    def get_rule(self):
        return self.service.state.rule

    def start(self) -> None:
        self.service.start()

    def pause(self) -> None:
        self._run_immediate_mutation(self.service.pause)

    def resume(self) -> None:
        self.service.resume()

    def step(self) -> None:
        self._run_immediate_mutation(self.service.step)

    def reset(
        self,
        topology_spec: TopologySpecInput | None = None,
        rule_name: str | None = None,
        speed: float | None = None,
        randomize: bool = False,
    ) -> None:
        self._run_immediate_mutation(
            self.service.reset,
            topology_spec=topology_spec,
            rule_name=rule_name,
            speed=speed,
            randomize=randomize,
        )

    def update_config(
        self,
        topology_spec: TopologySpecPatch | None = None,
        speed: float | None = None,
        rule_name: str | None = None,
    ) -> None:
        self._run_immediate_mutation(
            self.service.update_config,
            topology_spec=topology_spec,
            speed=speed,
            rule_name=rule_name,
        )

    def toggle_cell_by_id(self, cell_id: str) -> None:
        self._run_deferred_mutation(self.service.toggle_cell_by_id, cell_id)

    def set_cell_state_by_id(self, cell_id: str, state: int) -> None:
        self._run_deferred_mutation(self.service.set_cell_state_by_id, cell_id, state)

    def set_cells_by_id(self, cells: list[tuple[str, int]]) -> None:
        self._run_deferred_mutation(self.service.set_cells_by_id, cells)
