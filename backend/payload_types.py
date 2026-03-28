from __future__ import annotations

from typing import Literal, TypeAlias, TypedDict


JsonObject: TypeAlias = dict[str, object]
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


class CellTargetPayload(TypedDict):
    id: str


class CellUpdatePayload(CellTargetPayload):
    state: int


CellUpdatesPayload: TypeAlias = list[CellUpdatePayload]
