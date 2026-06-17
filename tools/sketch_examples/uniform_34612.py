"""Sketch for the 2-uniform 3-4-6-12 tiling.

The rectangular two-row unit contains four triangles, twelve squares, six
hexagons, and two dodecagons. It packages two half-offset primitive rows so
the descriptor can use an axis-aligned repeat while preserving the 3.4.6.4
and 4.6.12 vertex orbits.

Coordinates are normalized from the canonical ``2-uniform_n1.svg`` diagram:
https://commons.wikimedia.org/wiki/File:2-uniform_n1.svg
"""

import math
from typing import Any

GEOMETRY = "uniform-3-4-6-12"
LABEL = "2-uniform 3-4-6-12"
BASE_EDGE = 52.0
HALF_EDGE = BASE_EDGE / 2
TRIANGLE_HEIGHT = round(HALF_EDGE * math.sqrt(3), 6)
CELL_WIDTH = round(4 * HALF_EDGE + 4 * TRIANGLE_HEIGHT, 6)
CELL_HEIGHT = round(12 * HALF_EDGE + 4 * TRIANGLE_HEIGHT, 6)
ROW_OFFSET_X = 0.0


def _point(
    x_half_edges: int,
    x_triangle_heights: int,
    y_half_edges: int,
    y_triangle_heights: int,
) -> tuple[float, float]:
    return (
        round(x_half_edges * HALF_EDGE + x_triangle_heights * TRIANGLE_HEIGHT, 6),
        round(y_half_edges * HALF_EDGE + y_triangle_heights * TRIANGLE_HEIGHT, 6),
    )


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


FACES = [
    _face("t1", "triangle", "t", (_point(1, 2, 2, 1), _point(2, 2, 2, 0), _point(3, 2, 2, 1))),
    _face(
        "t2",
        "triangle",
        "t",
        (_point(1, 0, 4, 1), _point(0, 0, 4, 2), _point(-1, 0, 4, 1)),
        repeat_x_extra=1,
    ),
    _face(
        "t3",
        "triangle",
        "t",
        (_point(0, 0, 8, 2), _point(1, 0, 8, 3), _point(-1, 0, 8, 3)),
        repeat_x_extra=1,
    ),
    _face("t4", "triangle", "t", (_point(1, 2, 10, 3), _point(3, 2, 10, 3), _point(2, 2, 10, 4))),
    _face(
        "s1",
        "square",
        "s",
        (_point(1, 2, 4, 1), _point(1, 2, 2, 1), _point(3, 2, 2, 1), _point(3, 2, 4, 1)),
    ),
    _face(
        "s2",
        "square",
        "s",
        (_point(1, 1, 5, 1), _point(0, 1, 5, 2), _point(0, 0, 4, 2), _point(1, 0, 4, 1)),
    ),
    _face(
        "s3",
        "square",
        "s",
        (_point(1, 2, 2, 1), _point(1, 1, 1, 1), _point(2, 1, 1, 0), _point(2, 2, 2, 0)),
    ),
    _face(
        "s4",
        "square",
        "s",
        (_point(3, 3, 5, 1), _point(3, 4, 4, 1), _point(4, 4, 4, 2), _point(4, 3, 5, 2)),
    ),
    _face(
        "s5",
        "square",
        "s",
        (_point(3, 2, 2, 1), _point(2, 2, 2, 0), _point(2, 3, 1, 0), _point(3, 3, 1, 1)),
    ),
    _face(
        "s6",
        "square",
        "s",
        (_point(1, 0, 4, 1), _point(-1, 0, 4, 1), _point(-1, 0, 2, 1), _point(1, 0, 2, 1)),
        repeat_x_extra=1,
    ),
    _face(
        "s7",
        "square",
        "s",
        (_point(0, 1, 7, 2), _point(1, 1, 7, 3), _point(1, 0, 8, 3), _point(0, 0, 8, 2)),
    ),
    _face(
        "s8",
        "square",
        "s",
        (_point(4, 3, 7, 2), _point(4, 4, 8, 2), _point(3, 4, 8, 3), _point(3, 3, 7, 3)),
    ),
    _face(
        "s9",
        "square",
        "s",
        (_point(1, 2, 8, 3), _point(3, 2, 8, 3), _point(3, 2, 10, 3), _point(1, 2, 10, 3)),
    ),
    _face(
        "s10",
        "square",
        "s",
        (_point(1, 0, 8, 3), _point(1, 0, 10, 3), _point(-1, 0, 10, 3), _point(-1, 0, 8, 3)),
        repeat_x_extra=1,
    ),
    _face(
        "s11",
        "square",
        "s",
        (_point(1, 2, 10, 3), _point(2, 2, 10, 4), _point(2, 1, 11, 4), _point(1, 1, 11, 3)),
    ),
    _face(
        "s12",
        "square",
        "s",
        (_point(3, 2, 10, 3), _point(3, 3, 11, 3), _point(2, 3, 11, 4), _point(2, 2, 10, 4)),
    ),
    _face(
        "h1",
        "hexagon",
        "h",
        (
            _point(1, 2, 4, 1),
            _point(1, 1, 5, 1),
            _point(1, 0, 4, 1),
            _point(1, 0, 2, 1),
            _point(1, 1, 1, 1),
            _point(1, 2, 2, 1),
        ),
    ),
    _face(
        "h2",
        "hexagon",
        "h",
        (
            _point(3, 2, 4, 1),
            _point(3, 2, 2, 1),
            _point(3, 3, 1, 1),
            _point(3, 4, 2, 1),
            _point(3, 4, 4, 1),
            _point(3, 3, 5, 1),
        ),
    ),
    _face(
        "h3",
        "hexagon",
        "h",
        (
            _point(0, 1, 5, 2),
            _point(0, 1, 7, 2),
            _point(0, 0, 8, 2),
            _point(0, -1, 7, 2),
            _point(0, -1, 5, 2),
            _point(0, 0, 4, 2),
        ),
        repeat_x_extra=1,
    ),
    _face(
        "h4",
        "hexagon",
        "h",
        (
            _point(2, 2, 2, 0),
            _point(2, 1, 1, 0),
            _point(2, 1, -1, 0),
            _point(2, 2, -2, 0),
            _point(2, 3, -1, 0),
            _point(2, 3, 1, 0),
        ),
        repeat_y_extra=1,
    ),
    _face(
        "h5",
        "hexagon",
        "h",
        (
            _point(1, 1, 7, 3),
            _point(1, 2, 8, 3),
            _point(1, 2, 10, 3),
            _point(1, 1, 11, 3),
            _point(1, 0, 10, 3),
            _point(1, 0, 8, 3),
        ),
    ),
    _face(
        "h6",
        "hexagon",
        "h",
        (
            _point(3, 3, 7, 3),
            _point(3, 4, 8, 3),
            _point(3, 4, 10, 3),
            _point(3, 3, 11, 3),
            _point(3, 2, 10, 3),
            _point(3, 2, 8, 3),
        ),
    ),
    _face(
        "d1",
        "dodecagon",
        "d",
        (
            _point(1, 1, 1, 1),
            _point(1, 0, 2, 1),
            _point(-1, 0, 2, 1),
            _point(-1, -1, 1, 1),
            _point(-2, -1, 1, 0),
            _point(-2, -1, -1, 0),
            _point(-1, -1, -1, -1),
            _point(-1, 0, -2, -1),
            _point(1, 0, -2, -1),
            _point(1, 1, -1, -1),
            _point(2, 1, -1, 0),
            _point(2, 1, 1, 0),
        ),
        repeat_x_extra=1,
        repeat_y_extra=1,
    ),
    _face(
        "d2",
        "dodecagon",
        "d",
        (
            _point(1, 2, 4, 1),
            _point(3, 2, 4, 1),
            _point(3, 3, 5, 1),
            _point(4, 3, 5, 2),
            _point(4, 3, 7, 2),
            _point(3, 3, 7, 3),
            _point(3, 2, 8, 3),
            _point(1, 2, 8, 3),
            _point(1, 1, 7, 3),
            _point(0, 1, 7, 2),
            _point(0, 1, 5, 2),
            _point(1, 1, 5, 1),
        ),
    ),
]
