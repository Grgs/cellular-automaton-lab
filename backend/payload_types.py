from __future__ import annotations

from typing import Literal, NotRequired, TypeAlias, TypedDict


RawJsonObject: TypeAlias = dict[str, object]
RawJsonArray: TypeAlias = list[object]
RawJsonDocument: TypeAlias = RawJsonObject | RawJsonArray | str | int | float | bool | None
SparseCellsByIdPayload: TypeAlias = dict[str, int]


class FrontendManifestRecord(TypedDict, total=False):
    file: str
    src: str
    isEntry: bool
    css: list[str]


FrontendManifestPayload: TypeAlias = dict[str, FrontendManifestRecord]


class TopologySpecPayload(TypedDict):
    tiling_family: str
    adjacency_mode: str
    sizing_mode: str
    width: int
    height: int
    patch_depth: int


class SizingPolicyPayload(TypedDict):
    control: str
    default: int
    min: int
    max: int


class TopologyVariantPayload(TypedDict):
    id: str
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


class TopologyCatalogEntryPayload(TypedDict):
    tiling_family: str
    label: str
    picker_group: str
    picker_order: int
    sizing_mode: str
    family: str
    render_kind: str
    viewport_sync_mode: str
    supported_adjacency_modes: list[str]
    default_adjacency_mode: str
    default_rules: dict[str, str]
    geometry_keys: dict[str, str]
    sizing_policy: SizingPolicyPayload


class TopologySpecRequestPayload(TypedDict):
    tiling_family: str
    adjacency_mode: str
    sizing_mode: str
    width: int | None
    height: int | None
    patch_depth: int | None
    unsafe_size_override: NotRequired[bool]


class TopologySpecPatch(TypedDict, total=False):
    tiling_family: str
    adjacency_mode: str
    sizing_mode: str
    width: int
    height: int
    patch_depth: int
    unsafe_size_override: bool


TopologySpecInput: TypeAlias = TopologySpecPayload | TopologySpecRequestPayload | TopologySpecPatch


class ConfigTopologySpecPatchPayload(TypedDict, total=False):
    width: int
    height: int
    unsafe_size_override: bool


class ResetTopologySpecPayload(TopologySpecPayload):
    unsafe_size_override: NotRequired[bool]


class ConfigSyncRequestPayload(TypedDict, total=False):
    topology_spec: ConfigTopologySpecPatchPayload
    speed: float
    rule: str | None


class PersistedSimulationSnapshotV5(TypedDict):
    version: Literal[5]
    topology_spec: TopologySpecPayload
    speed: float
    running: bool
    generation: int
    rule: str
    cells_by_id: SparseCellsByIdPayload


class PersistedSimulationSnapshotCandidate(TypedDict, total=False):
    version: object
    topology_spec: object
    speed: object
    running: object
    generation: object
    rule: object
    cells_by_id: object


PersistedSimulationSnapshotInput: TypeAlias = (
    PersistedSimulationSnapshotV5 | PersistedSimulationSnapshotCandidate
)


class ServerMetaPayload(TypedDict):
    app_name: str


class CellStatePayload(TypedDict):
    value: int
    label: str
    color: str
    paintable: bool


class RuleDefinitionPayload(TypedDict):
    name: str
    display_name: str
    description: str
    states: list[CellStatePayload]
    default_paint_state: int
    supports_randomize: bool
    rule_protocol: str
    supports_all_topologies: bool


class RulesResponsePayload(TypedDict):
    rules: list[RuleDefinitionPayload]


class PointPayload(TypedDict):
    x: float
    y: float


class TopologyCellPayload(TypedDict):
    id: str
    kind: str
    neighbors: list[str | None]
    slot: NotRequired[str]
    center: NotRequired[PointPayload]
    vertices: NotRequired[list[PointPayload]]
    tile_family: NotRequired[str]
    orientation_token: NotRequired[str]
    chirality_token: NotRequired[str]
    decoration_tokens: NotRequired[list[str]]


class TopologyPayload(TypedDict):
    topology_spec: TopologySpecPayload
    topology_revision: str
    cells: list[TopologyCellPayload]


class SimulationStatePayload(TypedDict):
    topology_spec: TopologySpecPayload
    speed: float
    running: bool
    generation: int
    rule: RuleDefinitionPayload
    topology_revision: str
    cell_states: list[int]
    topology: TopologyPayload


class ApiErrorPayload(TypedDict):
    error: str


class PeriodicFaceTilingDescriptorPayload(TypedDict):
    geometry: str
    label: str
    metric_model: str
    base_edge: float
    unit_width: float
    unit_height: float
    min_dimension: int
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    cell_count_per_unit: int
    row_offset_x: float


class SimulationDefaultsPayload(TypedDict):
    topology_spec: TopologySpecPayload
    speed: float
    rule: str
    min_grid_size: int
    max_grid_size: int
    min_patch_depth: int
    max_patch_depth: int
    min_speed: float
    max_speed: float


class UiDefaultsPayload(TypedDict):
    cell_size: int
    min_cell_size: int
    max_cell_size: int
    storage_key: str


class ThemeDefaultsPayload(TypedDict):
    default: str
    storage_key: str


class AppDefaultsPayload(TypedDict):
    simulation: SimulationDefaultsPayload
    ui: UiDefaultsPayload
    theme: ThemeDefaultsPayload


class AperiodicFamilyBootstrapPayload(TypedDict):
    tiling_family: str
    label: str
    experimental: bool
    public_cell_kinds: list[str]


class AppBootstrapPayload(TypedDict):
    app_defaults: AppDefaultsPayload
    topology_catalog: list[TopologyCatalogEntryPayload]
    periodic_face_tilings: list[PeriodicFaceTilingDescriptorPayload]
    aperiodic_families: list[AperiodicFamilyBootstrapPayload]
    server_meta: ServerMetaPayload
    snapshot_version: int


class ResetControlRequestPayload(TypedDict):
    topology_spec: ResetTopologySpecPayload
    speed: float
    rule: str | None
    randomize: bool


class CellTargetPayload(TypedDict):
    id: str


class CellUpdatePayload(CellTargetPayload):
    state: int


CellUpdatesPayload: TypeAlias = list[CellUpdatePayload]


class CellUpdatesRequestPayload(TypedDict):
    cells: CellUpdatesPayload
