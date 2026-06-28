from __future__ import annotations

from backend.simulation.reference_specs.types import (
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

SPECS = {
    "uniform-2-18-36-33434": ReferenceFamilySpec(
        geometry="uniform-2-18-36-33434",
        display_name="2-uniform #18",
        source_urls=(
            "https://en.wikipedia.org/wiki/List_of_k-uniform_tilings",
            "https://commons.wikimedia.org/wiki/File:2-uniform_n18.svg",
        ),
        root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("square", "triangle"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=198,
                expected_kind_counts=(("square", 54), ("triangle", 144)),
                expected_adjacency_pairs=(
                    ("square", "triangle"),
                    ("triangle", "triangle"),
                ),
                expected_degree_histogram=((1, 2), (2, 33), (3, 120), (4, 43)),
                expected_signature="8efc9e0161ef",  # pragma: allowlist secret
                regular_polygon_kinds=("square", "triangle"),
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=22,
            slot_vocabulary=(
                "s1",
                "s2",
                "s3",
                "s4",
                "s5",
                "s6",
                "t1",
                "t10",
                "t11",
                "t12",
                "t13",
                "t14",
                "t15",
                "t16",
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
                ("square", "triangle", "square", "triangle", "triangle"),
                ("triangle", "triangle", "triangle", "triangle", "triangle", "triangle"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("square", "triangle", "square", "triangle", "triangle"), 91),
                (("triangle", "triangle", "triangle", "triangle", "triangle", "triangle"), 12),
            ),
        ),
    ),
}
