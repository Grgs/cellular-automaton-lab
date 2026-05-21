from __future__ import annotations

from backend.simulation.reference_specs.types import (
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)
from backend.simulation.reference_specs.helpers import (
    _prefixed_slots,
)

SPECS = {
    "tetrakis-square": ReferenceFamilySpec(
        geometry="tetrakis-square",
        display_name="Tetrakis Square",
        source_urls=("https://en.wikipedia.org/wiki/Tetrakis_square_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("triangle",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=36,
                expected_kind_counts=(("triangle", 36),),
                expected_adjacency_pairs=(("triangle", "triangle"),),
                expected_degree_histogram=((2, 12), (3, 24)),
                expected_signature="d7592c13db1e",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=4,
            slot_vocabulary=_prefixed_slots("s", 4),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("triangle", "triangle", "triangle", "triangle"),
                (
                    "triangle",
                    "triangle",
                    "triangle",
                    "triangle",
                    "triangle",
                    "triangle",
                    "triangle",
                    "triangle",
                ),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("triangle", "triangle", "triangle", "triangle"), 9),
                (
                    (
                        "triangle",
                        "triangle",
                        "triangle",
                        "triangle",
                        "triangle",
                        "triangle",
                        "triangle",
                        "triangle",
                    ),
                    4,
                ),
            ),
            expected_dual_geometry="archimedean-4-8-8",
        ),
    ),
}
