"""Sketch for 2-uniform tiling #10 [3^6; 3^2.6^2].

Start with the equilateral-triangle lattice and replace the six triangles
around selected lattice vertices with one regular hexagon.  The hexagon
centres use the two-site honeycomb basis ``(0, 0)`` and ``(1, 1)`` under the
translations ``3 * e1`` and ``3 * e2``.  Each hexagon shares three alternating
edges, making every hexagon corner a ``3^2.6^2`` vertex, while the gaps contain
pure ``3^6`` vertices.  One primitive cell contains two hexagons and six
triangles.

Reference image and catalog numbering:
https://commons.wikimedia.org/wiki/File:2-uniform_n10.svg
"""

import math
from typing import Any

EDGE = 52.0
H = round(EDGE * 3**0.5 / 2, 6)
ORIGIN_X = round(EDGE / 7, 6)
ORIGIN_Y = round(EDGE / 11, 6)

GEOMETRY = "uniform-2-10-36-3262"
LABEL = "2-uniform #10 (3^6; 3^2.6^2)"
BASE_EDGE = EDGE
CELL_WIDTH = 3 * EDGE
CELL_HEIGHT = 6 * H
ROW_OFFSET_X = 0.0


def _point(i: int, j: int) -> tuple[float, float]:
    return (
        round(ORIGIN_X + EDGE * (i + j / 2), 6),
        round(ORIGIN_Y + H * j, 6),
    )


def _face(
    slot: str, kind: str, prefix: str, vertices: tuple[tuple[float, float], ...]
) -> dict[str, Any]:
    center_x = sum(x for x, _ in vertices) / len(vertices)
    center_y = sum(y for _, y in vertices) / len(vertices)
    shift_x = -math.floor(center_x / CELL_WIDTH) * CELL_WIDTH
    shift_y = -math.floor(center_y / CELL_HEIGHT) * CELL_HEIGHT
    normalized = tuple((round(x + shift_x, 6), round(y + shift_y, 6)) for x, y in vertices)

    if max(x for x, _ in normalized) > CELL_WIDTH:
        normalized = tuple((round(x - CELL_WIDTH, 6), y) for x, y in normalized)
    if max(y for _, y in normalized) > CELL_HEIGHT:
        normalized = tuple((x, round(y - CELL_HEIGHT, 6)) for x, y in normalized)

    face: dict[str, Any] = {
        "slot": slot,
        "kind": kind,
        "prefix": prefix,
        "vertices": normalized,
    }
    if min(x for x, _ in normalized) < 0:
        face["repeat_x_extra"] = 1
    if min(y for _, y in normalized) < 0:
        face["repeat_y_extra"] = 1
    return face


def _triangle(slot: str, vertices: tuple[tuple[float, float], ...]) -> dict[str, Any]:
    return _face(slot, "triangle", "t", vertices)


def _is_hex_center(i: int, j: int) -> bool:
    return (i % 3, j % 3) in ((0, 0), (1, 1))


def _touches_hex_center(vertices: tuple[tuple[int, int], ...]) -> bool:
    return any(_is_hex_center(i, j) for i, j in vertices)


def _hexagon(slot: str, center: tuple[int, int]) -> dict[str, Any]:
    i, j = center
    offsets = ((1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1))
    return _face(
        slot,
        "hexagon",
        "h",
        tuple(_point(i + di, j + dj) for di, dj in offsets),
    )


FACES: list[dict[str, Any]] = [
    _hexagon("hex_a", (0, 0)),
    _hexagon("hex_b", (1, 1)),
    _hexagon("hex_c", (0, 3)),
    _hexagon("hex_d", (1, 4)),
]

for j in range(6):
    for i in range(3):
        up = ((i, j), (i + 1, j), (i, j + 1))
        if not _touches_hex_center(up):
            FACES.append(_triangle(f"u{i}{j}", tuple(_point(*vertex) for vertex in up)))

        down = ((i + 1, j), (i + 1, j + 1), (i, j + 1))
        if not _touches_hex_center(down):
            FACES.append(_triangle(f"d{i}{j}", tuple(_point(*vertex) for vertex in down)))
