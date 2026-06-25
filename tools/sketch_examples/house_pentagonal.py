"""Example sketch: "House" monohedral convex pentagonal tiling (Type 1).

The house / home-plate pentagon: a unit square with a symmetric 45-degree
roof on top. Interior angles are 90 / 90 / 135 / 90 / 135 (sum 540), and the
pair of vertical sides is parallel, so it is a Type 1 monohedral convex
pentagon in the Reinhardt classification -- the simplest convex pentagon that
tiles the plane.

Tiling: upright houses pack in rows sharing their vertical edges, leaving a
downward V between adjacent roofs; an inverted house fills each V (its two roof
edges match the two neighbouring upright roofs exactly). The inverted houses'
flat tops then carry the next row of upright houses, shifted by half a cell so
the tops land exactly on the next row's bottoms -- so the tiling is
edge-to-edge with only rational coordinates (every shared edge matches
bit-exactly; no T-junctions, no irrational tolerance needed).

That half-cell-per-row shift is a skew, but two rows shift by a full cell width
(2 * 25 = 50), so the tiling is periodic on a plain *rectangular* lattice with
a four-tile primitive unit: two upright + two inverted houses, the second row
pre-shifted by 25 in its coordinates. The square side is 50, the roof apex
rises 25 above the square top; the cell is 50 wide and 125 + 125 = 250 tall.

Run with:

    py -m tools tilings sketch tools/sketch_examples/house_pentagonal.py
"""

from typing import Any

GEOMETRY = "house-pentagonal"
LABEL = "House Pentagonal"
BASE_EDGE = 50.0
CELL_WIDTH = 50.0
CELL_HEIGHT = 250.0
ROW_OFFSET_X = 0.0


def _tile(
    slot: str, verts: list[tuple[float, float]], *, repeat_x_extra: int = 0
) -> dict[str, Any]:
    face: dict[str, Any] = {
        "slot": slot,
        "kind": "house-pentagon",
        "prefix": "h",
        "vertices": verts,
    }
    if repeat_x_extra:
        face["repeat_x_extra"] = repeat_x_extra
    return face


FACES = [
    # Row 0 (shift 0): upright house + the inverted house filling its right V.
    _tile(
        "up0",
        [(0.0, 0.0), (50.0, 0.0), (50.0, 50.0), (25.0, 75.0), (0.0, 50.0)],
    ),
    _tile(
        "down0",
        [(50.0, 50.0), (75.0, 75.0), (75.0, 125.0), (25.0, 125.0), (25.0, 75.0)],
        repeat_x_extra=1,
    ),
    # Row 1 (shift +25): same pair translated by (25, 125).
    _tile(
        "up1",
        [(25.0, 125.0), (75.0, 125.0), (75.0, 175.0), (50.0, 200.0), (25.0, 175.0)],
        repeat_x_extra=1,
    ),
    _tile(
        "down1",
        [(25.0, 175.0), (50.0, 200.0), (50.0, 250.0), (0.0, 250.0), (0.0, 200.0)],
    ),
]
