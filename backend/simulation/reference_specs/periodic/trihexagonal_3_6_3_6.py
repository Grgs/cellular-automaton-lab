from __future__ import annotations

from backend.simulation.reference_specs.types import (
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

SPECS = {
    "trihexagonal-3-6-3-6": ReferenceFamilySpec(
        geometry="trihexagonal-3-6-3-6",
        display_name="Kagome / Trihexagonal (3.6.3.6)",
        source_urls=("https://en.wikipedia.org/wiki/Trihexagonal_tiling",),
        root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("hexagon", "triangle-down", "triangle-up"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=27,
                expected_kind_counts=(("hexagon", 9), ("triangle-down", 9), ("triangle-up", 9)),
                expected_adjacency_pairs=(("hexagon", "triangle-down"), ("hexagon", "triangle-up")),
                expected_degree_histogram=((1, 5), (2, 6), (3, 11), (5, 2), (6, 3)),
                expected_signature="9e8a5ba64587",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=3,
            slot_vocabulary=("hexagon", "triangle-down", "triangle-up"),
            id_pattern="{prefix}:{x}:{y}",
            row_offset_x=52.0,
            expected_interior_vertex_configurations=(
                ("hexagon", "triangle-down", "hexagon", "triangle-up"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("hexagon", "triangle-down", "hexagon", "triangle-up"), 13),
            ),
            expected_dual_geometry="rhombille",
        ),
    ),
}
