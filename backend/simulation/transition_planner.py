from __future__ import annotations

from dataclasses import dataclass

from backend.defaults import DEFAULT_PATCH_DEPTH, DEFAULT_TILING_FAMILY
from backend.payload_types import (
    PersistedSimulationSnapshotInput,
    TopologySpecInput,
    TopologySpecPatch,
)
from backend.rules import RuleRegistry
from backend.rules.base import AutomatonRule
from backend.rules.constraints import normalize_rule_dimensions
from backend.simulation.models import SimulationConfig, SimulationStateData, TopologySpec
from backend.simulation.topology_catalog import (
    SUPPORTED_TOPOLOGY_FAMILIES,
    geometry_uses_backend_viewport_sync,
    geometry_uses_patch_depth,
    normalize_adjacency_mode,
    resolve_geometry_key,
)


@dataclass(frozen=True)
class ResetTransitionPlan:
    config: SimulationConfig
    rule: AutomatonRule
    board_mode: str


@dataclass(frozen=True)
class ConfigTransitionPlan:
    config: SimulationConfig
    rule: AutomatonRule
    board_mode: str
    coerce_rule_states: bool


@dataclass(frozen=True)
class RestoreTransitionPlan:
    config: SimulationConfig
    rule: AutomatonRule
    generation: int
    board_payload_kind: str


def _coerce_int(value: object, fallback: int) -> int:
    if value is None:
        return fallback
    if not isinstance(value, (str, bytes, bytearray, int, float)):
        return fallback
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _coerce_float(value: object, fallback: float) -> float:
    if value is None:
        return fallback
    if not isinstance(value, (str, bytes, bytearray, int, float)):
        return fallback
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _resolve_reset_rule(
    *,
    rule_registry: RuleRegistry,
    current_rule: AutomatonRule,
    current_geometry: str,
    next_geometry: str,
    rule_name: str | None,
) -> AutomatonRule:
    geometry_changed = next_geometry != current_geometry
    if rule_name is not None:
        return rule_registry.get(rule_name)
    if geometry_changed:
        return rule_registry.default_for_geometry(next_geometry)
    return current_rule


def plan_reset_transition(
    current_state: SimulationStateData,
    rule_registry: RuleRegistry,
    *,
    topology_spec: TopologySpec | TopologySpecInput | None = None,
    rule_name: str | None = None,
    speed: float | None = None,
    randomize: bool = False,
) -> ResetTransitionPlan:
    next_topology_spec = current_state.config.updated(
        topology_spec=topology_spec,
    ).topology_spec if topology_spec is not None else current_state.config.topology_spec
    next_geometry = next_topology_spec.geometry_key
    next_rule = _resolve_reset_rule(
        rule_registry=rule_registry,
        current_rule=current_state.rule,
        current_geometry=current_state.config.geometry,
        next_geometry=next_geometry,
        rule_name=rule_name,
    )
    next_width, next_height = normalize_rule_dimensions(
        next_rule,
        next_topology_spec.width,
        next_topology_spec.height,
    )
    next_config = SimulationConfig.from_values(
        topology_spec=next_topology_spec.updated(
            width=next_width,
            height=next_height,
        ),
        speed=current_state.config.speed if speed is None else speed,
    )
    return ResetTransitionPlan(
        config=next_config,
        rule=next_rule,
        board_mode="randomize" if randomize else "empty",
    )


def plan_config_transition(
    current_state: SimulationStateData,
    rule_registry: RuleRegistry,
    *,
    topology_spec: TopologySpecPatch | None = None,
    speed: float | None = None,
    rule_name: str | None = None,
) -> ConfigTransitionPlan:
    next_rule = current_state.rule
    if rule_name is not None:
        next_rule = rule_registry.get(rule_name)

    next_width = (
        topology_spec.get("width")
        if topology_spec is not None and geometry_uses_backend_viewport_sync(current_state.config.geometry)
        else None
    )
    next_height = (
        topology_spec.get("height")
        if topology_spec is not None and geometry_uses_backend_viewport_sync(current_state.config.geometry)
        else None
    )
    normalized_width, normalized_height = normalize_rule_dimensions(
        next_rule,
        current_state.config.width if next_width is None else next_width,
        current_state.config.height if next_height is None else next_height,
    )
    next_config = current_state.config.updated(
        width=normalized_width,
        height=normalized_height,
        speed=speed,
    )
    resize = (
        geometry_uses_backend_viewport_sync(current_state.config.geometry)
        and (
            next_config.width != current_state.config.width
            or next_config.height != current_state.config.height
        )
    )
    return ConfigTransitionPlan(
        config=next_config,
        rule=next_rule,
        board_mode="transfer" if resize else "reuse",
        coerce_rule_states=next_rule is not current_state.rule,
    )


def _resolve_restore_topology_spec(payload: PersistedSimulationSnapshotInput) -> TopologySpec:
    topology_spec = payload.get("topology_spec")
    if not isinstance(topology_spec, dict):
        return TopologySpec()
    tiling_family = str(topology_spec.get("tiling_family") or DEFAULT_TILING_FAMILY)
    if tiling_family not in SUPPORTED_TOPOLOGY_FAMILIES:
        return TopologySpec()
    adjacency_mode = normalize_adjacency_mode(tiling_family, topology_spec.get("adjacency_mode"))
    return TopologySpec.from_values(
        tiling_family=tiling_family,
        adjacency_mode=adjacency_mode,
        width=_coerce_int(topology_spec.get("width"), 1),
        height=_coerce_int(topology_spec.get("height"), 1),
        patch_depth=_coerce_int(topology_spec.get("patch_depth"), DEFAULT_PATCH_DEPTH),
    )


def _resolve_restore_rule(rule_registry: RuleRegistry, rule_name: str | None, geometry: str) -> AutomatonRule:
    if rule_name is not None and rule_registry.has(rule_name):
        return rule_registry.get(rule_name)
    return rule_registry.default_for_geometry(geometry)


def _restore_rule_name(payload: PersistedSimulationSnapshotInput) -> str | None:
    rule_name = payload.get("rule")
    return rule_name if isinstance(rule_name, str) else None


def _restore_board_payload_kind(payload: PersistedSimulationSnapshotInput) -> str:
    if isinstance(payload.get("cells_by_id"), dict):
        return "cells_by_id"
    return "empty"


def plan_restore_transition(
    payload: PersistedSimulationSnapshotInput,
    *,
    fallback_state: SimulationStateData,
    rule_registry: RuleRegistry,
) -> RestoreTransitionPlan:
    restored_topology_spec = _resolve_restore_topology_spec(payload)
    next_geometry = resolve_geometry_key(
        restored_topology_spec.tiling_family,
        restored_topology_spec.adjacency_mode,
    )
    next_rule = _resolve_restore_rule(rule_registry, _restore_rule_name(payload), next_geometry)
    next_patch_depth = _coerce_int(
        restored_topology_spec.patch_depth,
        fallback_state.config.patch_depth if geometry_uses_patch_depth(next_geometry) else DEFAULT_PATCH_DEPTH,
    )
    next_width = _coerce_int(restored_topology_spec.width, fallback_state.config.width)
    next_height = _coerce_int(restored_topology_spec.height, fallback_state.config.height)
    normalized_width, normalized_height = normalize_rule_dimensions(next_rule, next_width, next_height)
    next_width = next_width if normalized_width is None else normalized_width
    next_height = next_height if normalized_height is None else normalized_height
    next_config = SimulationConfig.from_values(
        topology_spec=restored_topology_spec.updated(
            width=next_width,
            height=next_height,
            patch_depth=next_patch_depth,
        ),
        width=next_width,
        height=next_height,
        speed=_coerce_float(payload.get("speed"), fallback_state.config.speed),
    )
    return RestoreTransitionPlan(
        config=next_config,
        rule=next_rule,
        generation=max(0, _coerce_int(payload.get("generation"), 0)),
        board_payload_kind=_restore_board_payload_kind(payload),
    )
