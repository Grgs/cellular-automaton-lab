from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend import payload_types


DOMAIN_FRONTEND_PATH = "frontend/types/domain.d.ts"
CONTROLLER_API_FRONTEND_PATH = "frontend/types/controller-api.d.ts"
STANDALONE_PROTOCOL_FRONTEND_PATH = "frontend/standalone/protocol.ts"
RENDERING_FRONTEND_PATH = "frontend/types/rendering.d.ts"
CONTROLLER_VIEW_FRONTEND_PATH = "frontend/types/controller-view.d.ts"
CONTROLLER_SYNC_SESSION_FRONTEND_PATH = "frontend/types/controller-sync-session.d.ts"
EDITOR_FRONTEND_PATH = "frontend/types/editor.d.ts"
ACTIONS_FRONTEND_PATH = "frontend/types/actions.d.ts"


def _typed_dict_by_name(type_name: str) -> type[Any]:
    try:
        typed_dict = getattr(payload_types, type_name)
    except AttributeError as error:
        raise AssertionError(f"Missing backend payload type {type_name!r}.") from error
    if not isinstance(typed_dict, type):
        raise AssertionError(f"Backend payload type {type_name!r} is not a class.")
    if not hasattr(typed_dict, "__required_keys__") or not hasattr(typed_dict, "__optional_keys__"):
        raise AssertionError(f"Backend payload type {type_name!r} is not a TypedDict.")
    return typed_dict


def _typed_dict_annotations(typed_dict: type[Any]) -> dict[str, object]:
    ordered_annotations: dict[str, object] = {}
    for base in reversed(typed_dict.__mro__):
        if base in {dict, object}:
            continue
        annotations = getattr(base, "__annotations__", None)
        if annotations:
            ordered_annotations.update(annotations)
    return ordered_annotations


def _ordered_typed_dict_fields(type_name: str, *, required: bool) -> tuple[str, ...]:
    typed_dict = _typed_dict_by_name(type_name)
    keys = typed_dict.__required_keys__ if required else typed_dict.__optional_keys__
    annotations = _typed_dict_annotations(typed_dict)
    return tuple(name for name in annotations if name in keys)


@dataclass(frozen=True)
class PayloadFieldContract:
    backend_type_name: str
    interface_name: str
    frontend_path: str = DOMAIN_FRONTEND_PATH

    @property
    def required_fields(self) -> tuple[str, ...]:
        return _ordered_typed_dict_fields(self.backend_type_name, required=True)

    @property
    def optional_fields(self) -> tuple[str, ...]:
        return _ordered_typed_dict_fields(self.backend_type_name, required=False)

    @property
    def all_fields(self) -> tuple[str, ...]:
        return (*self.required_fields, *self.optional_fields)


@dataclass(frozen=True)
class FrontendPropertyTypeContract:
    interface_name: str
    property_name: str
    property_type: str
    frontend_path: str


@dataclass(frozen=True)
class FrontendTypeAliasContract:
    type_name: str
    type_body: str
    frontend_path: str


@dataclass(frozen=True)
class PayloadTypeUnionContract:
    type_name: str
    members: tuple[str, ...]
    frontend_path: str
    host_interface_name: str | None = None
    host_property_name: str | None = None


PAYLOAD_FIELD_CONTRACTS: tuple[PayloadFieldContract, ...] = (
    PayloadFieldContract("TopologySpecPayload", "TopologySpec"),
    PayloadFieldContract("SimulationDefaultsPayload", "SimulationDefaults"),
    PayloadFieldContract("UiDefaultsPayload", "UiDefaults"),
    PayloadFieldContract("ThemeDefaultsPayload", "ThemeDefaults"),
    PayloadFieldContract("AppDefaultsPayload", "FrontendDefaults"),
    PayloadFieldContract("ServerMetaPayload", "ServerMetaPayload"),
    PayloadFieldContract(
        "AperiodicFamilyBootstrapPayload", "BootstrappedAperiodicFamilyDefinition"
    ),
    PayloadFieldContract("AppBootstrapPayload", "AppBootstrapData"),
    PayloadFieldContract("SizingPolicyPayload", "SizingPolicy"),
    PayloadFieldContract("TopologyCatalogEntryPayload", "BootstrappedTopologyDefinition"),
    PayloadFieldContract(
        "PeriodicFaceTilingDescriptorPayload",
        "PeriodicFaceTilingDescriptor",
        frontend_path=RENDERING_FRONTEND_PATH,
    ),
    PayloadFieldContract("PointPayload", "PointPayload"),
    PayloadFieldContract("TopologyCellPayload", "ApiTopologyCellPayload"),
    PayloadFieldContract("TopologyPayload", "ApiTopologyPayload"),
    PayloadFieldContract("CellStatePayload", "CellStateDefinition"),
    PayloadFieldContract("RuleDefinitionPayload", "ApiRuleDefinition"),
    PayloadFieldContract("RulesResponsePayload", "RulesResponse"),
    PayloadFieldContract("SimulationStatePayload", "ApiSimulationSnapshot"),
    PayloadFieldContract("PersistedSimulationSnapshotV5", "PersistedSimulationSnapshotV5"),
    PayloadFieldContract("PatternPayload", "PatternPayload"),
    PayloadFieldContract(
        "ConfigTopologySpecPatchPayload",
        "ConfigTopologySpecPatch",
        frontend_path=CONTROLLER_API_FRONTEND_PATH,
    ),
    PayloadFieldContract(
        "ResetTopologySpecPayload",
        "ResetTopologySpec",
        frontend_path=CONTROLLER_API_FRONTEND_PATH,
    ),
    PayloadFieldContract(
        "ConfigSyncRequestPayload",
        "ConfigSyncBody",
        frontend_path=CONTROLLER_API_FRONTEND_PATH,
    ),
    PayloadFieldContract(
        "ResetControlRequestPayload",
        "ResetControlBody",
        frontend_path=CONTROLLER_API_FRONTEND_PATH,
    ),
    PayloadFieldContract(
        "CellTargetPayload",
        "CellTargetRequest",
        frontend_path=CONTROLLER_API_FRONTEND_PATH,
    ),
    PayloadFieldContract(
        "CellUpdatePayload",
        "CellUpdateRequest",
        frontend_path=CONTROLLER_API_FRONTEND_PATH,
    ),
    PayloadFieldContract(
        "CellUpdatesRequestPayload",
        "CellUpdatesRequest",
        frontend_path=CONTROLLER_API_FRONTEND_PATH,
    ),
)

FRONTEND_PROPERTY_TYPE_CONTRACTS: tuple[FrontendPropertyTypeContract, ...] = (
    FrontendPropertyTypeContract(
        interface_name="AppBootstrapData",
        property_name="app_defaults",
        property_type="BootstrappedFrontendDefaults",
        frontend_path=DOMAIN_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="AppBootstrapData",
        property_name="topology_catalog",
        property_type="ReadonlyArray<BootstrappedTopologyDefinition>",
        frontend_path=DOMAIN_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="AppBootstrapData",
        property_name="periodic_face_tilings",
        property_type="ReadonlyArray<PeriodicFaceTilingDescriptor>",
        frontend_path=DOMAIN_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="AppBootstrapData",
        property_name="aperiodic_families",
        property_type="ReadonlyArray<BootstrappedAperiodicFamilyDefinition>",
        frontend_path=DOMAIN_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="ApiTopologyPayload",
        property_name="topology_spec",
        property_type="TopologySpec",
        frontend_path=DOMAIN_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="ApiTopologyPayload",
        property_name="cells",
        property_type="TopologyCell[]",
        frontend_path=DOMAIN_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="RulesResponse",
        property_name="rules",
        property_type="RuleDefinition[]",
        frontend_path=DOMAIN_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="ApiSimulationSnapshot",
        property_name="rule",
        property_type="RuleDefinition",
        frontend_path=DOMAIN_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="ApiSimulationSnapshot",
        property_name="topology",
        property_type="TopologyPayload",
        frontend_path=DOMAIN_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="PatternPayload",
        property_name="topology_spec",
        property_type="TopologySpec",
        frontend_path=DOMAIN_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="PersistedSimulationSnapshotV5",
        property_name="topology_spec",
        property_type="TopologySpec",
        frontend_path=DOMAIN_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="ConfigSyncBody",
        property_name="topology_spec",
        property_type="ConfigTopologySpecPatch",
        frontend_path=CONTROLLER_API_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="ResetControlBody",
        property_name="topology_spec",
        property_type="ResetTopologySpec",
        frontend_path=CONTROLLER_API_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="CellUpdatesRequest",
        property_name="cells",
        property_type="CellUpdateRequest[]",
        frontend_path=CONTROLLER_API_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="ViewportSyncOptions",
        property_name="body",
        property_type="ConfigSyncBody",
        frontend_path=CONTROLLER_VIEW_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="RuleSyncRequestOptions",
        property_name="body",
        property_type="ConfigSyncBody",
        frontend_path=CONTROLLER_SYNC_SESSION_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="EditorHistoryEntry",
        property_name="forwardCells",
        property_type="CellStateUpdate[]",
        frontend_path=EDITOR_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="EditorHistoryEntry",
        property_name="inverseCells",
        property_type="CellStateUpdate[]",
        frontend_path=EDITOR_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="EditorSessionOptions",
        property_name="setCellsRequest",
        property_type="SetCellsRequestFunction",
        frontend_path=EDITOR_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="EditorSessionOptions",
        property_name="postControl",
        property_type="PostControlFunction",
        frontend_path=EDITOR_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="InteractionControllerOptions",
        property_name="toggleCellRequest",
        property_type="ToggleCellRequestFunction",
        frontend_path=EDITOR_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="InteractionControllerOptions",
        property_name="setCellRequest",
        property_type="SetCellRequestFunction",
        frontend_path=EDITOR_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="InteractionControllerOptions",
        property_name="setCellsRequest",
        property_type="SetCellsRequestFunction",
        frontend_path=EDITOR_FRONTEND_PATH,
    ),
    FrontendPropertyTypeContract(
        interface_name="InteractionControllerOptions",
        property_name="postControl",
        property_type="PostControlFunction",
        frontend_path=EDITOR_FRONTEND_PATH,
    ),
)

FRONTEND_TYPE_ALIAS_CONTRACTS: tuple[FrontendTypeAliasContract, ...] = (
    FrontendTypeAliasContract(
        type_name="BootstrappedFrontendDefaults",
        type_body="FrontendDefaults",
        frontend_path=DOMAIN_FRONTEND_PATH,
    ),
    FrontendTypeAliasContract(
        type_name="TopologyDefinition",
        type_body="BootstrappedTopologyDefinition",
        frontend_path=DOMAIN_FRONTEND_PATH,
    ),
    FrontendTypeAliasContract(
        type_name="TopologyCell",
        type_body="ApiTopologyCellPayload",
        frontend_path=DOMAIN_FRONTEND_PATH,
    ),
    FrontendTypeAliasContract(
        type_name="ResetRequestBody",
        type_body="ResetControlBody",
        frontend_path=ACTIONS_FRONTEND_PATH,
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


def frontend_property_type_contracts() -> tuple[FrontendPropertyTypeContract, ...]:
    return FRONTEND_PROPERTY_TYPE_CONTRACTS


def frontend_type_alias_contracts() -> tuple[FrontendTypeAliasContract, ...]:
    return FRONTEND_TYPE_ALIAS_CONTRACTS


def payload_type_union_contracts() -> tuple[PayloadTypeUnionContract, ...]:
    return PAYLOAD_TYPE_UNION_CONTRACTS


__all__ = [
    "ACTIONS_FRONTEND_PATH",
    "CONTROLLER_API_FRONTEND_PATH",
    "CONTROLLER_SYNC_SESSION_FRONTEND_PATH",
    "CONTROLLER_VIEW_FRONTEND_PATH",
    "DOMAIN_FRONTEND_PATH",
    "EDITOR_FRONTEND_PATH",
    "FRONTEND_PROPERTY_TYPE_CONTRACTS",
    "FRONTEND_TYPE_ALIAS_CONTRACTS",
    "FrontendPropertyTypeContract",
    "FrontendTypeAliasContract",
    "PAYLOAD_FIELD_CONTRACTS",
    "PAYLOAD_TYPE_UNION_CONTRACTS",
    "PayloadFieldContract",
    "PayloadTypeUnionContract",
    "RENDERING_FRONTEND_PATH",
    "STANDALONE_PROTOCOL_FRONTEND_PATH",
    "frontend_property_type_contracts",
    "frontend_type_alias_contracts",
    "payload_field_contracts",
    "payload_type_union_contracts",
]
