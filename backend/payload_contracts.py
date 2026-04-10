from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PayloadFieldContract:
    interface_name: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...] = ()

    @property
    def all_fields(self) -> tuple[str, ...]:
        return (*self.required_fields, *self.optional_fields)


PAYLOAD_FIELD_CONTRACTS: tuple[PayloadFieldContract, ...] = (
    PayloadFieldContract(
        interface_name="TopologySpec",
        required_fields=(
            "tiling_family",
            "adjacency_mode",
            "sizing_mode",
            "width",
            "height",
            "patch_depth",
        ),
    ),
    PayloadFieldContract(
        interface_name="ApiTopologyCellPayload",
        required_fields=("id", "kind", "neighbors"),
        optional_fields=(
            "slot",
            "center",
            "vertices",
            "tile_family",
            "orientation_token",
            "chirality_token",
            "decoration_tokens",
        ),
    ),
    PayloadFieldContract(
        interface_name="ApiTopologyPayload",
        required_fields=("topology_revision", "topology_spec", "cells"),
    ),
    PayloadFieldContract(
        interface_name="ApiRuleDefinition",
        required_fields=(
            "name",
            "display_name",
            "description",
            "default_paint_state",
            "supports_randomize",
            "states",
            "rule_protocol",
            "supports_all_topologies",
        ),
    ),
    PayloadFieldContract(
        interface_name="PatternPayload",
        required_fields=("format", "version", "topology_spec", "rule", "cells_by_id"),
    ),
)


def payload_field_contracts() -> tuple[PayloadFieldContract, ...]:
    return PAYLOAD_FIELD_CONTRACTS


__all__ = [
    "PAYLOAD_FIELD_CONTRACTS",
    "PayloadFieldContract",
    "payload_field_contracts",
]
