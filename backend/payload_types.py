from __future__ import annotations

from typing import Literal, NotRequired, TypeAlias, TypedDict


JsonObject: TypeAlias = dict[str, object]
JsonArray: TypeAlias = list[object]
JsonDocument: TypeAlias = JsonObject | JsonArray | str | int | float | bool | None
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


class TopologySpecRequestPayload(TypedDict):
    tiling_family: str
    adjacency_mode: str
    sizing_mode: str
    width: int | None
    height: int | None
    patch_depth: int | None


class TopologySpecPatch(TypedDict, total=False):
    tiling_family: str
    adjacency_mode: str
    sizing_mode: str
    width: int
    height: int
    patch_depth: int


TopologySpecInput: TypeAlias = TopologySpecPayload | TopologySpecRequestPayload | TopologySpecPatch


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


class ResetControlRequestPayload(TypedDict):
    topology_spec: TopologySpecPayload
    speed: float
    rule: str
    randomize: bool


class CellTargetPayload(TypedDict):
    id: str


class CellUpdatePayload(CellTargetPayload):
    state: int


CellUpdatesPayload: TypeAlias = list[CellUpdatePayload]
