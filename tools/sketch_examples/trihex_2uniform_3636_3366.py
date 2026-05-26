"""Example sketch: the 2-uniform Trihex tiling [3.6.3.6; 3^2.6^2].

Construction: rows of pointy-top hexagons share vertical edges within
each row, creating (3^2.6^2) vertices at the shared corners. Between
rows, hexagons touch vertex-to-vertex (top of lower hex = bottom of
upper hex), with diamond-shaped gaps to the sides filled by pairs of
equilateral triangles. The vertices where two rows of hexes meet
end-on-end are (3.6.3.6) vertices.

Unit cell: width sqrt(3) (one hex column), height 2 (one row period).
Contains 1 full hexagon (centered) plus 2 triangles (forming the
diamond at the upper-right corner of the cell, which extends slightly
outside the cell on its NE/NW/SE faces; periodic copies tile the rest).
"""

import math
from typing import Any

from tools.sketch_helpers import regular_hexagon

EDGE = 1.0
# Compute HALF first then derive SQRT3 to keep 2*HALF_SQRT3 == SQRT3 exactly
# after the helpers' 6-decimal rounding (avoids spurious 1e-6 vertex drift).
HALF_SQRT3 = round(math.sqrt(3) / 2, 6)
SQRT3 = round(HALF_SQRT3 * 2, 6)

GEOMETRY = "trihex-2uniform-3636-3366"
LABEL = "2-uniform Trihex (3.6.3.6; 3^2.6^2)"
BASE_EDGE = EDGE
CELL_WIDTH = SQRT3
CELL_HEIGHT = 2.0
ROW_OFFSET_X = 0.0


def _hex(vertices: tuple[tuple[float, float], ...], slot: str) -> dict[str, Any]:
    return {"slot": slot, "kind": "hexagon", "prefix": "h", "vertices": vertices}


def _tri(vertices: tuple[tuple[float, float], ...], slot: str) -> dict[str, Any]:
    return {"slot": slot, "kind": "triangle", "prefix": "t", "vertices": vertices}


# Hexagon centered at (sqrt3/2, 1): pointy-top, edge=1.
HEX = regular_hexagon((HALF_SQRT3, 1.0), EDGE, orientation="pointy-top")

# Diamond at upper-right corner of cell, between row-y=1 hex (sqrt3/2, 1)
# and row-y=1 hex (3*sqrt3/2, 1) (shared edge x=sqrt3, y in [0.5, 1.5]),
# and row-y=3 hexes (sqrt3/2, 3) and (3*sqrt3/2, 3) above.
# Diamond corners:
#   bottom (sqrt3, 1.5) - shared (3^2.6^2) vertex of row-y=1 hexes
#   left (sqrt3/2, 2)   - top of (sqrt3/2, 1) = bottom of (sqrt3/2, 3)
#   top (sqrt3, 2.5)    - shared (3^2.6^2) vertex of row-y=3 hexes
#   right (3*sqrt3/2, 2)- top of (3*sqrt3/2, 1) = bottom of (3*sqrt3/2, 3)
# Split by vertical edge (sqrt3, 1.5)->(sqrt3, 2.5) into 2 triangles.
TRI_LEFT = (
    (SQRT3, 1.5),
    (HALF_SQRT3, 2.0),
    (SQRT3, 2.5),
)
TRI_RIGHT = (
    (SQRT3, 1.5),
    (SQRT3, 2.5),
    (3 * HALF_SQRT3, 2.0),
)


FACES = [
    _hex(HEX, "hex"),
    _tri(TRI_LEFT, "tl"),
    _tri(TRI_RIGHT, "tr"),
]
