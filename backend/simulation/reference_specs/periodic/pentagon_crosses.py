from __future__ import annotations

from backend.simulation.reference_specs.types import (
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

SPECS = {
    "pentagon-crosses": ReferenceFamilySpec(
        geometry="pentagon-crosses",
        display_name="Pentagon Crosses",
        source_urls=(),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("pentagon-cross",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=36,
                expected_kind_counts=(("pentagon-cross", 36),),
                expected_adjacency_pairs=(("pentagon-cross", "pentagon-cross"),),
                expected_degree_histogram=((2, 4), (3, 8), (4, 8), (5, 16)),
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=4,
            slot_vocabulary=("q0", "q1", "q2", "q3"),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("pentagon-cross", "pentagon-cross", "pentagon-cross"),
                ("pentagon-cross", "pentagon-cross", "pentagon-cross", "pentagon-cross"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("pentagon-cross", "pentagon-cross", "pentagon-cross"), 24),
                (("pentagon-cross", "pentagon-cross", "pentagon-cross", "pentagon-cross"), 13),
            ),
        ),
    ),
}
