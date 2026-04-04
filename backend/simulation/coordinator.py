from __future__ import annotations

import logging
from collections.abc import Callable
from typing import ParamSpec

from backend.payload_types import (
    PersistedSimulationSnapshotV5,
    TopologySpecInput,
    TopologySpecPatch,
)
from backend.rules import RuleRegistry
from backend.rules.base import AutomatonRule
from backend.simulation.coordinator_mutations import SimulationCoordinatorMutationDispatcher
from backend.simulation.coordinator_persistence import SimulationCoordinatorPersistence
from backend.simulation.coordinator_restore import SimulationCoordinatorRestore
from backend.simulation.engine import SimulationEngine
from backend.simulation.models import SimulationSnapshot
from backend.simulation.persistence import SimulationStateStore
from backend.simulation.persistence_coordinator import TimerFactory
from backend.simulation.topology import LatticeTopology
from backend.simulation.runtime import SimulationRuntime
from backend.simulation.service import SimulationService
from backend.simulation.state_restore import SimulationStateRestorer

P = ParamSpec("P")


class SimulationCoordinator:
    """Coordinates runtime, persistence, and restore around the simulation service."""

    def __init__(
        self,
        rule_registry: RuleRegistry,
        *,
        state_store: SimulationStateStore | None = None,
        persistence_debounce_ms: int = 100,
        timer_factory: TimerFactory | None = None,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.rule_registry = rule_registry
        self.engine = SimulationEngine()
        self.service = SimulationService(rule_registry=rule_registry, engine=self.engine)
        self.runtime = SimulationRuntime(self.service)
        self.state_restorer = SimulationStateRestorer(rule_registry)
        self.state_store = state_store
        self.persistence_runtime = SimulationCoordinatorPersistence(
            logger=self.logger,
            get_state=self.service.get_state,
            state_store=state_store,
            debounce_ms=persistence_debounce_ms,
            timer_factory=timer_factory,
        )
        self.persistence = self.persistence_runtime.coordinator
        self.restore_runtime = SimulationCoordinatorRestore(
            logger=self.logger,
            service=self.service,
            state_restorer=self.state_restorer,
        )
        self.mutation_dispatcher = SimulationCoordinatorMutationDispatcher(
            flush_immediately=self.persistence_runtime.flush_immediately,
            schedule_deferred_persist=self.persistence_runtime.schedule_deferred_persist,
        )
        self.restore_state()

    def start_background_loop(self) -> None:
        self.runtime.start_background_loop()

    def stop_background_loop(self, timeout: float = 1.0) -> None:
        self.runtime.stop_background_loop(timeout)

    def shutdown(self, timeout: float = 1.0) -> None:
        self.runtime.stop_background_loop(timeout)
        self.persistence_runtime.shutdown()

    def _run_immediate_mutation(
        self,
        action: Callable[P, None],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        self.mutation_dispatcher.run_immediate(action, *args, **kwargs)

    def _run_deferred_mutation(
        self,
        action: Callable[P, None],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        self.mutation_dispatcher.run_deferred(action, *args, **kwargs)

    def _save_state_to_store(self) -> None:
        self.persistence_runtime.save_to_store()

    def persist_state(self) -> None:
        self.persistence_runtime.persist_state()

    def _load_persisted_payload(self) -> PersistedSimulationSnapshotV5 | None:
        return self.persistence_runtime.load_persisted_payload()

    def _restore_payload(self, payload: PersistedSimulationSnapshotV5) -> None:
        self.restore_runtime.restore_payload(payload)

    def restore_state(self) -> None:
        payload = self._load_persisted_payload()
        if payload is None:
            return

        try:
            self._restore_payload(payload)
        except Exception as exc:
            self.logger.warning("Persisted simulation state was invalid: %s", exc)

    def get_state(self) -> SimulationSnapshot:
        return self.service.get_state()

    def get_topology(self) -> LatticeTopology:
        return self.service.state.topology

    def get_topology_revision(self) -> str | None:
        topology = self.get_topology()
        return topology.topology_revision if topology is not None else None

    def get_rule(self) -> AutomatonRule:
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
