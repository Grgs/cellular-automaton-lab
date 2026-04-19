from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class BuilderSignalExpectation:
    module: str
    attribute: str
    expected_value: object


@dataclass(frozen=True)
class MetadataRequirement:
    kind: str
    fields: tuple[str, ...]


@dataclass(frozen=True)
class PeriodicDescriptorExpectation:
    face_template_count: int
    slot_vocabulary: tuple[str, ...]
    id_pattern: str
    row_offset_x: float
    expected_interior_vertex_configurations: tuple[tuple[str, ...], ...]
    expected_interior_vertex_configuration_frequencies: tuple[tuple[tuple[str, ...], int], ...]
    expected_dual_geometry: str | None = None
    expected_dual_candidate_geometries: tuple[str, ...] = ()
    expected_dual_structure_signature: tuple[tuple[int, int], ...] | None = None
    canonical_grid_size: tuple[int, int] | None = None


@dataclass(frozen=True)
class ReferenceDepthExpectation:
    exact_total_cells: int | None = None
    minimum_total_cells: int | None = None
    require_connected_graph: bool = True
    require_hole_free_surface: bool = True
    expected_kind_counts: tuple[tuple[str, int], ...] | None = None
    expected_orientation_token_counts: tuple[tuple[str, int], ...] | None = None
    required_kinds: tuple[str, ...] = ()
    expected_adjacency_pairs: tuple[tuple[str, str], ...] | None = None
    required_adjacency_pairs: tuple[tuple[str, str], ...] = ()
    required_chirality_adjacency_pairs: tuple[tuple[str, str], ...] = ()
    expected_degree_histogram: tuple[tuple[int, int], ...] | None = None
    min_unique_orientation_tokens: int | None = None
    min_unique_chirality_tokens: int | None = None
    min_three_opposite_chirality_neighbor_cells: int | None = None
    min_unique_polygon_areas_by_kind: tuple[tuple[str, int], ...] | None = None
    expected_polygon_area_frequencies_by_kind: tuple[
        tuple[str, tuple[tuple[float, int], ...]],
        ...
    ] | None = None
    min_unique_decoration_variants_by_kind: tuple[tuple[str, int], ...] | None = None
    min_bounds_longest_span: float | None = None
    max_bounds_aspect_ratio: float | None = None
    expected_signature: str | None = None
    canonical_patch_fixture_key: str | None = None
    canonical_patch_include_id: bool = False


@dataclass(frozen=True)
class ReferenceFamilySpec:
    geometry: str
    display_name: str
    source_urls: tuple[str, ...]
    canonical_root_seed_policy: str
    allowed_public_cell_kinds: tuple[str, ...]
    required_metadata: tuple[MetadataRequirement, ...]
    sample_mode: Literal["patch_depth", "grid"] = "patch_depth"
    depth_expectations: dict[int, ReferenceDepthExpectation] = field(default_factory=dict)
    periodic_descriptor: PeriodicDescriptorExpectation | None = None
    builder_signals: tuple[BuilderSignalExpectation, ...] = ()
    exact_reference_mode: str | None = None
    notes: tuple[str, ...] = ()
