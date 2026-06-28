from __future__ import annotations

from backend.simulation.reference_specs.types import (
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

# Tiltwork is a non-canonical (made-up) periodic tiling: each unit
# square holds a 45°-rotated center diamond inset and four right-isoceles
# triangles in the corners. At every edge midpoint, 4 triangle 45° corners
# meet 2 diamond 90° corners (total 360°); at every grid corner, 4
# triangle right angles meet (4 * 90° = 360°). Not Archimedean (two
# distinct vertex configurations) and not the dual of any catalog tiling.

SPECS = {
    "tiltwork": ReferenceFamilySpec(
        geometry="tiltwork",
        display_name="Tiltwork",
        source_urls=(),
        root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("diamond", "corner-triangle"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=45,
                expected_kind_counts=(
                    ("corner-triangle", 36),
                    ("diamond", 9),
                ),
                expected_adjacency_pairs=(
                    ("corner-triangle", "corner-triangle"),
                    ("corner-triangle", "diamond"),
                ),
                expected_degree_histogram=((1, 4), (2, 16), (3, 16), (4, 9)),
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=5,
            slot_vocabulary=("s0", "s1", "s2", "s3", "s4"),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("corner-triangle", "corner-triangle", "corner-triangle", "corner-triangle"),
                (
                    "corner-triangle",
                    "corner-triangle",
                    "diamond",
                    "corner-triangle",
                    "corner-triangle",
                    "diamond",
                ),
            ),
            expected_interior_vertex_configuration_frequencies=(
                (("corner-triangle", "corner-triangle", "corner-triangle", "corner-triangle"), 4),
                (
                    (
                        "corner-triangle",
                        "corner-triangle",
                        "diamond",
                        "corner-triangle",
                        "corner-triangle",
                        "diamond",
                    ),
                    12,
                ),
            ),
        ),
    ),
}
