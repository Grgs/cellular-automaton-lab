from __future__ import annotations

import random
import threading

from backend.defaults import DEFAULT_GEOMETRY
from backend.payload_types import TopologySpecInput, TopologySpecPatch
from backend.rules import RuleRegistry
from backend.rules.base import AutomatonRule
from backend.rules.constraints import normalize_rule_dimensions
from backend.simulation.engine import SimulationEngine
from backend.simulation.models import (
    RuleSnapshot,
    SimulationConfig,
    SimulationSnapshot,
    SimulationStateData,
)
from backend.simulation.topology import (
    SimulationBoard,
    empty_board,
)
from backend.simulation.transition_planner import (
    plan_config_transition,
    plan_reset_transition,
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
        default_config = SimulationConfig()
        default_rule = rule_registry.default_for_geometry(DEFAULT_GEOMETRY)
        default_width, default_height = normalize_rule_dimensions(
            default_rule,
            default_config.width,
            default_config.height,
        )
        default_config = default_config.updated(width=default_width, height=default_height)
        self.rule_registry = rule_registry
        self.engine = engine or SimulationEngine()
        self._lock = lock or threading.Lock()
        self._state = state or SimulationStateData(
            config=default_config,
            running=False,
            generation=0,
            rule=default_rule,
            board=empty_board(DEFAULT_GEOMETRY, default_config.width, default_config.height),
        )

    @property
    def lock(self) -> threading.Lock:
        return self._lock

    @property
    def state(self) -> SimulationStateData:
        return self._state

    def _empty_board(
        self,
        geometry: str,
        width: int,
        height: int,
        patch_depth: int | None = None,
    ) -> SimulationBoard:
        return empty_board(geometry, width, height, patch_depth=patch_depth)

    def _random_board(
        self,
        geometry: str,
        width: int,
        height: int,
        rule: AutomatonRule,
        *,
        patch_depth: int | None = None,
    ) -> SimulationBoard:
        if not rule.supports_randomize or not rule.randomize_weights:
            raise SimulationOperationError(f"Rule '{rule.name}' does not support random reset.")

        state_values = list(rule.randomize_weights.keys())
        state_weights = list(rule.randomize_weights.values())
        board = self._empty_board(geometry, width, height, patch_depth=patch_depth)
        board.cell_states = random.choices(state_values, weights=state_weights, k=board.topology.cell_count)
        return board

    def _clone_board(self, board: SimulationBoard) -> SimulationBoard:
        return board.clone()

    def _validate_state_value(self, state: int) -> None:
        if not self._state.rule.is_valid_state(state):
            raise SimulationOperationError(
                f"State '{state}' is invalid for rule '{self._state.rule.name}'."
            )

    def _validate_state_values(self, states: list[int]) -> None:
        for state in states:
            self._validate_state_value(state)

    def _set_cells_by_id_unlocked(self, cells: list[tuple[str, int]]) -> None:
        for cell_id, state in cells:
            if self._state.topology.has_cell(cell_id):
                self._state.board.set_state_for(cell_id, int(state))

    def _toggle_cells_by_id_unlocked(self, cell_ids: list[str]) -> None:
        for cell_id in cell_ids:
            if not self._state.topology.has_cell(cell_id):
                continue
            current_state = self._state.board.state_for(cell_id)
            self._state.board.set_state_for(
                cell_id,
                0 if current_state else self._state.rule.default_paint_state,
            )

    def _coerce_board_to_rule(self, board: SimulationBoard, rule: AutomatonRule) -> SimulationBoard:
        allowed_states = rule.state_values()
        return SimulationBoard(
            topology=board.topology,
            cell_states=[
                cell_state if cell_state in allowed_states else 0
                for cell_state in board.cell_states
            ],
        )

    def _transfer_board(
        self,
        board: SimulationBoard,
        geometry: str,
        width: int,
        height: int,
        patch_depth: int | None = None,
    ) -> SimulationBoard:
        resized = self._empty_board(geometry, width, height, patch_depth=patch_depth)
        old_lookup = {
            cell.id: board.cell_states[index]
            for index, cell in enumerate(board.topology.cells)
        }
        for index, cell in enumerate(resized.topology.cells):
            resized.cell_states[index] = old_lookup.get(cell.id, 0)
        return resized

    def _snapshot_unlocked(self) -> SimulationSnapshot:
        return SimulationSnapshot(
            board=self._clone_board(self._state.board),
            config=self._state.config,
            running=self._state.running,
            generation=self._state.generation,
            rule=RuleSnapshot.from_rule(self._state.rule),
        )

    def runtime_plan(self) -> tuple[bool, float]:
        with self._lock:
            if self._state.running:
                return True, max(0.02, 1.0 / self._state.config.speed)
            return False, 0.2

    def get_state(self) -> SimulationSnapshot:
        with self._lock:
            return self._snapshot_unlocked()

    def replace_state(self, next_state: SimulationStateData) -> None:
        with self._lock:
            self._state = SimulationStateData(
                config=next_state.config,
                running=bool(next_state.running),
                generation=int(next_state.generation),
                rule=next_state.rule,
                board=self._clone_board(next_state.board),
            )

    def start(self) -> None:
        with self._lock:
            self._state.running = True

    def pause(self) -> None:
        with self._lock:
            self._state.running = False

    def resume(self) -> None:
        self.start()

    def _step_unlocked(self) -> None:
        self._state.board = self.engine.step_board(
            self._state.board,
            self._state.rule,
        )
        self._state.generation += 1

    def step(self) -> None:
        with self._lock:
            self._state.running = False
            self._step_unlocked()

    def step_if_running(self) -> bool:
        with self._lock:
            if not self._state.running:
                return False
            self._step_unlocked()
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
                plan = plan_reset_transition(
                    self._state,
                    self.rule_registry,
                    topology_spec=topology_spec,
                    rule_name=rule_name,
                    speed=speed,
                    randomize=randomize,
                )
            except ValueError as exc:
                raise SimulationOperationError(str(exc)) from exc

            self._state.running = False
            self._state.generation = 0
            self._state.rule = plan.rule
            next_board = (
                self._random_board(
                    plan.config.geometry,
                    plan.config.width,
                    plan.config.height,
                    plan.rule,
                    patch_depth=plan.config.patch_depth,
                )
                if plan.board_mode == "randomize"
                else self._empty_board(
                    plan.config.geometry,
                    plan.config.width,
                    plan.config.height,
                    patch_depth=plan.config.patch_depth,
                )
            )
            self._state.board = next_board
            self._state.config = plan.config.updated(
                width=next_board.topology.width,
                height=next_board.topology.height,
            )

    def update_config(
        self,
        topology_spec: TopologySpecPatch | None = None,
        speed: float | None = None,
        rule_name: str | None = None,
    ) -> None:
        with self._lock:
            try:
                plan = plan_config_transition(
                    self._state,
                    self.rule_registry,
                    topology_spec=topology_spec,
                    speed=speed,
                    rule_name=rule_name,
                )
            except ValueError as exc:
                raise SimulationOperationError(str(exc)) from exc

            if plan.board_mode == "transfer":
                self._state.running = False
                self._state.board = self._transfer_board(
                    self._state.board,
                    plan.config.geometry,
                    plan.config.width,
                    plan.config.height,
                    plan.config.patch_depth,
                )
            if plan.coerce_rule_states:
                self._state.board = self._coerce_board_to_rule(self._state.board, plan.rule)
                self._state.rule = plan.rule
            self._state.config = plan.config

    def toggle_cell_by_id(self, cell_id: str) -> None:
        with self._lock:
            self._toggle_cells_by_id_unlocked([cell_id])

    def set_cell_state_by_id(self, cell_id: str, state: int) -> None:
        with self._lock:
            self._validate_state_values([state])
            self._set_cells_by_id_unlocked([(cell_id, state)])

    def set_cells_by_id(self, cells: list[tuple[str, int]]) -> None:
        with self._lock:
            self._validate_state_values([state for _, state in cells])
            self._set_cells_by_id_unlocked(cells)
