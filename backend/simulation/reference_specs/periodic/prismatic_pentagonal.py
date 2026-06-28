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
    "prismatic-pentagonal": ReferenceFamilySpec(
        geometry="prismatic-pentagonal",
        display_name="Prismatic Pentagonal",
        source_urls=("https://en.wikipedia.org/wiki/Prismatic_pentagonal_tiling",),
        root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("pentagon",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=72,
                expected_kind_counts=(("pentagon", 72),),
                expected_adjacency_pairs=(("pentagon", "pentagon"),),
                expected_degree_histogram=((2, 2), (3, 12), (4, 18), (5, 40)),
                expected_signature="5fc704eefa57",  # pragma: allowlist secret
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
                (("pentagon", "pentagon", "pentagon"), 60),
                (("pentagon", "pentagon", "pentagon", "pentagon"), 25),
            ),
            expected_dual_candidate_geometries=(
                "archimedean-3-3-3-4-4",
                "archimedean-3-3-4-3-4",
            ),
            expected_dual_structure_signature=((3, 60), (4, 25)),
        ),
    ),
}
