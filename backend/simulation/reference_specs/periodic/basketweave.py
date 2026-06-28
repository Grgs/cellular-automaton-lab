from __future__ import annotations

from backend.simulation.reference_specs.types import (
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)

# Basketweave tiling: 2:1 rectangular bricks of a single kind arranged so
# that pairs of parallel bricks form 50x50 blocks, then blocks alternate
# orientation in a checkerboard pattern. The 100x100 unit cell contains
# eight bricks: four horizontal and four vertical.
#
# Like Pythagorean and Herringbone the tiling is non-edge-to-edge: each
# brick has exactly one long edge whose midpoint hosts a T-junction with
# a perpendicular brick's short edge. To make the exact-edge-matching
# adjacency builder work, every brick is modelled as a 5-vertex polygon
# (four corners plus a single mid-edge vertex on that long edge), so
# every polygon edge ends at a vertex shared with its neighbour.
#
# Vertex configurations in the infinite tiling (with all bricks of one
# kind):
#   3-valent (brick, brick, brick) at every T-junction
#   4-valent (brick, brick, brick, brick) at every block corner where
#   four bricks meet

SPECS = {
    "basketweave": ReferenceFamilySpec(
        geometry="basketweave",
        display_name="Basketweave",
        source_urls=("https://en.wikipedia.org/wiki/Basket_weave_(pattern)",),
        root_seed_policy="descriptor-driven open-boundary 3x3 sample",
        allowed_public_cell_kinds=("basketweave-brick",),
        required_metadata=(),
        sample_mode="grid",
        depth_expectations={
            3: ReferenceDepthExpectation(
                exact_total_cells=72,
                expected_kind_counts=(("basketweave-brick", 72),),
                expected_adjacency_pairs=(("basketweave-brick", "basketweave-brick"),),
                expected_degree_histogram=(
                    (2, 4),
                    (3, 8),
                    (4, 20),
                    (5, 40),
                ),
            ),
        },
        periodic_descriptor=PeriodicDescriptorExpectation(
            face_template_count=8,
            slot_vocabulary=("h1", "h2", "h3", "h4", "v1", "v2", "v3", "v4"),
            id_pattern="{prefix}:{slot}:{x}:{y}",
            row_offset_x=0.0,
            expected_interior_vertex_configurations=(
                ("basketweave-brick", "basketweave-brick", "basketweave-brick"),
                (
                    "basketweave-brick",
                    "basketweave-brick",
                    "basketweave-brick",
                    "basketweave-brick",
                ),
            ),
            expected_interior_vertex_configuration_frequencies=(
                # Open-boundary 3x3 sample reported by the verifier.
                (
                    ("basketweave-brick", "basketweave-brick", "basketweave-brick"),
                    60,
                ),
                (
                    (
                        "basketweave-brick",
                        "basketweave-brick",
                        "basketweave-brick",
                        "basketweave-brick",
                    ),
                    25,
                ),
            ),
        ),
    ),
}
