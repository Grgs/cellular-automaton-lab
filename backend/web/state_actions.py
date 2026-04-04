from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from backend.contract_validation import (
    normalize_config_topology_patch,
    normalize_reset_topology_spec,
    parse_cell_target,
    parse_cell_updates,
    parse_optional_float,
    parse_rule_name,
    parse_state_value,
)
from backend.payload_types import (
    CellTargetPayload,
    CellUpdatePayload,
    RawJsonObject,
)
from backend.rules import RuleRegistry
from backend.simulation.coordinator import SimulationCoordinator


@dataclass(frozen=True)
class StateActionService:
    coordinator: SimulationCoordinator
    rules: RuleRegistry

    def apply_reset_payload(self, payload: RawJsonObject) -> None:
        topology_spec = normalize_reset_topology_spec(payload)
        self.coordinator.reset(
            topology_spec=topology_spec,
            rule_name=parse_rule_name(payload, self.rules),
            speed=parse_optional_float(payload, "speed"),
            randomize=bool(payload.get("randomize", False)),
        )

    def apply_config_payload(self, payload: RawJsonObject) -> None:
        self.coordinator.update_config(
            topology_spec=normalize_config_topology_patch(payload),
            speed=parse_optional_float(payload, "speed"),
            rule_name=parse_rule_name(payload, self.rules),
        )

    def _dispatch_single_cell_target(
        self,
        target: CellTargetPayload,
        *,
        by_id: Callable[[str], None],
    ) -> None:
        by_id(str(target["id"]))

    def _dispatch_cell_updates(self, parsed_cells: list[CellUpdatePayload]) -> None:
        id_cells = [
            (cell["id"], cell["state"])
            for cell in parsed_cells
        ]
        if id_cells:
            self.coordinator.set_cells_by_id(id_cells)

    def apply_toggle_cell_payload(self, payload: RawJsonObject) -> None:
        self._dispatch_single_cell_target(
            parse_cell_target(payload),
            by_id=self.coordinator.toggle_cell_by_id,
        )

    def apply_set_cell_payload(self, payload: RawJsonObject) -> None:
        state = parse_state_value(payload, self.coordinator.get_rule())
        self._dispatch_single_cell_target(
            parse_cell_target(payload),
            by_id=lambda cell_id: self.coordinator.set_cell_state_by_id(
                cell_id=cell_id,
                state=state,
            ),
        )

    def apply_set_cells_payload(self, payload: RawJsonObject) -> None:
        self._dispatch_cell_updates(parse_cell_updates(payload, self.coordinator.get_rule()))
