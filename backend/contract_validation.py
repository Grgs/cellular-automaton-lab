from __future__ import annotations

from typing import Literal, NoReturn

from backend.payload_types import (
    CellTargetPayload,
    CellUpdatePayload,
    PersistedSimulationSnapshotV5,
    RawJsonObject,
    SparseCellsByIdPayload,
    TopologySpecPatch,
    TopologySpecRequestPayload,
)
from backend.rules import RuleRegistry
from backend.rules.base import AutomatonRule
from backend.simulation.models import TopologySpec
from backend.simulation.topology_catalog import (
    SUPPORTED_TOPOLOGY_FAMILIES,
    get_topology_definition,
    normalize_adjacency_mode,
)


SNAPSHOT_VERSION: Literal[5] = 5


class ContractValidationError(ValueError):
    """Raised when a command or persisted payload is malformed."""


def _raise_validation(message: str, exc: Exception | None = None) -> NoReturn:
    if exc is None:
        raise ContractValidationError(message)
    raise ContractValidationError(message) from exc


def require_json_object(value: object, message: str) -> RawJsonObject:
    if not isinstance(value, dict):
        _raise_validation(message)
    return value


def _coerce_int(value: object, message: str) -> int:
    if isinstance(value, (str, bytes, bytearray, int, float)):
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            _raise_validation(message, exc)
    _raise_validation(message)


def _coerce_float(value: object, message: str) -> float:
    if isinstance(value, (str, bytes, bytearray, int, float)):
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            _raise_validation(message, exc)
    _raise_validation(message)


def parse_optional_int(payload: RawJsonObject, key: str) -> int | None:
    value = payload.get(key)
    if value in (None, ""):
        return None
    return _coerce_int(value, f"'{key}' must be an integer.")


def parse_optional_float(payload: RawJsonObject, key: str) -> float | None:
    value = payload.get(key)
    if value in (None, ""):
        return None
    return _coerce_float(value, f"'{key}' must be a number.")


def parse_required_int(payload: RawJsonObject, key: str) -> int:
    if key not in payload:
        _raise_validation(f"Missing required field '{key}'.")
    return _coerce_int(payload[key], f"'{key}' must be an integer.")


def parse_state_value(payload: RawJsonObject, rule: AutomatonRule, key: str = "state") -> int:
    if key not in payload:
        _raise_validation(f"Missing required field '{key}'.")
    parsed = _coerce_int(payload[key], f"'{key}' must be a valid state value.")
    if not rule.is_valid_state(parsed):
        _raise_validation(f"'{key}' must be one of the states supported by rule '{rule.name}'.")
    return parsed


def parse_cell_id(payload: RawJsonObject, key: str = "id") -> str:
    value = payload.get(key)
    if value in (None, ""):
        _raise_validation(f"Missing required field '{key}'.")
    if not isinstance(value, str):
        _raise_validation(f"'{key}' must be a string.")
    return value


def parse_cell_target(payload: RawJsonObject, *, id_key: str = "id") -> CellTargetPayload:
    return {"id": parse_cell_id(payload, id_key)}


def parse_cell_updates(
    payload: RawJsonObject,
    rule: AutomatonRule,
    key: str = "cells",
) -> list[CellUpdatePayload]:
    raw_cells = payload.get(key)
    if not isinstance(raw_cells, list) or len(raw_cells) == 0:
        _raise_validation(f"'{key}' must be a non-empty list.")

    parsed_cells: list[CellUpdatePayload] = []
    for index, cell in enumerate(raw_cells):
        if not isinstance(cell, dict):
            _raise_validation(f"'{key}' must be a non-empty list.")
        cell_id = cell.get("id")
        if not isinstance(cell_id, str) or cell_id == "":
            _raise_validation(f"'{key}[{index}].id' must be a string.")
        parsed_cells.append({
            "id": cell_id,
            "state": parse_state_value(cell, rule, "state"),
        })
    return parsed_cells


def parse_rule_name(payload: RawJsonObject, rule_registry: RuleRegistry) -> str | None:
    value = payload.get("rule")
    if value in (None, ""):
        return None
    if not isinstance(value, str) or not rule_registry.has(value):
        _raise_validation("'rule' must reference a known rule module.")
    return value


def parse_topology_spec(
    payload: RawJsonObject,
    key: str = "topology_spec",
) -> TopologySpecRequestPayload | None:
    raw_topology_spec = payload.get(key)
    if raw_topology_spec in (None, ""):
        return None
    if not isinstance(raw_topology_spec, dict):
        _raise_validation(f"'{key}' must be an object.")

    tiling_family_value = raw_topology_spec.get("tiling_family")
    if tiling_family_value in (None, ""):
        tiling_family = ""
    elif isinstance(tiling_family_value, str):
        tiling_family = tiling_family_value
    else:
        supported = ", ".join(SUPPORTED_TOPOLOGY_FAMILIES)
        _raise_validation(f"'{key}.tiling_family' must be one of: {supported}.")

    if tiling_family not in SUPPORTED_TOPOLOGY_FAMILIES:
        supported = ", ".join(SUPPORTED_TOPOLOGY_FAMILIES)
        _raise_validation(f"'{key}.tiling_family' must be one of: {supported}.")

    adjacency_mode_value = raw_topology_spec.get("adjacency_mode")
    adjacency_mode = None if adjacency_mode_value in (None, "") else str(adjacency_mode_value)
    definition = get_topology_definition(tiling_family)

    return {
        "tiling_family": tiling_family,
        "adjacency_mode": normalize_adjacency_mode(tiling_family, adjacency_mode),
        "sizing_mode": definition.sizing_mode,
        "width": parse_optional_int(raw_topology_spec, "width"),
        "height": parse_optional_int(raw_topology_spec, "height"),
        "patch_depth": parse_optional_int(raw_topology_spec, "patch_depth"),
    }


def normalize_reset_topology_spec(payload: RawJsonObject) -> TopologySpecRequestPayload | None:
    if payload.get("geometry") not in (None, ""):
        _raise_validation("'geometry' must be provided through 'topology_spec'.")
    if payload.get("width") not in (None, "") or payload.get("height") not in (None, ""):
        _raise_validation("'width' and 'height' must be provided through 'topology_spec'.")
    if payload.get("patch_depth") not in (None, ""):
        _raise_validation("'patch_depth' must be provided through 'topology_spec'.")
    return parse_topology_spec(payload)


def normalize_config_topology_patch(payload: RawJsonObject) -> TopologySpecPatch:
    if payload.get("geometry") not in (None, ""):
        _raise_validation("'geometry' can only be changed through reset.")
    if payload.get("width") not in (None, "") or payload.get("height") not in (None, ""):
        _raise_validation("'width' and 'height' must be provided through 'topology_spec'.")
    if payload.get("patch_depth") not in (None, ""):
        _raise_validation("'patch_depth' can only be changed through reset.")

    topology_spec = payload.get("topology_spec")
    if topology_spec is None:
        return {}
    mapping = require_json_object(topology_spec, "'topology_spec' must be an object.")
    disallowed_keys = {"tiling_family", "adjacency_mode", "sizing_mode", "patch_depth"} & set(mapping.keys())
    if disallowed_keys:
        disallowed = ", ".join(sorted(disallowed_keys))
        _raise_validation(f"'{disallowed}' can only be changed through reset.")

    topology_patch: TopologySpecPatch = {}
    width = parse_optional_int(mapping, "width")
    height = parse_optional_int(mapping, "height")
    if width is not None:
        topology_patch["width"] = width
    if height is not None:
        topology_patch["height"] = height
    return topology_patch


def validate_persisted_snapshot_payload(payload: object) -> PersistedSimulationSnapshotV5:
    payload_mapping = require_json_object(
        payload,
        "Persisted simulation state must be a JSON object.",
    )

    version = payload_mapping.get("version")
    if version != SNAPSHOT_VERSION:
        _raise_validation("Persisted simulation state version is unsupported.")

    topology_spec_mapping = require_json_object(
        payload_mapping.get("topology_spec"),
        "Persisted simulation state topology spec is invalid.",
    )
    topology_spec = TopologySpec.from_values(
        tiling_family=str(topology_spec_mapping.get("tiling_family") or ""),
        adjacency_mode=str(topology_spec_mapping.get("adjacency_mode") or ""),
        width=_coerce_int(topology_spec_mapping.get("width"), "Persisted simulation field 'width' is invalid."),
        height=_coerce_int(topology_spec_mapping.get("height"), "Persisted simulation field 'height' is invalid."),
        patch_depth=_coerce_int(topology_spec_mapping.get("patch_depth"), "Persisted simulation field 'patch_depth' is invalid."),
    )

    running = payload_mapping.get("running")
    if not isinstance(running, bool):
        _raise_validation("Persisted simulation running state is invalid.")

    rule_name = payload_mapping.get("rule")
    if not isinstance(rule_name, str) or not rule_name:
        _raise_validation("Persisted simulation rule is invalid.")

    cells_by_id_payload = payload_mapping.get("cells_by_id")
    if not isinstance(cells_by_id_payload, dict):
        _raise_validation("Persisted simulation cells_by_id payload is invalid.")
    normalized_cells_by_id: SparseCellsByIdPayload = {}
    for cell_id, cell_state in cells_by_id_payload.items():
        if not isinstance(cell_id, str) or not cell_id:
            _raise_validation("Persisted simulation cells_by_id payload is invalid.")
        normalized_cells_by_id[cell_id] = _coerce_int(
            cell_state,
            "Persisted simulation cells_by_id payload is invalid.",
        )

    speed = _coerce_float(
        payload_mapping.get("speed"),
        "Persisted simulation state numeric fields are invalid.",
    )
    generation = _coerce_int(
        payload_mapping.get("generation"),
        "Persisted simulation state numeric fields are invalid.",
    )

    return {
        "version": SNAPSHOT_VERSION,
        "topology_spec": topology_spec.to_dict(),
        "speed": speed,
        "running": running,
        "generation": generation,
        "rule": rule_name,
        "cells_by_id": normalized_cells_by_id,
    }
