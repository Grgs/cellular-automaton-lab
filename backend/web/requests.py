from __future__ import annotations

from typing import Mapping, NoReturn

from flask import Request
from pydantic import ValidationError

from backend.payload_types import (
    CellTargetPayload,
    CellUpdatePayload,
    RawJsonObject,
    TopologySpecRequestPayload,
)
from backend.rules import RuleRegistry
from backend.rules.base import AutomatonRule
from backend.simulation.topology_catalog import (
    SUPPORTED_TOPOLOGY_FAMILIES,
    get_topology_definition,
    normalize_adjacency_mode,
)
from backend.web.request_models import (
    CellIdValueModel,
    CellUpdatesPayloadModel,
    IdCellTargetModel,
    OptionalFloatValueModel,
    OptionalIntValueModel,
    RequiredIntValueModel,
    RuleNameValueModel,
    StateValueModel,
    TopologySpecValueModel,
)


class RequestValidationError(ValueError):
    """Raised when an API request payload is malformed."""


def get_payload(request: Request) -> RawJsonObject:
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else {}


def _raise_validation(message: str, exc: Exception | None = None) -> NoReturn:
    if exc is None:
        raise RequestValidationError(message)
    raise RequestValidationError(message) from exc


def parse_optional_int(payload: Mapping[str, object], key: str) -> int | None:
    try:
        return OptionalIntValueModel.model_validate({"value": payload.get(key)}).value
    except ValidationError as exc:
        _raise_validation(f"'{key}' must be an integer.", exc)


def parse_optional_float(payload: Mapping[str, object], key: str) -> float | None:
    try:
        return OptionalFloatValueModel.model_validate({"value": payload.get(key)}).value
    except ValidationError as exc:
        _raise_validation(f"'{key}' must be a number.", exc)


def parse_required_int(payload: Mapping[str, object], key: str) -> int:
    if key not in payload:
        _raise_validation(f"Missing required field '{key}'.")
    try:
        return RequiredIntValueModel.model_validate({"value": payload[key]}).value
    except ValidationError as exc:
        _raise_validation(f"'{key}' must be an integer.", exc)


def parse_state_value(payload: Mapping[str, object], rule: AutomatonRule, key: str = "state") -> int:
    if key not in payload:
        _raise_validation(f"Missing required field '{key}'.")
    try:
        parsed = StateValueModel.model_validate({"value": payload[key]}).value
    except ValidationError as exc:
        _raise_validation(f"'{key}' must be a valid state value.", exc)

    if not rule.is_valid_state(parsed):
        _raise_validation(f"'{key}' must be one of the states supported by rule '{rule.name}'.")
    return parsed


def parse_cell_id(payload: Mapping[str, object], key: str = "id") -> str:
    value = payload.get(key)
    if value in (None, ""):
        _raise_validation(f"Missing required field '{key}'.")
    try:
        return CellIdValueModel.model_validate({"value": value}).value
    except ValidationError as exc:
        _raise_validation(f"'{key}' must be a string.", exc)


def parse_cell_target(
    payload: Mapping[str, object],
    *,
    id_key: str = "id",
) -> CellTargetPayload:
    if payload.get(id_key) in (None, ""):
        _raise_validation(f"Missing required field '{id_key}'.")
    try:
        id_target = IdCellTargetModel.model_validate({id_key: payload.get(id_key)})
    except ValidationError as exc:
        _raise_validation(f"'{id_key}' must be a string.", exc)
    return id_target.to_payload()


def parse_cell_updates(
    payload: Mapping[str, object],
    rule: AutomatonRule,
    key: str = "cells",
) -> list[CellUpdatePayload]:
    try:
        raw_cells = CellUpdatesPayloadModel.model_validate(payload).cells
    except ValidationError as exc:
        _raise_validation(f"'{key}' must be a non-empty list.", exc)

    parsed_cells: list[CellUpdatePayload] = []
    for index, cell in enumerate(raw_cells):
        parsed_state = parse_state_value({"state": cell.state}, rule, "state")
        if not isinstance(cell.id, str) or cell.id == "":
            _raise_validation(f"'{key}[{index}].id' must be a string.")
        parsed_cells.append({"id": cell.id, "state": parsed_state})

    return parsed_cells


def parse_rule_name(payload: Mapping[str, object], rule_registry: RuleRegistry) -> str | None:
    try:
        rule_name = RuleNameValueModel.model_validate({"value": payload.get("rule")}).value
    except ValidationError as exc:
        _raise_validation("'rule' must reference a known rule module.", exc)
    if rule_name is None:
        return None
    if not rule_registry.has(rule_name):
        _raise_validation("'rule' must reference a known rule module.")
    return rule_name


def parse_topology_spec(
    payload: Mapping[str, object],
    key: str = "topology_spec",
) -> TopologySpecRequestPayload | None:
    try:
        topology_spec = TopologySpecValueModel.model_validate(payload.get(key) or {})
    except ValidationError as exc:
        supported = ", ".join(SUPPORTED_TOPOLOGY_FAMILIES)
        _raise_validation(f"'{key}.tiling_family' must be one of: {supported}.", exc)
    if payload.get(key) in (None, ""):
        return None
    tiling_family = topology_spec.tiling_family
    if tiling_family is None or tiling_family not in SUPPORTED_TOPOLOGY_FAMILIES:
        supported = ", ".join(SUPPORTED_TOPOLOGY_FAMILIES)
        _raise_validation(f"'{key}.tiling_family' must be one of: {supported}.")
    definition = get_topology_definition(tiling_family)
    adjacency_mode = normalize_adjacency_mode(tiling_family, topology_spec.adjacency_mode)
    topology_spec_payload = topology_spec.to_payload()
    topology_spec_payload["tiling_family"] = tiling_family
    topology_spec_payload["adjacency_mode"] = adjacency_mode
    topology_spec_payload["sizing_mode"] = definition.sizing_mode
    return topology_spec_payload
