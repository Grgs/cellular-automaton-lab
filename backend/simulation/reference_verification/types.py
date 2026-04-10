from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, NotRequired, TypedDict

VerificationStatus = Literal["PASS", "KNOWN_DEVIATION", "FAIL"]


@dataclass(frozen=True)
class ReferenceCheckFailure:
    code: str
    message: str
    depth: int | None = None


@dataclass(frozen=True)
class ReferencePatchObservation:
    geometry: str
    sample_mode: str
    depth: int
    total_cells: int
    kind_counts: tuple[tuple[str, int], ...]
    orientation_token_counts: tuple[tuple[str, int], ...]
    degree_histogram: tuple[tuple[int, int], ...]
    connected_component_count: int
    disconnected_component_sizes: tuple[int, ...]
    largest_component_size: int
    isolated_cell_count: int
    surface_component_count: int | None
    hole_count: int
    unique_orientation_tokens: int
    unique_chirality_tokens: int
    chirality_adjacency_pairs: tuple[tuple[str, str], ...]
    three_opposite_chirality_neighbor_cells: int
    unique_polygon_areas_by_kind: tuple[tuple[str, int], ...]
    unique_decoration_variants_by_kind: tuple[tuple[str, int], ...]
    adjacency_pairs: tuple[tuple[str, str], ...]
    bounds_width: float
    bounds_height: float
    bounds_longest_span: float
    bounds_aspect_ratio: float
    signature: str


@dataclass(frozen=True)
class ReferenceVerificationResult:
    geometry: str
    display_name: str
    status: VerificationStatus
    blocking: bool
    waived: bool
    source_urls: tuple[str, ...]
    observations: tuple[ReferencePatchObservation, ...]
    failures: tuple[ReferenceCheckFailure, ...]

    @property
    def is_success(self) -> bool:
        return self.status != "FAIL"


class _LocalReferencePayload(TypedDict):
    kind: str
    orientation_token: str | None
    chirality_token: str | None
    decoration_tokens: list[str] | None
    area: float


class _LocalReferenceRootPayload(_LocalReferencePayload):
    degree: int


class _LocalReferenceNeighborPayload(_LocalReferencePayload):
    delta: list[float]


class _LocalReferenceAnchorPayload(TypedDict):
    root: _LocalReferenceRootPayload
    neighbors: list[_LocalReferenceNeighborPayload]


class _CanonicalPatchCellPayload(TypedDict):
    kind: str
    orientation_token: str | None
    chirality_token: str | None
    decoration_tokens: list[str] | None
    center: list[float]
    vertices: list[list[float]]
    id: NotRequired[str]


class _CanonicalPatchFixturePayload(TypedDict):
    depth: int
    include_id: bool
    cells: list[_CanonicalPatchCellPayload]
