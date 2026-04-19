from __future__ import annotations

from dataclasses import dataclass


DOMAIN_FRONTEND_PATH = "frontend/types/domain.d.ts"
CONTROLLER_API_FRONTEND_PATH = "frontend/types/controller-api.d.ts"
STANDALONE_PROTOCOL_FRONTEND_PATH = "frontend/standalone/protocol.ts"


@dataclass(frozen=True)
class PayloadFieldContract:
    interface_name: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...] = ()
    frontend_path: str = DOMAIN_FRONTEND_PATH

    @property
    def all_fields(self) -> tuple[str, ...]:
        return (*self.required_fields, *self.optional_fields)


@dataclass(frozen=True)
class PayloadTypeUnionContract:
    type_name: str
    members: tuple[str, ...]
    frontend_path: str
    host_interface_name: str | None = None
    host_property_name: str | None = None


PAYLOAD_FIELD_CONTRACTS: tuple[PayloadFieldContract, ...] = (
    PayloadFieldContract(
        interface_name="BootstrappedAperiodicFamilyDefinition",
        required_fields=("tiling_family", "label", "experimental", "public_cell_kinds"),
    ),
    PayloadFieldContract(
        interface_name="AppBootstrapData",
        required_fields=(
            "app_defaults",
            "topology_catalog",
            "periodic_face_tilings",
            "aperiodic_families",
            "server_meta",
            "snapshot_version",
        ),
    ),
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
    PayloadFieldContract(
        interface_name="ConfigTopologySpecPatch",
        required_fields=(),
        optional_fields=("width", "height", "unsafe_size_override"),
        frontend_path=CONTROLLER_API_FRONTEND_PATH,
    ),
    PayloadFieldContract(
        interface_name="ResetTopologySpec",
        required_fields=(
            "tiling_family",
            "adjacency_mode",
            "sizing_mode",
            "width",
            "height",
            "patch_depth",
        ),
        optional_fields=("unsafe_size_override",),
        frontend_path=CONTROLLER_API_FRONTEND_PATH,
    ),
    PayloadFieldContract(
        interface_name="ConfigSyncBody",
        required_fields=(),
        optional_fields=("topology_spec", "speed", "rule"),
        frontend_path=CONTROLLER_API_FRONTEND_PATH,
    ),
    PayloadFieldContract(
        interface_name="ResetControlBody",
        required_fields=("topology_spec", "speed", "rule", "randomize"),
        frontend_path=CONTROLLER_API_FRONTEND_PATH,
    ),
    PayloadFieldContract(
        interface_name="CellTargetRequest",
        required_fields=("id",),
        frontend_path=CONTROLLER_API_FRONTEND_PATH,
    ),
    PayloadFieldContract(
        interface_name="CellUpdateRequest",
        required_fields=("id", "state"),
        frontend_path=CONTROLLER_API_FRONTEND_PATH,
    ),
    PayloadFieldContract(
        interface_name="CellUpdatesRequest",
        required_fields=("cells",),
        frontend_path=CONTROLLER_API_FRONTEND_PATH,
    ),
)

PAYLOAD_TYPE_UNION_CONTRACTS: tuple[PayloadTypeUnionContract, ...] = (
    PayloadTypeUnionContract(
        type_name="StandaloneRequestPayload",
        members=(
            "ResetControlBody",
            "ConfigSyncBody",
            "CellTargetRequest",
            "CellUpdateRequest",
            "CellUpdatesRequest",
        ),
        frontend_path=STANDALONE_PROTOCOL_FRONTEND_PATH,
        host_interface_name="StandaloneRequestMessage",
        host_property_name="payload",
    ),
)


def payload_field_contracts() -> tuple[PayloadFieldContract, ...]:
    return PAYLOAD_FIELD_CONTRACTS


def payload_type_union_contracts() -> tuple[PayloadTypeUnionContract, ...]:
    return PAYLOAD_TYPE_UNION_CONTRACTS


__all__ = [
    "CONTROLLER_API_FRONTEND_PATH",
    "DOMAIN_FRONTEND_PATH",
    "PAYLOAD_FIELD_CONTRACTS",
    "PAYLOAD_TYPE_UNION_CONTRACTS",
    "PayloadFieldContract",
    "PayloadTypeUnionContract",
    "STANDALONE_PROTOCOL_FRONTEND_PATH",
    "payload_field_contracts",
    "payload_type_union_contracts",
]
