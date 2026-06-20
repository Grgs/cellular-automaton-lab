"""Sketch for 2-uniform #19 variant 1 [3^6; 3^4.6].

Start with the equilateral-triangle lattice and replace the six triangles
around every ``(3i, 3j)`` lattice point with a regular hexagon.  This is the
triangular hexagon-centre arrangement shown in the canonical
``2-uniform_n19.svg`` diagram.  Each primitive cell has one hexagon, twelve
triangles, six ``3^4.6`` vertices, and two ``3^6`` vertices.

The installed rectangular repeat packages four primitive cells so the
default board has balanced proportions instead of rendering as a strip.

Reference image and catalog numbering:
https://commons.wikimedia.org/wiki/File:2-uniform_n19.svg
"""

import math
from typing import Any

EDGE = 1.0
H = round(EDGE * math.sqrt(3) / 2, 6)

GEOMETRY = "uniform-2-19-v1-36-346"
LABEL = "2-uniform #19 variant 1 (3^6; 3^4.6)"
BASE_EDGE = EDGE
CELL_WIDTH = 6 * EDGE
CELL_HEIGHT = 6 * H
ROW_OFFSET_X = 0.0


def _point(i: int, j: int) -> tuple[float, float]:
    return (round(EDGE * (i + j / 2), 6), round(H * j, 6))


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
    return i % 3 == 0 and j % 3 == 0


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
    _hexagon("hex-00", (0, 0)),
    _hexagon("hex-30", (3, 0)),
    _hexagon("hex-03", (0, 3)),
    _hexagon("hex-33", (3, 3)),
]

for j in range(6):
    for i in range(6):
        up = ((i, j), (i + 1, j), (i, j + 1))
        if not _touches_hex_center(up):
            FACES.append(_triangle(f"u{i}{j}", tuple(_point(*vertex) for vertex in up)))

        down = ((i + 1, j), (i + 1, j + 1), (i, j + 1))
        if not _touches_hex_center(down):
            FACES.append(_triangle(f"d{i}{j}", tuple(_point(*vertex) for vertex in down)))
