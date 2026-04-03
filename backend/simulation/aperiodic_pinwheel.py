from __future__ import annotations

import math

from backend.simulation.aperiodic_support import (
    Affine,
    AperiodicPatch,
    PatchRecord,
    Vec,
    affine_apply,
    affine_multiply,
    id_from_transform,
    patch_from_records,
    polygon_centroid,
    rounded_point,
)


_BASE_TRIANGLE = (
    Vec(0.0, 0.0),
    Vec(2.0, 0.0),
    Vec(2.0, 1.0),
)


def _reflection_across_edge(left: Vec, right: Vec) -> Affine:
    dx = right.x - left.x
    dy = right.y - left.y
    length_squared = (dx * dx) + (dy * dy)
    a = ((dx * dx) - (dy * dy)) / length_squared
    b = (2.0 * dx * dy) / length_squared
    d = b
    e = ((dy * dy) - (dx * dx)) / length_squared
    c = left.x - (a * left.x) - (b * left.y)
    f = left.y - (d * left.x) - (e * left.y)
    return (a, b, c, d, e, f)


_EDGE_REFLECTIONS = (
    _reflection_across_edge(_BASE_TRIANGLE[0], _BASE_TRIANGLE[1]),
    _reflection_across_edge(_BASE_TRIANGLE[1], _BASE_TRIANGLE[2]),
    _reflection_across_edge(_BASE_TRIANGLE[2], _BASE_TRIANGLE[0]),
)

_PINWHEEL_SEQUENCE = (0, 1, 2)


def _orientation_token(transform: Affine) -> str:
    angle = math.degrees(math.atan2(transform[3], transform[0]))
    return str(int(round(angle)) % 360)


def _chirality_token(transform: Affine) -> str:
    determinant = (transform[0] * transform[4]) - (transform[1] * transform[3])
    return "left" if determinant >= 0 else "right"


def _triangle_record(index: int, transform: Affine) -> PatchRecord:
    vertices = tuple(affine_apply(transform, vertex) for vertex in _BASE_TRIANGLE)
    return {
        "id": f"{index}:{id_from_transform('pinwheel', transform)}",
        "kind": "pinwheel-triangle",
        "center": rounded_point(polygon_centroid(vertices)),
        "vertices": tuple(rounded_point(vertex) for vertex in vertices),
        "tile_family": "pinwheel",
        "orientation_token": _orientation_token(transform),
        "chirality_token": _chirality_token(transform),
    }


def build_pinwheel_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    triangle_count = max(1, 2 ** resolved_depth)
    records: list[PatchRecord] = []
    current_transform: Affine = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    for index in range(triangle_count):
        records.append(_triangle_record(index, current_transform))
        current_transform = affine_multiply(
            current_transform,
            _EDGE_REFLECTIONS[_PINWHEEL_SEQUENCE[index % len(_PINWHEEL_SEQUENCE)]],
        )
    return patch_from_records(resolved_depth, records)
