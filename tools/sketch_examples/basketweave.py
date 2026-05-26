"""Example sketch: classic 2:1 Basketweave tiling.

Run with:

    py tools/sketch_tiling.py tools/sketch_examples/basketweave.py \\
        --svg /tmp/sketch.svg \\
        --json /tmp/sketch.json \\
        --reference-spec /tmp/spec.py

Two 2:1 rectangular bricks - horizontal (50x25) and vertical (25x50) -
arranged so that pairs of parallel bricks form 50x50 blocks, with the
blocks themselves checkerboarded by orientation. The fundamental cell is
100x100 and contains 8 bricks: four horizontal and four vertical.

Like Pythagorean and Herringbone, the tiling is non-edge-to-edge: every
brick has exactly one long edge whose midpoint is a T-junction where a
perpendicular brick's short edge lands. To make every edge match
exactly, each brick is modeled as a 5-vertex polygon (four corners plus
a single mid-edge vertex on the long edge that hosts the T-junction).

For a 3x3 patch, the reported interior vertex configurations are:
    60x  (basketweave-brick,) * 3   - 3-brick T-junction vertices
    25x  (basketweave-brick,) * 4   - 4-brick block-corner vertices
"""

from typing import Any

SHORT = 25.0
LONG = 2 * SHORT  # 50.0

GEOMETRY = "basketweave"
LABEL = "Basketweave"
BASE_EDGE = SHORT
CELL_WIDTH = 2 * LONG  # 100
CELL_HEIGHT = 2 * LONG  # 100
ROW_OFFSET_X = 0.0


def _brick(vertices: tuple[tuple[float, float], ...], slot: str) -> dict[str, Any]:
    return {"slot": slot, "kind": "basketweave-brick", "prefix": "b", "vertices": vertices}


# Block A (top-left, 0-50 x 0-50): two horizontal bricks stacked.
# Block B (top-right, 50-100 x 0-50): two vertical bricks side-by-side.
# Block C (bottom-left, 0-50 x 50-100): two vertical bricks side-by-side.
# Block D (bottom-right, 50-100 x 50-100): two horizontal bricks stacked.

FACES = [
    # H1: top of Block A. Top edge meets V3/V4 corner (wrap from above) at (25, 0).
    _brick(((0, 0), (25, 0), (50, 0), (50, 25), (0, 25)), "h1"),
    # H2: bottom of Block A. Bottom edge meets V3/V4 corner at (25, 50).
    _brick(((0, 25), (50, 25), (50, 50), (25, 50), (0, 50)), "h2"),
    # H3: top of Block D. Top edge meets V1/V2 corner at (75, 50).
    _brick(((50, 50), (75, 50), (100, 50), (100, 75), (50, 75)), "h3"),
    # H4: bottom of Block D. Bottom edge meets V1/V2 corner (wrap from below) at (75, 100).
    _brick(((50, 75), (100, 75), (100, 100), (75, 100), (50, 100)), "h4"),
    # V1: left of Block B. Left edge meets H1/H2 corner at (50, 25).
    _brick(((50, 0), (75, 0), (75, 50), (50, 50), (50, 25)), "v1"),
    # V2: right of Block B. Right edge meets H1/H2 corner (wrap from right) at (100, 25).
    _brick(((75, 0), (100, 0), (100, 25), (100, 50), (75, 50)), "v2"),
    # V3: left of Block C. Left edge meets H3/H4 corner (wrap from left) at (0, 75).
    _brick(((0, 50), (25, 50), (25, 100), (0, 100), (0, 75)), "v3"),
    # V4: right of Block C. Right edge meets H3/H4 corner at (50, 75).
    _brick(((25, 50), (50, 50), (50, 75), (50, 100), (25, 100)), "v4"),
]
