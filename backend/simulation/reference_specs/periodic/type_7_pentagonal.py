from __future__ import annotations

from backend.simulation.reference_specs.helpers import (
    _prefixed_slots,
)
from backend.simulation.reference_specs.types import (
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

SPECS = {
    "type-7-pentagonal": ReferenceFamilySpec(
        geometry="type-7-pentagonal",
        display_name="Type 7 Pentagonal",
        source_urls=(
            "https://en.wikipedia.org/wiki/Pentagonal_tiling",
            "https://www.mathartroom.com/wallpaper/pentagon_tiling/type07/",
        ),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("pentagon",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=72,
                expected_kind_counts=(("pentagon", 72),),
                expected_adjacency_pairs=(("pentagon", "pentagon"),),
                expected_degree_histogram=((1, 2), (2, 6), (3, 8), (4, 16), (5, 40)),
                expected_signature="d89202cef9f7",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=8,
            slot_vocabulary=_prefixed_slots("s", 8),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("pentagon", "pentagon", "pentagon"),
                ("pentagon", "pentagon", "pentagon", "pentagon"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("pentagon", "pentagon", "pentagon"), 56),
                (("pentagon", "pentagon", "pentagon", "pentagon"), 24),
            ),
            expected_dual_candidate_geometries=(
                "archimedean-3-3-3-4-4",
                "archimedean-3-3-4-3-4",
            ),
            expected_dual_structure_signature=((3, 56), (4, 24)),
        ),
    ),
}
