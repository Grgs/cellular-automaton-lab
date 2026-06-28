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
    "floret-pentagonal": ReferenceFamilySpec(
        geometry="floret-pentagonal",
        display_name="Floret Pentagonal",
        source_urls=("https://en.wikipedia.org/wiki/Floret_pentagonal_tiling",),
        root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("pentagon",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=756,
                expected_kind_counts=(("pentagon", 756),),
                expected_adjacency_pairs=(("pentagon", "pentagon"),),
                expected_degree_histogram=((1, 2), (2, 17), (3, 40), (4, 39), (5, 658)),
                expected_signature="68fc9ff72780",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=84,
            slot_vocabulary=_prefixed_slots("s", 84),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("pentagon", "pentagon", "pentagon"),
                ("pentagon", "pentagon", "pentagon", "pentagon", "pentagon", "pentagon"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("pentagon", "pentagon", "pentagon"), 938),
                (("pentagon", "pentagon", "pentagon", "pentagon", "pentagon", "pentagon"), 108),
            ),
            expected_dual_geometry="archimedean-3-3-3-3-6",
        ),
    ),
}
