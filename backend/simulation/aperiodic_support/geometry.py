"""Geometry helpers: vertex rounding, canonical edges, polygon centroid, extents.

Stateless pure functions over the basic types from ``.types``.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Iterable

from .types import COORDINATE_PRECISION, Vec


def rounded_point(point: Vec | tuple[float, float]) -> tuple[float, float]:
    x_value, y_value = point if isinstance(point, tuple) else (point.x, point.y)
    return (
        round(float(x_value), COORDINATE_PRECISION),
        round(float(y_value), COORDINATE_PRECISION),
    )


def canonical_edge(
    point_a: tuple[float, float],
    point_b: tuple[float, float],
    *,
    precision: int = COORDINATE_PRECISION,
) -> tuple[tuple[float, float], tuple[float, float]]:
    left = (
        round(float(point_a[0]), precision),
        round(float(point_a[1]), precision),
    )
    right = (
        round(float(point_b[0]), precision),
        round(float(point_b[1]), precision),
    )
    return (left, right) if left <= right else (right, left)


def exact_canonical_edge(
    point_a: tuple[Fraction, Fraction],
    point_b: tuple[Fraction, Fraction],
) -> tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]]:
    return (point_a, point_b) if point_a <= point_b else (point_b, point_a)


def compatibility_extent(values: list[float]) -> int:
    if not values:
        return 1
    return max(1, int(math.ceil(max(values) - min(values))))


def polygon_centroid(vertices: Iterable[Vec]) -> Vec:
    points = list(vertices)
    if not points:
        return Vec(0.0, 0.0)
    area_twice = 0.0
    centroid_x = 0.0
    centroid_y = 0.0
    for index, point in enumerate(points):
        next_point = points[(index + 1) % len(points)]
        cross = (point.x * next_point.y) - (next_point.x * point.y)
        area_twice += cross
        centroid_x += (point.x + next_point.x) * cross
        centroid_y += (point.y + next_point.y) * cross
    if math.isclose(area_twice, 0.0):
        return Vec(
            sum(point.x for point in points) / len(points),
            sum(point.y for point in points) / len(points),
        )
    scale = 1 / (3 * area_twice)
    return Vec(centroid_x * scale, centroid_y * scale)


def encode_float(value: float) -> str:
    scaled = int(round(value * 1_000_000))
    if scaled < 0:
        return f"n{abs(scaled)}"
    if scaled > 0:
        return f"p{scaled}"
    return "0"
