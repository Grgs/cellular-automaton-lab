"""Sketch for 3-uniform #4 [3^6; 3^2.6^2; 6^3].

The integer-lattice face templates are reduced from the canonical
``3-uniform_4.svg`` catalog diagram.  Horizontal lattice steps are triangle
altitudes and vertical steps are half-edges, so every listed polygon is an
exact regular triangle or hexagon after scaling.

One primitive rectangular repeat contains 12 triangles and 6 hexagons.  The
installed cell packages two repeats side by side to keep the default board
balanced rather than strip-shaped.

Reference image and catalog numbering:
https://commons.wikimedia.org/wiki/File:3-uniform_4.svg
"""

import math
from typing import Any

EDGE = 1.0
DX = round(EDGE * math.sqrt(3) / 2, 6)
DY = EDGE / 2

GEOMETRY = "uniform-3-4-36-3262-63"
LABEL = "3-uniform #4 (3^6; 3^2.6^2; 6^3)"
BASE_EDGE = EDGE
CELL_WIDTH = 8 * DX
CELL_HEIGHT = 12 * DY
ROW_OFFSET_X = 0.0

_BASE_FACE_LATTICE: tuple[tuple[str, tuple[tuple[int, int], ...]], ...] = (
    ("hexagon", ((1, -1), (2, 0), (2, 2), (1, 3), (0, 2), (0, 0))),
    ("hexagon", ((1, 5), (0, 6), (-1, 5), (-1, 3), (0, 2), (1, 3))),
    ("hexagon", ((1, 5), (1, 3), (2, 2), (3, 3), (3, 5), (2, 6))),
    ("hexagon", ((1, 9), (1, 11), (0, 12), (-1, 11), (-1, 9), (0, 8))),
    ("hexagon", ((1, 9), (2, 8), (3, 9), (3, 11), (2, 12), (1, 11))),
    ("hexagon", ((2, 8), (2, 6), (3, 5), (4, 6), (4, 8), (3, 9))),
    ("triangle", ((1, 5), (1, 7), (0, 6))),
    ("triangle", ((1, 7), (0, 8), (0, 6))),
    ("triangle", ((1, 7), (1, 5), (2, 6))),
    ("triangle", ((1, 7), (1, 9), (0, 8))),
    ("triangle", ((1, 7), (2, 6), (2, 8))),
    ("triangle", ((1, 7), (2, 8), (1, 9))),
    ("triangle", ((2, 0), (3, -1), (3, 1))),
    ("triangle", ((3, 1), (2, 2), (2, 0))),
    ("triangle", ((3, 1), (3, -1), (4, 0))),
    ("triangle", ((3, 1), (3, 3), (2, 2))),
    ("triangle", ((3, 1), (4, 2), (3, 3))),
    ("triangle", ((4, 2), (3, 1), (4, 0))),
)


def _vertices(
    lattice_vertices: tuple[tuple[int, int], ...], column: int
) -> tuple[tuple[float, float], ...]:
    return tuple((round((i + 4 * column) * DX, 6), round(j * DY, 6)) for i, j in lattice_vertices)


FACES: list[dict[str, Any]] = []
for column in range(2):
    for index, (kind, lattice_vertices) in enumerate(_BASE_FACE_LATTICE, start=1):
        vertices = _vertices(lattice_vertices, column)
        face: dict[str, Any] = {
            "slot": f"{kind[0]}{column}-{index}",
            "kind": kind,
            "prefix": "h" if kind == "hexagon" else "t",
            "vertices": vertices,
        }
        if min(x for x, _ in vertices) < 0:
            face["repeat_x_extra"] = 1
        if min(y for _, y in vertices) < 0:
            face["repeat_y_extra"] = 1
        FACES.append(face)
