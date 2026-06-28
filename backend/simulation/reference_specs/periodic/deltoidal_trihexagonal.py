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
    "deltoidal-trihexagonal": ReferenceFamilySpec(
        geometry="deltoidal-trihexagonal",
        display_name="Deltoidal Trihexagonal",
        source_urls=("https://en.wikipedia.org/wiki/Deltoidal_trihexagonal_tiling",),
        root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("kite",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=108,
                expected_kind_counts=(("kite", 108),),
                expected_adjacency_pairs=(("kite", "kite"),),
                expected_degree_histogram=((1, 3), (2, 19), (3, 11), (4, 75)),
                expected_signature="8256bbb6a915",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=12,
            slot_vocabulary=tuple(sorted(_prefixed_slots("s", 12))),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("kite", "kite", "kite"),
                ("kite", "kite", "kite", "kite"),
                ("kite", "kite", "kite", "kite", "kite", "kite"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("kite", "kite", "kite"), 28),
                (("kite", "kite", "kite", "kite"), 40),
                (("kite", "kite", "kite", "kite", "kite", "kite"), 12),
            ),
            expected_dual_candidate_geometries=("archimedean-3-4-6-4",),
            expected_dual_structure_signature=((3, 28), (4, 40), (6, 12)),
        ),
    ),
}
