from __future__ import annotations

from backend.payload_types import (
    ApiErrorPayload,
    CellStatePayload,
    JsonObject,
    RuleDefinitionPayload,
    RulesResponsePayload,
    ServerMetaPayload,
    SimulationStatePayload,
    TopologyCellPayload,
    TopologyPayload,
    TopologySpecPayload,
)


def _require_json_object(value: object, *, context: str) -> JsonObject:
    if not isinstance(value, dict):
        raise AssertionError(f"{context} must be a JSON object.")
    return value


def _require_json_list(value: object, *, context: str) -> list[object]:
    if not isinstance(value, list):
        raise AssertionError(f"{context} must be a JSON array.")
    return value


def _require_str(value: object, *, context: str) -> str:
    if not isinstance(value, str):
        raise AssertionError(f"{context} must be a string.")
    return value


def _require_int(value: object, *, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AssertionError(f"{context} must be an integer.")
    return value


def _require_bool(value: object, *, context: str) -> bool:
    if not isinstance(value, bool):
        raise AssertionError(f"{context} must be a boolean.")
    return value


def _require_float(value: object, *, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AssertionError(f"{context} must be numeric.")
    return float(value)


def require_topology_spec_payload(value: object, *, context: str) -> TopologySpecPayload:
    payload = _require_json_object(value, context=context)
    return {
        "tiling_family": _require_str(payload.get("tiling_family"), context=f"{context}.tiling_family"),
        "adjacency_mode": _require_str(payload.get("adjacency_mode"), context=f"{context}.adjacency_mode"),
        "sizing_mode": _require_str(payload.get("sizing_mode"), context=f"{context}.sizing_mode"),
        "width": _require_int(payload.get("width"), context=f"{context}.width"),
        "height": _require_int(payload.get("height"), context=f"{context}.height"),
        "patch_depth": _require_int(payload.get("patch_depth"), context=f"{context}.patch_depth"),
    }


def require_cell_state_payload(value: object, *, context: str) -> CellStatePayload:
    payload = _require_json_object(value, context=context)
    return {
        "value": _require_int(payload.get("value"), context=f"{context}.value"),
        "label": _require_str(payload.get("label"), context=f"{context}.label"),
        "color": _require_str(payload.get("color"), context=f"{context}.color"),
        "paintable": _require_bool(payload.get("paintable"), context=f"{context}.paintable"),
    }


def require_rule_definition_payload(value: object, *, context: str) -> RuleDefinitionPayload:
    payload = _require_json_object(value, context=context)
    states = _require_json_list(payload.get("states"), context=f"{context}.states")
    return {
        "name": _require_str(payload.get("name"), context=f"{context}.name"),
        "display_name": _require_str(payload.get("display_name"), context=f"{context}.display_name"),
        "description": _require_str(payload.get("description"), context=f"{context}.description"),
        "states": [
            require_cell_state_payload(state, context=f"{context}.states[{index}]")
            for index, state in enumerate(states)
        ],
        "default_paint_state": _require_int(
            payload.get("default_paint_state"),
            context=f"{context}.default_paint_state",
        ),
        "supports_randomize": _require_bool(
            payload.get("supports_randomize"),
            context=f"{context}.supports_randomize",
        ),
        "rule_protocol": _require_str(payload.get("rule_protocol"), context=f"{context}.rule_protocol"),
        "supports_all_topologies": _require_bool(
            payload.get("supports_all_topologies"),
            context=f"{context}.supports_all_topologies",
        ),
    }


def require_topology_cell_payload(value: object, *, context: str) -> TopologyCellPayload:
    payload = _require_json_object(value, context=context)
    neighbors = _require_json_list(payload.get("neighbors"), context=f"{context}.neighbors")
    normalized_payload: TopologyCellPayload = {
        "id": _require_str(payload.get("id"), context=f"{context}.id"),
        "kind": _require_str(payload.get("kind"), context=f"{context}.kind"),
        "neighbors": [
            None if neighbor is None else _require_str(neighbor, context=f"{context}.neighbors[{index}]")
            for index, neighbor in enumerate(neighbors)
        ],
    }
    slot = payload.get("slot")
    if slot is not None:
        normalized_payload["slot"] = _require_str(slot, context=f"{context}.slot")
    center = payload.get("center")
    if center is not None:
        center_payload = _require_json_object(center, context=f"{context}.center")
        normalized_payload["center"] = {
            "x": _require_float(center_payload.get("x"), context=f"{context}.center.x"),
            "y": _require_float(center_payload.get("y"), context=f"{context}.center.y"),
        }
    vertices = payload.get("vertices")
    if vertices is not None:
        vertices_payload = _require_json_list(vertices, context=f"{context}.vertices")
        normalized_payload["vertices"] = [
            {
                "x": _require_float(
                    _require_json_object(vertex, context=f"{context}.vertices[{index}]").get("x"),
                    context=f"{context}.vertices[{index}].x",
                ),
                "y": _require_float(
                    _require_json_object(vertex, context=f"{context}.vertices[{index}]").get("y"),
                    context=f"{context}.vertices[{index}].y",
                ),
            }
            for index, vertex in enumerate(vertices_payload)
        ]
    return normalized_payload


def require_topology_payload(value: object, *, context: str) -> TopologyPayload:
    payload = _require_json_object(value, context=context)
    cells = _require_json_list(payload.get("cells"), context=f"{context}.cells")
    return {
        "topology_spec": require_topology_spec_payload(
            payload.get("topology_spec"),
            context=f"{context}.topology_spec",
        ),
        "topology_revision": _require_str(
            payload.get("topology_revision"),
            context=f"{context}.topology_revision",
        ),
        "cells": [
            require_topology_cell_payload(cell, context=f"{context}.cells[{index}]")
            for index, cell in enumerate(cells)
        ],
    }


def require_simulation_state_payload(value: object, *, context: str) -> SimulationStatePayload:
    payload = _require_json_object(value, context=context)
    cell_states = _require_json_list(payload.get("cell_states"), context=f"{context}.cell_states")
    normalized_payload: SimulationStatePayload = {
        "topology_spec": require_topology_spec_payload(
            payload.get("topology_spec"),
            context=f"{context}.topology_spec",
        ),
        "speed": _require_float(payload.get("speed"), context=f"{context}.speed"),
        "running": _require_bool(payload.get("running"), context=f"{context}.running"),
        "generation": _require_int(payload.get("generation"), context=f"{context}.generation"),
        "rule": require_rule_definition_payload(payload.get("rule"), context=f"{context}.rule"),
        "topology_revision": _require_str(
            payload.get("topology_revision"),
            context=f"{context}.topology_revision",
        ),
        "cell_states": [
            _require_int(cell_state, context=f"{context}.cell_states[{index}]")
            for index, cell_state in enumerate(cell_states)
        ],
    }
    topology = payload.get("topology")
    if topology is not None:
        normalized_payload["topology"] = require_topology_payload(
            topology,
            context=f"{context}.topology",
        )
    return normalized_payload


def require_rules_response_payload(value: object, *, context: str) -> RulesResponsePayload:
    payload = _require_json_object(value, context=context)
    rules = _require_json_list(payload.get("rules"), context=f"{context}.rules")
    return {
        "rules": [
            require_rule_definition_payload(rule, context=f"{context}.rules[{index}]")
            for index, rule in enumerate(rules)
        ]
    }


def require_api_error_payload(value: object, *, context: str) -> ApiErrorPayload:
    payload = _require_json_object(value, context=context)
    return {
        "error": _require_str(payload.get("error"), context=f"{context}.error"),
    }


def require_server_meta_payload(value: object, *, context: str) -> ServerMetaPayload:
    payload = _require_json_object(value, context=context)
    return {
        "app_name": _require_str(payload.get("app_name"), context=f"{context}.app_name"),
    }
