"""Example sketch: square-grid tiling by right-isosceles triangles.

Each square lattice cell is split along the same diagonal into two congruent
45-45-90 triangles. This gives the catalog a lightweight non-regular triangle
topology that is visually and graph-theoretically distinct from the existing
equilateral triangular grid.

Run with:

    py tools/sketch_tiling.py tools/sketch_examples/right_triangle.py \
        --svg /tmp/sketch.svg \
        --json /tmp/sketch.json \
        --reference-spec /tmp/spec.py
"""

from typing import Any

EDGE = 50.0

GEOMETRY = "right-triangle"
LABEL = "Right-Triangle"
BASE_EDGE = EDGE
CELL_WIDTH = EDGE
CELL_HEIGHT = EDGE
ROW_OFFSET_X = 0.0


def _tri(vertices: tuple[tuple[float, float], ...], slot: str) -> dict[str, Any]:
    return {"slot": slot, "kind": "right-triangle", "prefix": "t", "vertices": vertices}


FACES = [
    _tri(((0.0, 0.0), (EDGE, 0.0), (EDGE, EDGE)), "lower"),
    _tri(((0.0, 0.0), (EDGE, EDGE), (0.0, EDGE)), "upper"),
]
