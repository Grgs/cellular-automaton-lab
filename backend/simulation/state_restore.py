from __future__ import annotations

from backend.payload_types import PersistedSimulationSnapshotInput, SparseCellsByIdPayload
from backend.rules import RuleRegistry
from backend.rules.base import AutomatonRule
from backend.simulation.models import (
    SimulationStateData,
)
from backend.simulation.topology import SimulationBoard, board_from_cells_by_id, board_from_states
from backend.simulation.transition_planner import plan_restore_transition


class SimulationStateRestorer:
    """Builds normalized mutable simulation state from persisted snapshot payloads."""

    def __init__(self, rule_registry: RuleRegistry) -> None:
        self.rule_registry = rule_registry

    def restore(
        self,
        payload: PersistedSimulationSnapshotInput,
        *,
        fallback_state: SimulationStateData,
    ) -> SimulationStateData:
        plan = plan_restore_transition(
            payload,
            fallback_state=fallback_state,
            rule_registry=self.rule_registry,
        )
        next_board = self._normalize_board(
            payload,
            geometry=plan.config.geometry,
            width=plan.config.width,
            height=plan.config.height,
            patch_depth=plan.config.patch_depth,
            rule=plan.rule,
            payload_kind=plan.board_payload_kind,
        )
        next_config = plan.config.updated(
            width=next_board.topology.width,
            height=next_board.topology.height,
        )

        return SimulationStateData(
            config=next_config,
            running=False,
            generation=plan.generation,
            rule=plan.rule,
            board=next_board,
        )

    def _normalize_board(
        self,
        payload: PersistedSimulationSnapshotInput,
        *,
        geometry: str,
        width: int,
        height: int,
        patch_depth: int,
        rule: AutomatonRule,
        payload_kind: str,
    ) -> SimulationBoard:
        if payload_kind == "cells_by_id":
            return board_from_cells_by_id(
                geometry,
                width,
                height,
                self._normalize_cells_by_id(payload.get("cells_by_id"), rule),
                patch_depth=patch_depth,
            )
        return board_from_states(geometry, width, height, [], patch_depth=patch_depth)

    def _normalize_cells_by_id(
        self,
        cells_by_id_payload: object,
        rule: AutomatonRule,
    ) -> SparseCellsByIdPayload:
        allowed_states = rule.state_values()
        normalized: SparseCellsByIdPayload = {}
        if not isinstance(cells_by_id_payload, dict):
            return normalized
        for cell_id, cell_state in cells_by_id_payload.items():
            if not isinstance(cell_id, str) or cell_id == "":
                continue
            try:
                normalized_state = int(cell_state)
            except (TypeError, ValueError):
                normalized_state = 0
            if normalized_state in allowed_states and normalized_state != 0:
                normalized[cell_id] = normalized_state
        return normalized
