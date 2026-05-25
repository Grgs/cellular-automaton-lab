"""Example sketch: the 2-uniform Triangle+Square tiling [3^6; 3^3.4^2].

Run with:

    py tools/sketch_tiling.py tools/sketch_examples/triangular_square_2uniform.py \
        --svg /tmp/sketch.svg --json /tmp/sketch.json

The reported interior vertex configurations should be:
    25x ('square', 'square', 'triangle', 'triangle', 'triangle')
    18x ('triangle', 'triangle', 'triangle', 'triangle', 'triangle', 'triangle')
"""

import math

EDGE = 52.0
H = round(EDGE * math.sqrt(3) / 2, 6)  # triangle height with edge 52

GEOMETRY = "triangular-square-2uniform"
LABEL = "2-uniform Triangle+Square (3^6; 3^3.4^2)"
BASE_EDGE = EDGE
CELL_WIDTH = 2 * EDGE
CELL_HEIGHT = 2 * H + EDGE
ROW_OFFSET_X = 0.0

FACES = [
    # Block A row 1: triangular tiling, base on y=0, apexes at y=H (half-integer x)
    {
        "slot": "ua",
        "kind": "triangle",
        "prefix": "t",
        "vertices": [(0, 0), (EDGE, 0), (EDGE / 2, H)],
    },
    {
        "slot": "ub",
        "kind": "triangle",
        "prefix": "t",
        "vertices": [(EDGE, 0), (2 * EDGE, 0), (3 * EDGE / 2, H)],
    },
    {
        "slot": "da",
        "kind": "triangle",
        "prefix": "t",
        "vertices": [(EDGE / 2, H), (3 * EDGE / 2, H), (EDGE, 0)],
    },
    {  # straddles the left edge of the cell; repeat_x_extra=1 covers the right
        "slot": "dleft",
        "kind": "triangle",
        "prefix": "t",
        "vertices": [(-EDGE / 2, H), (EDGE / 2, H), (0, 0)],
        "repeat_x_extra": 1,
    },
    # Block A row 2: triangular tiling, base at y=H, apex at y=2H (integer x)
    {
        "slot": "uc",
        "kind": "triangle",
        "prefix": "t",
        "vertices": [(EDGE / 2, H), (3 * EDGE / 2, H), (EDGE, 2 * H)],
    },
    {
        "slot": "db",
        "kind": "triangle",
        "prefix": "t",
        "vertices": [(0, 2 * H), (EDGE, 2 * H), (EDGE / 2, H)],
    },
    {
        "slot": "dc",
        "kind": "triangle",
        "prefix": "t",
        "vertices": [(EDGE, 2 * H), (2 * EDGE, 2 * H), (3 * EDGE / 2, H)],
    },
    {  # straddles left edge; repeat_x_extra=1 covers the right boundary
        "slot": "uleftr2",
        "kind": "triangle",
        "prefix": "t",
        "vertices": [(-EDGE / 2, H), (EDGE / 2, H), (0, 2 * H)],
        "repeat_x_extra": 1,
    },
    # Block B: row of squares
    {
        "slot": "sa",
        "kind": "square",
        "prefix": "s",
        "vertices": [
            (0, 2 * H),
            (EDGE, 2 * H),
            (EDGE, 2 * H + EDGE),
            (0, 2 * H + EDGE),
        ],
    },
    {
        "slot": "sb",
        "kind": "square",
        "prefix": "s",
        "vertices": [
            (EDGE, 2 * H),
            (2 * EDGE, 2 * H),
            (2 * EDGE, 2 * H + EDGE),
            (EDGE, 2 * H + EDGE),
        ],
    },
]
