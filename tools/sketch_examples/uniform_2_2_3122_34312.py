"""Sketch for 2-uniform #2 [3.12^2; 3.4.3.12].

The canonical ``2-uniform_n2.svg`` places regular dodecagons on a square
lattice with one axis-aligned square in each four-dodecagon gap.  Four
equilateral triangles surround that square.  The exact lattice period is
``2 + sqrt(3)`` edge lengths in each direction.

Reference image and catalog numbering:
https://commons.wikimedia.org/wiki/File:2-uniform_n2.svg
"""

import math
from typing import Any

EDGE = 1.0
SQRT3 = math.sqrt(3)
EXTENT = round(1 + SQRT3 / 2, 6)
PERIOD = round(2 * EXTENT, 6)
INNER = round((1 + SQRT3) / 2, 6)
OUTER = round(PERIOD - INNER, 6)
MID = EXTENT

GEOMETRY = "uniform-2-2-3122-34312"
LABEL = "2-uniform #2 (3.12^2; 3.4.3.12)"
BASE_EDGE = EDGE
CELL_WIDTH = PERIOD
CELL_HEIGHT = PERIOD
ROW_OFFSET_X = 0.0


def _regular_dodecagon() -> tuple[tuple[float, float], ...]:
    radius = EDGE / (2 * math.sin(math.pi / 12))
    return tuple(
        (
            round(radius * math.cos(math.radians(angle)), 6),
            round(radius * math.sin(math.radians(angle)), 6),
        )
        for angle in range(15, 360, 30)
    )


FACES: list[dict[str, Any]] = [
    {
        "slot": "dodecagon",
        "kind": "dodecagon",
        "prefix": "d",
        "vertices": _regular_dodecagon(),
        "repeat_x_extra": 1,
        "repeat_y_extra": 1,
    },
    {
        "slot": "square",
        "kind": "square",
        "prefix": "s",
        "vertices": ((INNER, INNER), (OUTER, INNER), (OUTER, OUTER), (INNER, OUTER)),
    },
    {
        "slot": "triangle-bottom",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((INNER, INNER), (MID, 0.5), (OUTER, INNER)),
    },
    {
        "slot": "triangle-right",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((OUTER, INNER), (PERIOD - 0.5, MID), (OUTER, OUTER)),
    },
    {
        "slot": "triangle-top",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((OUTER, OUTER), (MID, PERIOD - 0.5), (INNER, OUTER)),
    },
    {
        "slot": "triangle-left",
        "kind": "triangle",
        "prefix": "t",
        "vertices": ((INNER, OUTER), (0.5, MID), (INNER, INNER)),
    },
]
