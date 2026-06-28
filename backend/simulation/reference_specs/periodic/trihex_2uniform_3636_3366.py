from __future__ import annotations

from backend.simulation.reference_specs.types import (
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

# 2-uniform tiling [3.6.3.6; 3^2.6^2]: combines kagome-like trihexagonal
# vertices with "elongated trihex" vertices where two hexagons share an
# edge. Construction: rows of pointy-top hexagons share vertical edges
# within each row (creating (3^2.6^2) vertices at the shared corners
# where two edge-sharing hexagons meet two adjacent triangles in TTHH
# order). Between rows, hexagons touch vertex-to-vertex (top of lower hex
# = bottom of upper hex), with diamond gaps to the sides filled by pairs
# of equilateral triangles. The end-to-end vertices between rows are
# (3.6.3.6) (THTH order). Edge-to-edge; no T-junctions.
#
# The reference verifier preserves vertex configuration ORDER (the
# polygon kinds around the vertex going CCW), so the two genuine vertex
# types resolve as:
#   (hexagon, hexagon, triangle, triangle)  - (3^2.6^2) HHTT order
#   (hexagon, triangle, hexagon, triangle)  - (3.6.3.6)  HTHT order

SPECS = {
    "trihex-2uniform-3636-3366": ReferenceFamilySpec(
        geometry="trihex-2uniform-3636-3366",
        display_name="2-uniform Trihex (3.6.3.6; 3^2.6^2)",
        source_urls=("https://en.wikipedia.org/wiki/Euclidean_tilings_by_convex_regular_polygons",),
        root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("hexagon", "triangle"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=27,
                expected_kind_counts=(
                    ("hexagon", 9),
                    ("triangle", 18),
                ),
                expected_adjacency_pairs=(
                    ("hexagon", "hexagon"),
                    ("hexagon", "triangle"),
                    ("triangle", "triangle"),
                ),
                expected_degree_histogram=(
                    (1, 3),
                    (2, 6),
                    (3, 13),
                    (4, 1),
                    (5, 2),
                    (6, 2),
                ),
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=3,
            slot_vocabulary=("hex", "tl", "tr"),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("hexagon", "hexagon", "triangle", "triangle"),
                ("hexagon", "triangle", "hexagon", "triangle"),
            ),
            expected_interior_vertex_configuration_frequencies=(
                # 3x3 open-boundary sample observed by the verifier.
                # (3^2.6^2) at hex-row shared corners; (3.6.3.6) at the
                # vertex-touching points between rows.
                (("hexagon", "hexagon", "triangle", "triangle"), 10),
                (("hexagon", "triangle", "hexagon", "triangle"), 4),
            ),
        ),
    ),
}
