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
    "triakis-triangular": ReferenceFamilySpec(
        geometry="triakis-triangular",
        display_name="Triakis Triangular",
        source_urls=("https://en.wikipedia.org/wiki/Triakis_triangular_tiling",),
        root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("triangle",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=324,
                expected_kind_counts=(("triangle", 324),),
                expected_adjacency_pairs=(("triangle", "triangle"),),
                expected_degree_histogram=((1, 16), (2, 26), (3, 282)),
                expected_signature="8b5758b46c56",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=36,
            slot_vocabulary=_prefixed_slots("s", 36),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("triangle", "triangle", "triangle"),
                (
                    "triangle",
                    "triangle",
                    "triangle",
                    "triangle",
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
                (("triangle", "triangle", "triangle"), 94),
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
                        "triangle",
                        "triangle",
                        "triangle",
                        "triangle",
                    ),
                    40,
                ),
            ),
            expected_dual_geometry="archimedean-3-12-12",
        ),
    ),
}
