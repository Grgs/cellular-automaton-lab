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
    "rhombille": ReferenceFamilySpec(
        geometry="rhombille",
        display_name="Rhombille",
        source_urls=("https://en.wikipedia.org/wiki/Rhombille_tiling",),
        root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("rhombus",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=54,
                expected_kind_counts=(("rhombus", 54),),
                expected_adjacency_pairs=(("rhombus", "rhombus"),),
                expected_degree_histogram=((1, 1), (2, 12), (3, 9), (4, 32)),
                expected_signature="0c57a0b0510a",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=6,
            slot_vocabulary=_prefixed_slots("s", 6),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("rhombus", "rhombus", "rhombus"),
                ("rhombus", "rhombus", "rhombus", "rhombus", "rhombus", "rhombus"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("rhombus", "rhombus", "rhombus"), 27),
                (("rhombus", "rhombus", "rhombus", "rhombus", "rhombus", "rhombus"), 10),
            ),
            expected_dual_geometry="trihexagonal-3-6-3-6",
        ),
    ),
}
