"""Geometric polygon constructors for tiling sketches.

These helpers exist so a sketch file (the input to
``tools/sketch_tiling.py``) never has to spell out ``sqrt(3) / 2`` or
hand-derive the third vertex of an equilateral triangle from its base.
Every helper returns a tuple of ``(x, y)`` vertex tuples in counter-
clockwise order with coordinates already rounded to six decimal places
(the same precision the backend's edge-matcher uses), so values derived
two different ways agree to the last digit and the polygon-overlap
validator never fires on float noise.

Typical usage in a sketch file::

    from tools.sketch_helpers import equilateral_triangle, square, hexagon

    EDGE = 52.0
    FACES = [
        {
            "slot": "ua",
            "kind": "triangle",
            "vertices": equilateral_triangle((0, 0), (EDGE, 0), side="above"),
        },
        {
            "slot": "sa",
            "kind": "square",
            "vertices": square((0, 90.066642), EDGE),
        },
        ...
    ]

The companion to this module is ``tools/sketch_tiling.py`` (the validator
that consumes sketches). See ``tools/sketch_examples/`` for full sketches
demonstrating common construction patterns.
"""

from __future__ import annotations

import math
from collections.abc import Iterable

_PRECISION = 6  # decimals; matches the backend's _edge_key rounding


Vertex = tuple[float, float]


def _round(point: tuple[float, float]) -> Vertex:
    return (round(point[0], _PRECISION), round(point[1], _PRECISION))


def _round_all(points: Iterable[tuple[float, float]]) -> tuple[Vertex, ...]:
    return tuple(_round(p) for p in points)


# --- Triangles --------------------------------------------------------------


def equilateral_triangle(
    p1: tuple[float, float],
    p2: tuple[float, float],
    *,
    side: str = "above",
) -> tuple[Vertex, Vertex, Vertex]:
    """Equilateral triangle with one edge from p1 to p2.

    ``side="above"`` (default) puts the third vertex on the left of the
    directed line p1 -> p2 (so for a horizontal base p1=(0,0), p2=(1,0)
    the apex is at (0.5, sqrt(3)/2) - above in screen-y-up coordinates,
    below in screen-y-down coordinates).

    ``side="below"`` puts the third vertex on the right of the directed
    line.

    Returns vertices in CCW order: (p1, p2, apex) for ``side="above"``,
    (p1, apex, p2) for ``side="below"``.
    """
    if side not in ("above", "below"):
        raise ValueError(f"side must be 'above' or 'below', got {side!r}")
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    length = math.hypot(dx, dy)
    if length < 1e-9:
        raise ValueError("p1 and p2 must be distinct")
    midpoint = ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)
    height = length * math.sqrt(3) / 2.0
    # Perpendicular unit vector to the left of p1 -> p2:
    perp = (-dy / length, dx / length)
    sign = 1.0 if side == "above" else -1.0
    apex = (midpoint[0] + sign * perp[0] * height, midpoint[1] + sign * perp[1] * height)
    if side == "above":
        return (_round(p1), _round(p2), _round(apex))
    return (_round(p1), _round(apex), _round(p2))


def isoceles_right_triangle(
    leg_p1: tuple[float, float],
    leg_p2: tuple[float, float],
    *,
    side: str = "above",
) -> tuple[Vertex, Vertex, Vertex]:
    """Isoceles right triangle with legs from a shared right-angle vertex.

    leg_p1 and leg_p2 are the two non-right-angle vertices; the right
    angle is placed perpendicular-out from the midpoint of leg_p1->leg_p2
    on the chosen side. Useful for tetrakis-square-like patterns.
    """
    if side not in ("above", "below"):
        raise ValueError(f"side must be 'above' or 'below', got {side!r}")
    dx = leg_p2[0] - leg_p1[0]
    dy = leg_p2[1] - leg_p1[1]
    length = math.hypot(dx, dy)
    if length < 1e-9:
        raise ValueError("leg_p1 and leg_p2 must be distinct")
    midpoint = ((leg_p1[0] + leg_p2[0]) / 2.0, (leg_p1[1] + leg_p2[1]) / 2.0)
    perp = (-dy / length, dx / length)
    sign = 1.0 if side == "above" else -1.0
    height = length / 2.0
    apex = (midpoint[0] + sign * perp[0] * height, midpoint[1] + sign * perp[1] * height)
    if side == "above":
        return (_round(leg_p1), _round(leg_p2), _round(apex))
    return (_round(leg_p1), _round(apex), _round(leg_p2))


# --- Squares ----------------------------------------------------------------


def square(
    bottom_left: tuple[float, float],
    side: float,
) -> tuple[Vertex, Vertex, Vertex, Vertex]:
    """Axis-aligned square with the given bottom-left corner and side length.

    Vertices in CCW order (screen-y-down convention): bottom-left,
    bottom-right, top-right, top-left.
    """
    if side <= 0:
        raise ValueError("side must be positive")
    x, y = bottom_left
    return (
        _round((x, y)),
        _round((x + side, y)),
        _round((x + side, y + side)),
        _round((x, y + side)),
    )


def square_with_mid_edge_vertices(
    bottom_left: tuple[float, float],
    side: float,
    *,
    bottom: bool = True,
    right: bool = True,
    top: bool = True,
    left: bool = True,
) -> tuple[Vertex, ...]:
    """Square with optional collinear vertices at edge midpoints.

    Used for T-junction handling (see the Pythagorean and Herringbone
    tilings). The geometry is still a square; the extra vertices are
    collinear with the square's corners so polygon edges split at points
    where a neighbouring polygon's vertex lands mid-edge.

    Returns vertices CCW starting from the bottom-left corner.
    """
    if side <= 0:
        raise ValueError("side must be positive")
    x, y = bottom_left
    pts: list[tuple[float, float]] = [(x, y)]
    if bottom:
        pts.append((x + side / 2.0, y))
    pts.append((x + side, y))
    if right:
        pts.append((x + side, y + side / 2.0))
    pts.append((x + side, y + side))
    if top:
        pts.append((x + side / 2.0, y + side))
    pts.append((x, y + side))
    if left:
        pts.append((x, y + side / 2.0))
    return _round_all(pts)


# --- Hexagons ---------------------------------------------------------------


def regular_hexagon(
    center: tuple[float, float],
    edge: float,
    *,
    orientation: str = "flat-top",
) -> tuple[Vertex, ...]:
    """Regular hexagon centred on ``center`` with given edge length.

    ``orientation="flat-top"`` (default) puts a flat edge at the top and
    bottom; vertices are at angles 0, 60, 120, 180, 240, 300 deg from the
    center (so leftmost/rightmost points are vertices).

    ``orientation="pointy-top"`` puts a vertex at the top and bottom;
    vertices at angles 30, 90, 150, 210, 270, 330 deg.

    Returns 6 vertices in CCW order starting from the rightmost vertex
    (flat-top) or upper-right vertex (pointy-top).
    """
    if edge <= 0:
        raise ValueError("edge must be positive")
    if orientation not in ("flat-top", "pointy-top"):
        raise ValueError(f"orientation must be 'flat-top' or 'pointy-top', got {orientation!r}")
    cx, cy = center
    if orientation == "flat-top":
        offsets = (0, 60, 120, 180, 240, 300)
    else:
        offsets = (30, 90, 150, 210, 270, 330)
    points = [
        (cx + edge * math.cos(math.radians(a)), cy + edge * math.sin(math.radians(a)))
        for a in offsets
    ]
    return _round_all(points)


__all__ = [
    "Vertex",
    "equilateral_triangle",
    "isoceles_right_triangle",
    "regular_hexagon",
    "square",
    "square_with_mid_edge_vertices",
]
