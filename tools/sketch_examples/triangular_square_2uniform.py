"""Example sketch: the 2-uniform Triangle+Square tiling [3^6; 3^3.4^2].

Run with:

    py tools/sketch_tiling.py tools/sketch_examples/triangular_square_2uniform.py \\
        --svg /tmp/sketch.svg \\
        --json /tmp/sketch.json \\
        --reference-spec /tmp/spec.py

The reported interior vertex configurations should be:
    25x ('square', 'square', 'triangle', 'triangle', 'triangle')
    18x ('triangle', 'triangle', 'triangle', 'triangle', 'triangle', 'triangle')

This file is also the input the unit tests under
``tests/unit/test_sketch_tiling.py`` use to verify the tool against the
backend's reference verifier - keep the geometry consistent if you edit it.
"""

import math
from typing import Any

from tools.sketch_helpers import equilateral_triangle, square

EDGE = 52.0
H = round(EDGE * math.sqrt(3) / 2, 6)  # triangle height with edge 52

GEOMETRY = "triangular-square-2uniform"
LABEL = "2-uniform Triangle+Square (3^6; 3^3.4^2)"
BASE_EDGE = EDGE
CELL_WIDTH = 2 * EDGE
CELL_HEIGHT = 2 * H + EDGE
ROW_OFFSET_X = 0.0


def _tri(vertices: tuple[tuple[float, float], ...], slot: str) -> dict[str, Any]:
    return {"slot": slot, "kind": "triangle", "prefix": "t", "vertices": vertices}


def _sq(vertices: tuple[tuple[float, float], ...], slot: str) -> dict[str, Any]:
    return {"slot": slot, "kind": "square", "prefix": "s", "vertices": vertices}


FACES = [
    # Block A row 1: triangular tiling, base on y=0, apexes at y=H (half-integer x).
    # Using equilateral_triangle so we never spell out sqrt(3)/2 by hand and so
    # all coordinates land on the same 6-decimal grid the validator uses.
    _tri(equilateral_triangle((0, 0), (EDGE, 0), side="above"), "ua"),
    _tri(equilateral_triangle((EDGE, 0), (2 * EDGE, 0), side="above"), "ub"),
    # Down-triangle inside the cell: apex at (EDGE, 0), base on row 1 top.
    _tri(equilateral_triangle((EDGE / 2, H), (3 * EDGE / 2, H), side="below"), "da"),
    # Down-triangle straddling the left edge of the cell; repeat_x_extra=1
    # so the rightmost cell of any finite patch is fully covered.
    {
        **_tri(equilateral_triangle((-EDGE / 2, H), (EDGE / 2, H), side="below"), "dleft"),
        "repeat_x_extra": 1,
    },
    # Block A row 2: triangular tiling, base at y=H, apex at y=2H (integer x).
    _tri(equilateral_triangle((EDGE / 2, H), (3 * EDGE / 2, H), side="above"), "uc"),
    _tri(equilateral_triangle((0, 2 * H), (EDGE, 2 * H), side="below"), "db"),
    _tri(equilateral_triangle((EDGE, 2 * H), (2 * EDGE, 2 * H), side="below"), "dc"),
    {
        **_tri(equilateral_triangle((-EDGE / 2, H), (EDGE / 2, H), side="above"), "uleftr2"),
        "repeat_x_extra": 1,
    },
    # Block B: row of squares.
    _sq(square((0, 2 * H), EDGE), "sa"),
    _sq(square((EDGE, 2 * H), EDGE), "sb"),
]
