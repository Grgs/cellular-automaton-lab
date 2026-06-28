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
    expected_tile_family_counts: tuple[tuple[str, int], ...] | None = None
    expected_orientation_token_counts: tuple[tuple[str, int], ...] | None = None
    expected_chirality_token_counts: tuple[tuple[str, int], ...] | None = None
    required_kinds: tuple[str, ...] = ()
    expected_adjacency_pairs: tuple[tuple[str, str], ...] | None = None
    required_adjacency_pairs: tuple[tuple[str, str], ...] = ()
    required_chirality_adjacency_pairs: tuple[tuple[str, str], ...] = ()
    expected_degree_histogram: tuple[tuple[int, int], ...] | None = None
    min_unique_orientation_tokens: int | None = None
    min_unique_chirality_tokens: int | None = None
    min_three_opposite_chirality_neighbor_cells: int | None = None
    min_unique_polygon_areas_by_kind: tuple[tuple[str, int], ...] | None = None
    expected_polygon_area_frequencies_by_kind: (
        tuple[tuple[str, tuple[tuple[float, int], ...]], ...] | None
    ) = None
    min_unique_decoration_variants_by_kind: tuple[tuple[str, int], ...] | None = None
    min_bounds_longest_span: float | None = None
    max_bounds_aspect_ratio: float | None = None
    expected_signature: str | None = None
    canonical_patch_fixture_key: str | None = None
    canonical_patch_include_id: bool = False
    # When set, every cell polygon must be a triangle whose sorted side
    # lengths, normalized by the shortest side, match these ratios within a
    # small relative tolerance. This pins per-tile congruence to the family's
    # prototile shape (e.g. ``(1.0, 2.0, sqrt(5))`` for pinwheel), which the
    # count/area/adjacency invariants cannot see: an angle-mismatched affine
    # subdivision preserves areas and counts while shearing tile shapes.
    expected_triangle_side_ratios: tuple[float, float, float] | None = None
    # When set, every cell of these kinds must be a regular polygon: all edge
    # lengths equal and all interior angles equal within a small relative
    # tolerance. This is an independent geometric truth (a regular n-gon is
    # fully determined by n) that the count/area/adjacency/vertex-configuration
    # invariants cannot see -- a sheared or dented face can preserve cell counts,
    # areas, and even which polygon kinds meet at a vertex while ceasing to be
    # regular. Used by uniform tilings whose faces are regular by definition.
    regular_polygon_kinds: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReferenceFamilySpec:
    geometry: str
    display_name: str
    source_urls: tuple[str, ...]
    root_seed_policy: str
    allowed_public_cell_kinds: tuple[str, ...]
    required_metadata: tuple[MetadataRequirement, ...]
    sample_mode: Literal["patch_depth", "grid"] = "patch_depth"
    depth_expectations: dict[int, ReferenceDepthExpectation] = field(default_factory=dict)
    periodic_descriptor: PeriodicDescriptorExpectation | None = None
    builder_signals: tuple[BuilderSignalExpectation, ...] = ()
    exact_reference_mode: str | None = None
    notes: tuple[str, ...] = ()
