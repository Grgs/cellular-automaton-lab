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


_HALF_SQRT3 = math.sqrt(3) / 2


def _hex_point(x: float, y: float) -> Vec:
    return Vec(x + (0.5 * y), _HALF_SQRT3 * y)

_HAT_OUTLINE = (
    _hex_point(0, 0),
    _hex_point(-1, -1),
    _hex_point(0, -2),
    _hex_point(2, -2),
    _hex_point(2, -1),
    _hex_point(4, -2),
    _hex_point(5, -1),
    _hex_point(4, 0),
    _hex_point(3, 0),
    _hex_point(2, 2),
    _hex_point(0, 3),
    _hex_point(0, 2),
    _hex_point(-1, 2),
)

_HAT_ATTACHMENTS: tuple[Affine, ...] = (
    (0.0, 0.5773502691896257, -1.0, -0.5773502691896257, 0.0, -1.7320508075688772),
    (0.5, 0.8660254037844386, 3.0, -0.8660254037844386, 0.5, -1.7320508075688772),
)


def _orientation_token(transform: Affine) -> str:
    angle = math.degrees(math.atan2(transform[3], transform[0]))
    return str(int(round(angle)) % 360)


def _chirality_token(transform: Affine) -> str:
    determinant = (transform[0] * transform[4]) - (transform[1] * transform[3])
    return "left" if determinant >= 0 else "right"


def _hat_record(transform: Affine) -> PatchRecord:
    vertices = tuple(affine_apply(transform, vertex) for vertex in _HAT_OUTLINE)
    return {
        "id": id_from_transform("hat", transform),
        "kind": "hat",
        "center": rounded_point(polygon_centroid(vertices)),
        "vertices": tuple(rounded_point(vertex) for vertex in vertices),
        "tile_family": "hat",
        "orientation_token": _orientation_token(transform),
        "chirality_token": _chirality_token(transform),
    }


_HAT_SEQUENCE = (0, 0, 1)


def build_hat_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    records: list[PatchRecord] = []
    current_transform: Affine = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    records.append(_hat_record(current_transform))
    for index in range(resolved_depth):
        current_transform = affine_multiply(
            current_transform,
            _HAT_ATTACHMENTS[_HAT_SEQUENCE[index % len(_HAT_SEQUENCE)]],
        )
        records.append(_hat_record(current_transform))
    return patch_from_records(resolved_depth, records)
