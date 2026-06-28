from __future__ import annotations

from backend.simulation.reference_specs.types import (
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

SPECS = {
    "right-triangle": ReferenceFamilySpec(
        geometry="right-triangle",
        display_name="Right-Triangle",
        source_urls=(),
        root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("right-triangle",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=18,
                expected_kind_counts=(("right-triangle", 18),),
                expected_adjacency_pairs=(("right-triangle", "right-triangle"),),
                expected_degree_histogram=((1, 2), (2, 8), (3, 8)),
                expected_signature="2b3c5c738684",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=2,
            slot_vocabulary=("lower", "upper"),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                (
                    "right-triangle",
                    "right-triangle",
                    "right-triangle",
                    "right-triangle",
                    "right-triangle",
                    "right-triangle",
                ),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (
                    (
                        "right-triangle",
                        "right-triangle",
                        "right-triangle",
                        "right-triangle",
                        "right-triangle",
                        "right-triangle",
                    ),
                    4,
                ),
            ),
        ),
    ),
}
