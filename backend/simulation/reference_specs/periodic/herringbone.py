from __future__ import annotations

from backend.simulation.reference_specs.types import (
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

# Herringbone tiling: 2:1 bricks (length 2, width 1) in two orientations -
# horizontal (H) and vertical (V) - laid in alternating rows. The
# fundamental domain is a 2x3 unit cell containing one H brick at the
# bottom and two V bricks stacked above; tiling by translation gives the
# classic brick-and-plank running-bond pattern where every H row is
# capped above and below by a row of V bricks.
#
# The tiling is non-edge-to-edge in the same way Pythagorean is: each H
# brick's long edge (length 2) is met at its midpoint by the short edges
# (length 1) of two V bricks. To make the exact-edge-matching adjacency
# builder work, H bricks are modelled as 6-vertex polygons (four corners
# plus two collinear mid-long-edge vertices), so every polygon edge ends
# at a vertex shared with its neighbour. V bricks stay 4-vertex - their
# long edges match the long edges of adjacent V bricks exactly.
#
# Vertex configurations in the infinite tiling:
#   3-valent (H, V, V) at every H long-edge midpoint
#   4-valent (H, H, V, V) at every brick corner

SPECS = {
    "herringbone": ReferenceFamilySpec(
        geometry="herringbone",
        display_name="Herringbone",
        source_urls=("https://en.wikipedia.org/wiki/Herringbone_pattern",),
        canonical_root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("herringbone-horizontal", "herringbone-vertical"),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=27,
                expected_kind_counts=(
                    ("herringbone-horizontal", 9),
                    ("herringbone-vertical", 18),
                ),
                expected_adjacency_pairs=(
                    ("herringbone-horizontal", "herringbone-horizontal"),
                    ("herringbone-horizontal", "herringbone-vertical"),
                    ("herringbone-vertical", "herringbone-vertical"),
                ),
                expected_degree_histogram=(
                    (2, 2),
                    (3, 10),
                    (4, 9),
                    (5, 4),
                    (6, 2),
                ),
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=3,
            slot_vocabulary=("h0", "v0", "v1"),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                # 4-valent at brick corners (H, H, V, V)
                (
                    "herringbone-horizontal",
                    "herringbone-horizontal",
                    "herringbone-vertical",
                    "herringbone-vertical",
                ),
                # 3-valent at H long-edge midpoints (H, V, V)
                (
                    "herringbone-horizontal",
                    "herringbone-vertical",
                    "herringbone-vertical",
                ),
            ),
            expected_interior_vertex_configuration_frequencies=(
                # In the open-boundary 3x3 sample the verifier counts
                # 10 brick-corner (4-valent) and 15 long-edge-midpoint
                # (3-valent) interior vertices.
                (
                    (
                        "herringbone-horizontal",
                        "herringbone-horizontal",
                        "herringbone-vertical",
                        "herringbone-vertical",
                    ),
                    10,
                ),
                (
                    (
                        "herringbone-horizontal",
                        "herringbone-vertical",
                        "herringbone-vertical",
                    ),
                    15,
                ),
            ),
        ),
    ),
}
