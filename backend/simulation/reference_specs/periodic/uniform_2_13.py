from __future__ import annotations

from backend.simulation.reference_specs.types import (
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

SPECS = {
    "uniform-2-13-36-32412": ReferenceFamilySpec(
        geometry="uniform-2-13-36-32412",
        display_name="2-uniform #13",
        source_urls=(
            "https://en.wikipedia.org/wiki/List_of_k-uniform_tilings",
            "https://commons.wikimedia.org/wiki/File:2-uniform_n13.svg",
        ),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("dodecagon", "square", "triangle"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=144,
                expected_kind_counts=(
                    ("dodecagon", 9),
                    ("square", 27),
                    ("triangle", 108),
                ),
                expected_adjacency_pairs=(
                    ("dodecagon", "square"),
                    ("dodecagon", "triangle"),
                    ("square", "triangle"),
                    ("triangle", "triangle"),
                ),
                expected_degree_histogram=(
                    (1, 6),
                    (2, 32),
                    (3, 84),
                    (4, 16),
                    (8, 2),
                    (12, 4),
                ),
                expected_signature="6ae9f47020d8",  # pragma: allowlist secret
                regular_polygon_kinds=("dodecagon", "square", "triangle"),
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=16,
            slot_vocabulary=(
                "d1",
                "s1",
                "s2",
                "s3",
                "t1",
                "t10",
                "t11",
                "t12",
                "t2",
                "t3",
                "t4",
                "t5",
                "t6",
                "t7",
                "t8",
                "t9",
            ),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("dodecagon", "square", "triangle", "triangle"),
                ("triangle", "triangle", "triangle", "triangle", "triangle", "triangle"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("dodecagon", "square", "triangle", "triangle"), 70),
                (("triangle", "triangle", "triangle", "triangle", "triangle", "triangle"), 12),
            ),
        ),
    ),
}
