from __future__ import annotations

from backend.simulation.reference_specs.types import (
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

SPECS = {
    "cairo-pentagonal": ReferenceFamilySpec(
        geometry="cairo-pentagonal",
        display_name="Cairo Pentagonal",
        source_urls=("https://en.wikipedia.org/wiki/Cairo_pentagonal_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("pentagon",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=36,
                expected_kind_counts=(("pentagon", 36),),
                expected_adjacency_pairs=(("pentagon", "pentagon"),),
                expected_degree_histogram=((2, 3), (3, 8), (4, 13), (5, 12)),
                expected_signature="e33351b2ed77",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=4,
            slot_vocabulary=("a", "b", "c", "d"),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=71.0,
            expected_interior_vertex_configurations=(
                ("pentagon", "pentagon", "pentagon"),
                ("pentagon", "pentagon", "pentagon", "pentagon"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("pentagon", "pentagon", "pentagon"), 26),
                (("pentagon", "pentagon", "pentagon", "pentagon"), 10),
            ),
            expected_dual_candidate_geometries=(
                "archimedean-3-3-3-4-4",
                "archimedean-3-3-4-3-4",
            ),
            expected_dual_structure_signature=((3, 26), (4, 10)),
        ),
    ),
}
