from __future__ import annotations

from typing import Any, NoReturn

from flask import Request
from pydantic import ValidationError

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
    IdCellUpdateModel,
    OptionalFloatValueModel,
    OptionalIntValueModel,
    RequiredIntValueModel,
    RuleNameValueModel,
    StateValueModel,
    TopologySpecValueModel,
)


class RequestValidationError(ValueError):
    """Raised when an API request payload is malformed."""


def get_payload(request: Request) -> dict[str, Any]:
    payload = request.get_json(silent=True)
    return payload if isinstance(payload, dict) else {}


def _raise_validation(message: str, exc: Exception | None = None) -> NoReturn:
    if exc is None:
        raise RequestValidationError(message)
    raise RequestValidationError(message) from exc


def parse_optional_int(payload: dict[str, Any], key: str) -> int | None:
    try:
        return OptionalIntValueModel.model_validate({"value": payload.get(key)}).value
    except ValidationError as exc:
        _raise_validation(f"'{key}' must be an integer.", exc)


def parse_optional_float(payload: dict[str, Any], key: str) -> float | None:
    try:
        return OptionalFloatValueModel.model_validate({"value": payload.get(key)}).value
    except ValidationError as exc:
        _raise_validation(f"'{key}' must be a number.", exc)


def parse_required_int(payload: dict[str, Any], key: str) -> int:
    if key not in payload:
        _raise_validation(f"Missing required field '{key}'.")
    try:
        return RequiredIntValueModel.model_validate({"value": payload[key]}).value
    except ValidationError as exc:
        _raise_validation(f"'{key}' must be an integer.", exc)


def parse_state_value(payload: dict[str, Any], rule: AutomatonRule, key: str = "state") -> int:
    if key not in payload:
        _raise_validation(f"Missing required field '{key}'.")
    try:
        parsed = StateValueModel.model_validate({"value": payload[key]}).value
    except ValidationError as exc:
        _raise_validation(f"'{key}' must be a valid state value.", exc)

    if not rule.is_valid_state(parsed):
        _raise_validation(f"'{key}' must be one of the states supported by rule '{rule.name}'.")
    return parsed


def parse_cell_id(payload: dict[str, Any], key: str = "id") -> str:
    value = payload.get(key)
    if value in (None, ""):
        _raise_validation(f"Missing required field '{key}'.")
    try:
        return CellIdValueModel.model_validate({"value": value}).value
    except ValidationError as exc:
        _raise_validation(f"'{key}' must be a string.", exc)


def parse_cell_target(
    payload: dict[str, Any],
    *,
    id_key: str = "id",
) -> dict[str, str]:
    if payload.get(id_key) in (None, ""):
        _raise_validation(f"Missing required field '{id_key}'.")
    try:
        id_target = IdCellTargetModel.model_validate({id_key: payload.get(id_key)})
    except ValidationError as exc:
        _raise_validation(f"'{id_key}' must be a string.", exc)
    return {"id": id_target.id}


def parse_cell_updates(
    payload: dict[str, Any],
    rule: AutomatonRule,
    key: str = "cells",
) -> list[dict[str, int | str]]:
    try:
        raw_cells = CellUpdatesPayloadModel.model_validate(payload).cells
    except ValidationError as exc:
        _raise_validation(f"'{key}' must be a non-empty list.", exc)

    parsed_cells: list[dict[str, int | str]] = []
    for index, cell in enumerate(raw_cells):
        if not isinstance(cell, dict):
            _raise_validation(f"'{key}[{index}]' must be an object.")
        parsed_state = parse_state_value(cell, rule, "state")
        try:
            parsed_id_cell = IdCellUpdateModel.model_validate({
                "id": cell.get("id"),
                "state": cell.get("state"),
            })
            parsed_cells.append({"id": parsed_id_cell.id, "state": parsed_state})
        except ValidationError:
            parsed_cells.append(
                {
                    **parse_cell_target(cell),
                    "state": parsed_state,
                }
            )

    return parsed_cells


def parse_rule_name(payload: dict[str, Any], rule_registry: RuleRegistry) -> str | None:
    try:
        rule_name = RuleNameValueModel.model_validate({"value": payload.get("rule")}).value
    except ValidationError as exc:
        _raise_validation("'rule' must reference a known rule module.", exc)
    if rule_name is None:
        return None
    if not rule_registry.has(rule_name):
        _raise_validation("'rule' must reference a known rule module.")
    return rule_name


def parse_topology_spec(payload: dict[str, Any], key: str = "topology_spec") -> dict[str, Any] | None:
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
    return {
        "tiling_family": tiling_family,
        "adjacency_mode": adjacency_mode,
        "sizing_mode": definition.sizing_mode,
        "width": topology_spec.width,
        "height": topology_spec.height,
        "patch_depth": topology_spec.patch_depth,
    }
