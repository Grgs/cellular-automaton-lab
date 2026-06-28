from __future__ import annotations

from backend.simulation.reference_specs.types import (
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

SPECS = {
    "uniform-3-4-6-12": ReferenceFamilySpec(
        geometry="uniform-3-4-6-12",
        display_name="2-uniform 3-4-6-12",
        source_urls=("https://en.wikipedia.org/wiki/3-4-6-12_tiling",),
        root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("dodecagon", "hexagon", "square", "triangle"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=241,
                expected_kind_counts=(
                    ("dodecagon", 25),
                    ("hexagon", 60),
                    ("square", 114),
                    ("triangle", 42),
                ),
                expected_adjacency_pairs=(
                    ("dodecagon", "hexagon"),
                    ("dodecagon", "square"),
                    ("hexagon", "square"),
                    ("square", "triangle"),
                ),
                expected_degree_histogram=((2, 12), (3, 48), (4, 112), (6, 48), (7, 8), (12, 13)),
                expected_signature="e848c971b946",  # pragma: allowlist secret
                # Every face in the 3.4.6.12 tiling is a regular polygon by
                # definition; assert it independently from the cells' own
                # vertices so a sheared face can't slip past the count/area/
                # vertex-configuration checks.
                regular_polygon_kinds=("dodecagon", "hexagon", "square", "triangle"),
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=24,
            slot_vocabulary=(
                "d1",
                "d2",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "s1",
                "s10",
                "s11",
                "s12",
                "s2",
                "s3",
                "s4",
                "s5",
                "s6",
                "s7",
                "s8",
                "s9",
                "t1",
                "t2",
                "t3",
                "t4",
            ),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("dodecagon", "hexagon", "square"),
                ("hexagon", "square", "triangle", "square"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("dodecagon", "hexagon", "square"), 216),
                (("hexagon", "square", "triangle", "square"), 102),
            ),
        ),
    ),
}
