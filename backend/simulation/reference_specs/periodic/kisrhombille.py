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
    "kisrhombille": ReferenceFamilySpec(
        geometry="kisrhombille",
        display_name="Kisrhombille",
        source_urls=("https://en.wikipedia.org/wiki/Truncated_trihexagonal_tiling",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("triangle",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=216,
                expected_kind_counts=(("triangle", 216),),
                expected_adjacency_pairs=(("triangle", "triangle"),),
                expected_degree_histogram=((1, 9), (2, 30), (3, 177)),
                expected_signature="8744608a6fc6",  # pragma: allowlist secret
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=24,
            slot_vocabulary=_prefixed_slots("s", 24),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("triangle", "triangle", "triangle", "triangle"),
                ("triangle", "triangle", "triangle", "triangle", "triangle", "triangle"),
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
                (("triangle", "triangle", "triangle", "triangle"), 45),
                (("triangle", "triangle", "triangle", "triangle", "triangle", "triangle"), 28),
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
                    12,
                ),
            ),
            expected_dual_geometry="archimedean-4-6-12",
        ),
    ),
}
