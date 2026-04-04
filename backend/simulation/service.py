from __future__ import annotations

import random
import threading

from backend.payload_types import TopologySpecInput, TopologySpecPatch
from backend.rules import RuleRegistry
from backend.simulation.engine import SimulationEngine
from backend.simulation.models import SimulationSnapshot, SimulationStateData
from backend.simulation.service_boards import (
    build_initial_state,
    clone_service_board,
    coerce_board_to_rule,
    empty_service_board,
    random_service_board,
    step_board,
    transfer_board,
)
from backend.simulation.service_cells import (
    set_cells_by_id,
    toggle_cells_by_id,
    validate_state_values,
)
from backend.simulation.service_snapshots import snapshot_state
from backend.simulation.service_transitions import (
    apply_config_transition,
    apply_reset_transition,
)


class SimulationOperationError(ValueError):
    """Raised when a requested simulation operation is invalid for the current rule."""


class SimulationService:
    """Thread-safe state mutation service for the cellular automaton."""

    def __init__(
        self,
        rule_registry: RuleRegistry,
        engine: SimulationEngine | None = None,
        *,
        lock: threading.Lock | None = None,
        state: SimulationStateData | None = None,
    ) -> None:
        self.rule_registry = rule_registry
        self.engine = engine or SimulationEngine()
        self._lock = lock or threading.Lock()
        self._state = state or build_initial_state(rule_registry)

    @property
    def lock(self) -> threading.Lock:
        return self._lock

    @property
    def state(self) -> SimulationStateData:
        return self._state

    def runtime_plan(self) -> tuple[bool, float]:
        with self._lock:
            if self._state.running:
                return True, max(0.02, 1.0 / self._state.config.speed)
            return False, 0.2

    def get_state(self) -> SimulationSnapshot:
        with self._lock:
            return snapshot_state(self._state)

    def replace_state(self, next_state: SimulationStateData) -> None:
        with self._lock:
            self._state = SimulationStateData(
                config=next_state.config,
                running=bool(next_state.running),
                generation=int(next_state.generation),
                rule=next_state.rule,
                board=clone_service_board(next_state.board),
            )

    def start(self) -> None:
        with self._lock:
            self._state.running = True

    def pause(self) -> None:
        with self._lock:
            self._state.running = False

    def resume(self) -> None:
        self.start()

    def step(self) -> None:
        with self._lock:
            self._state.running = False
            step_board(self.engine, self._state)

    def step_if_running(self) -> bool:
        with self._lock:
            if not self._state.running:
                return False
            step_board(self.engine, self._state)
            return True

    def reset(
        self,
        topology_spec: TopologySpecInput | None = None,
        rule_name: str | None = None,
        speed: float | None = None,
        randomize: bool = False,
    ) -> None:
        with self._lock:
            try:
                apply_reset_transition(
                    self._state,
                    self.rule_registry,
                    create_random_board=random_service_board,
                    create_empty_board=empty_service_board,
                    choice_fn=random.choices,
                    topology_spec=topology_spec,
                    rule_name=rule_name,
                    speed=speed,
                    randomize=randomize,
                )
            except ValueError as exc:
                raise SimulationOperationError(str(exc)) from exc

    def update_config(
        self,
        topology_spec: TopologySpecPatch | None = None,
        speed: float | None = None,
        rule_name: str | None = None,
    ) -> None:
        with self._lock:
            try:
                apply_config_transition(
                    self._state,
                    self.rule_registry,
                    transfer_board=transfer_board,
                    coerce_board_to_rule=coerce_board_to_rule,
                    topology_spec=topology_spec,
                    speed=speed,
                    rule_name=rule_name,
                )
            except ValueError as exc:
                raise SimulationOperationError(str(exc)) from exc

    def toggle_cell_by_id(self, cell_id: str) -> None:
        with self._lock:
            toggle_cells_by_id(self._state, [cell_id])

    def set_cell_state_by_id(self, cell_id: str, state: int) -> None:
        with self._lock:
            try:
                validate_state_values(self._state.rule, [state])
            except ValueError as exc:
                raise SimulationOperationError(str(exc)) from exc
            set_cells_by_id(self._state, [(cell_id, state)])

    def set_cells_by_id(self, cells: list[tuple[str, int]]) -> None:
        with self._lock:
            try:
                validate_state_values(self._state.rule, [state for _, state in cells])
            except ValueError as exc:
                raise SimulationOperationError(str(exc)) from exc
            set_cells_by_id(self._state, cells)
