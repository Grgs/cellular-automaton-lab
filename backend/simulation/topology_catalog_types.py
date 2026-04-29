from __future__ import annotations

from dataclasses import dataclass

from backend.payload_types import (
    SizingPolicyPayload,
    TopologyCatalogEntryPayload,
    TopologyVariantPayload,
)


@dataclass(frozen=True)
class TopologyVariantDefinition:
    geometry_key: str
    tiling_family: str
    adjacency_mode: str
    label: str
    picker_group: str
    picker_order: int
    default_rule: str
    sizing_mode: str
    family: str
    viewport_sync_mode: str

    @property
    def id(self) -> str:
        return self.geometry_key

    def to_dict(self) -> TopologyVariantPayload:
        return {
            "id": self.geometry_key,
            "geometry_key": self.geometry_key,
            "tiling_family": self.tiling_family,
            "adjacency_mode": self.adjacency_mode,
            "label": self.label,
            "picker_group": self.picker_group,
            "picker_order": self.picker_order,
            "default_rule": self.default_rule,
            "sizing_mode": self.sizing_mode,
            "family": self.family,
            "viewport_sync_mode": self.viewport_sync_mode,
        }


@dataclass(frozen=True)
class SizingPolicyDefinition:
    control: str
    default: int
    minimum: int
    maximum: int
    unsafe_maximum: int | None = None

    def to_dict(self) -> SizingPolicyPayload:
        payload: SizingPolicyPayload = {
            "control": self.control,
            "default": self.default,
            "min": self.minimum,
            "max": self.maximum,
        }
        if self.unsafe_maximum is not None:
            payload["unsafe_max"] = self.unsafe_maximum
        return payload


@dataclass(frozen=True)
class TopologyDefinition:
    tiling_family: str
    label: str
    picker_group: str
    picker_order: int
    sizing_mode: str
    family: str
    render_kind: str
    viewport_sync_mode: str
    supported_adjacency_modes: tuple[str, ...]
    default_adjacency_mode: str
    default_rules: dict[str, str]
    geometry_keys: dict[str, str]
    sizing_policy: SizingPolicyDefinition

    def to_dict(self) -> TopologyCatalogEntryPayload:
        return {
            "tiling_family": self.tiling_family,
            "label": self.label,
            "picker_group": self.picker_group,
            "picker_order": self.picker_order,
            "sizing_mode": self.sizing_mode,
            "family": self.family,
            "render_kind": self.render_kind,
            "viewport_sync_mode": self.viewport_sync_mode,
            "supported_adjacency_modes": list(self.supported_adjacency_modes),
            "default_adjacency_mode": self.default_adjacency_mode,
            "default_rules": dict(self.default_rules),
            "geometry_keys": dict(self.geometry_keys),
            "sizing_policy": self.sizing_policy.to_dict(),
        }
