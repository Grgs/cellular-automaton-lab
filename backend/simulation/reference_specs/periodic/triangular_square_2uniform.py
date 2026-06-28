from __future__ import annotations

from backend.simulation.reference_specs.types import (
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

# 2-uniform tiling [3^6; 3^3.4^2] - the first 2-uniform tiling in the
# catalog. It uses only equilateral triangles and squares (all unit edge
# length), arranged so that two distinct vertex transitivity classes
# coexist edge-to-edge:
#
#   3^6      - six triangles meeting at a point, like the interior of
#              the regular triangular tiling
#   3^3.4^2  - three triangles plus two squares, the elongated-
#              triangular vertex configuration
#
# Construction: stack alternating "blocks" vertically.
#   Block A: two consecutive rows of pure triangular tiling
#            (height sqrt(3) at unit edge, contains 4 triangles per
#            unit horizontal cell)
#   Block B: one row of squares (height 1, contains 1 square per unit
#            horizontal cell)
# The interior y=sqrt(3)/2 line inside Block A is a row of 6-triangle
# vertices (3^6). The boundary lines y=0 and y=sqrt(3) between Block A
# and Block B are rows of triangle+square vertices (3^3.4^2).
#
# Cell width is 2 horizontal units so that both the interior and
# boundary down-triangles fit cleanly; the boundary down-triangle that
# straddles the left edge of the cell (and the corresponding row-2 up-
# triangle) carry repeat_x_extra=1 so the rightmost cell of any finite
# patch is fully covered.

SPECS = {
    "triangular-square-2uniform": ReferenceFamilySpec(
        geometry="triangular-square-2uniform",
        display_name="2-uniform Triangle+Square",
        source_urls=("https://en.wikipedia.org/wiki/List_of_k-uniform_tilings",),
        root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("triangle", "square"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=96,
                expected_kind_counts=(
                    ("square", 18),
                    ("triangle", 78),
                ),
                expected_adjacency_pairs=(
                    ("square", "square"),
                    ("square", "triangle"),
                    ("triangle", "triangle"),
                ),
                expected_degree_histogram=(
                    (2, 20),
                    (3, 68),
                    (4, 8),
                ),
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=10,
            slot_vocabulary=(
                "da",
                "db",
                "dc",
                "dleft",
                "sa",
                "sb",
                "ua",
                "ub",
                "uc",
                "uleftr2",
            ),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                # 3^3.4^2: 3 triangles + 2 squares (sorted to match
                # verifier's canonical ordering)
                ("square", "square", "triangle", "triangle", "triangle"),
                # 3^6: 6 triangles
                (
                    "triangle",
                    "triangle",
                    "triangle",
                    "triangle",
                    "triangle",
                    "triangle",
                ),
            ),
            expected_interior_vertex_configuration_frequencies=(
                # In the open-boundary 3x3 sample the verifier counts
                # 25 boundary vertices and 18 interior triangle-strip
                # vertices.
                (
                    (
                        "square",
                        "square",
                        "triangle",
                        "triangle",
                        "triangle",
                    ),
                    25,
                ),
                (
                    (
                        "triangle",
                        "triangle",
                        "triangle",
                        "triangle",
                        "triangle",
                        "triangle",
                    ),
                    18,
                ),
            ),
        ),
    ),
}
