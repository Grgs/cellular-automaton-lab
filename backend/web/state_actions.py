from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from backend.payload_types import (
    CellTargetPayload,
    CellUpdatePayload,
    RawJsonObject,
    TopologySpecPatch,
)
from backend.rules import RuleRegistry
from backend.simulation.coordinator import SimulationCoordinator
from backend.web.requests import (
    RequestValidationError,
    parse_cell_target,
    parse_cell_updates,
    parse_optional_float,
    parse_optional_int,
    parse_rule_name,
    parse_state_value,
    parse_topology_spec,
)


@dataclass(frozen=True)
class StateActionService:
    coordinator: SimulationCoordinator
    rules: RuleRegistry

    def apply_reset_payload(self, payload: RawJsonObject) -> None:
        if payload.get("geometry") not in (None, ""):
            raise RequestValidationError("'geometry' must be provided through 'topology_spec'.")
        if payload.get("width") not in (None, "") or payload.get("height") not in (None, ""):
            raise RequestValidationError("'width' and 'height' must be provided through 'topology_spec'.")
        if payload.get("patch_depth") not in (None, ""):
            raise RequestValidationError("'patch_depth' must be provided through 'topology_spec'.")
        topology_spec = parse_topology_spec(payload)
        self.coordinator.reset(
            topology_spec=topology_spec,
            rule_name=parse_rule_name(payload, self.rules),
            speed=parse_optional_float(payload, "speed"),
            randomize=bool(payload.get("randomize", False)),
        )

    def apply_config_payload(self, payload: RawJsonObject) -> None:
        if payload.get("geometry") not in (None, ""):
            raise RequestValidationError("'geometry' can only be changed through reset.")
        if payload.get("width") not in (None, "") or payload.get("height") not in (None, ""):
            raise RequestValidationError("'width' and 'height' must be provided through 'topology_spec'.")
        if payload.get("patch_depth") not in (None, ""):
            raise RequestValidationError("'patch_depth' can only be changed through reset.")
        topology_spec = payload.get("topology_spec")
        if topology_spec is not None and not isinstance(topology_spec, dict):
            raise RequestValidationError("'topology_spec' must be an object.")
        disallowed_keys = {"tiling_family", "adjacency_mode", "sizing_mode", "patch_depth"} & set((topology_spec or {}).keys())
        if disallowed_keys:
            disallowed = ", ".join(sorted(disallowed_keys))
            raise RequestValidationError(f"'{disallowed}' can only be changed through reset.")
        topology_patch: TopologySpecPatch = {}
        if topology_spec is not None:
            width = parse_optional_int(topology_spec, "width")
            height = parse_optional_int(topology_spec, "height")
            if width is not None:
                topology_patch["width"] = width
            if height is not None:
                topology_patch["height"] = height
        self.coordinator.update_config(
            topology_spec=topology_patch,
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
