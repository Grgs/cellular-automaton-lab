"""Sketch for 2-uniform #12 [3^2.6^2; 3^4.6].

Rows of edge-sharing pointy-top hexagons alternate by half a horizontal
period. Four equilateral triangles fill each gap between adjacent rows.
The construction follows the canonical ``2-uniform_n12.svg`` diagram:
https://commons.wikimedia.org/wiki/File:2-uniform_n12.svg
"""

import math
from typing import Any

from tools.sketch_helpers import regular_hexagon

EDGE = 1.0
HALF_SQRT3 = round(math.sqrt(3) / 2, 6)
SQRT3 = round(2 * HALF_SQRT3, 6)

GEOMETRY = "uniform-2-12-3262-346"
LABEL = "2-uniform #12 (3^2.6^2; 3^4.6)"
BASE_EDGE = EDGE
CELL_WIDTH = 2 * SQRT3
CELL_HEIGHT = 5.0
ROW_OFFSET_X = 0.0


def _face(
    slot: str,
    kind: str,
    prefix: str,
    vertices: tuple[tuple[float, float], ...],
    *,
    repeat_x_extra: int = 0,
    repeat_y_extra: int = 0,
) -> dict[str, Any]:
    face: dict[str, Any] = {
        "slot": slot,
        "kind": kind,
        "prefix": prefix,
        "vertices": vertices,
    }
    if repeat_x_extra:
        face["repeat_x_extra"] = repeat_x_extra
    if repeat_y_extra:
        face["repeat_y_extra"] = repeat_y_extra
    return face


_BASE_FACES = [
    _face(
        "hex",
        "hexagon",
        "h",
        regular_hexagon((HALF_SQRT3, 1.0), EDGE, orientation="pointy-top"),
        repeat_y_extra=1,
    ),
    _face(
        "t1",
        "triangle",
        "t",
        ((0.0, 1.5), (HALF_SQRT3, 2.0), (0.0, 2.5)),
        repeat_x_extra=1,
    ),
    _face(
        "t2",
        "triangle",
        "t",
        ((HALF_SQRT3, 2.0), (HALF_SQRT3, 3.0), (0.0, 2.5)),
        repeat_x_extra=1,
    ),
    _face(
        "t3",
        "triangle",
        "t",
        ((HALF_SQRT3, 2.0), (SQRT3, 1.5), (SQRT3, 2.5)),
    ),
    _face(
        "t4",
        "triangle",
        "t",
        ((HALF_SQRT3, 2.0), (SQRT3, 2.5), (HALF_SQRT3, 3.0)),
    ),
    _face(
        "hex-shifted",
        "hexagon",
        "h",
        regular_hexagon((0.0, 3.5), EDGE, orientation="pointy-top"),
        repeat_x_extra=1,
    ),
    _face(
        "t5",
        "triangle",
        "t",
        ((0.0, 4.5), (HALF_SQRT3, 4.0), (HALF_SQRT3, 5.0)),
        repeat_x_extra=1,
    ),
    _face(
        "t6",
        "triangle",
        "t",
        ((0.0, 4.5), (HALF_SQRT3, 5.0), (0.0, 5.5)),
        repeat_x_extra=1,
    ),
    _face(
        "t7",
        "triangle",
        "t",
        ((HALF_SQRT3, 4.0), (SQRT3, 4.5), (HALF_SQRT3, 5.0)),
    ),
    _face(
        "t8",
        "triangle",
        "t",
        ((SQRT3, 4.5), (SQRT3, 5.5), (HALF_SQRT3, 5.0)),
    ),
]

FACES: list[dict[str, Any]] = []
for column in range(2):
    offset_x = column * SQRT3
    for base_face in _BASE_FACES:
        face = {
            **base_face,
            "slot": f"{base_face['slot']}-{column + 1}",
            "vertices": tuple((x + offset_x, y) for x, y in base_face["vertices"]),
        }
        if column:
            face.pop("repeat_x_extra", None)
        FACES.append(face)
