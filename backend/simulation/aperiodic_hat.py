from __future__ import annotations

import math
from collections import deque

from backend.simulation.aperiodic_support import (
    Affine,
    AperiodicPatch,
    PatchRecord,
    Vec,
    affine_apply,
    affine_inverse,
    affine_multiply,
    patch_from_records,
    polygon_centroid,
    rotation,
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
_HAT_MOVES: tuple[Affine, ...] = (
    _HAT_ATTACHMENTS[0],
    _HAT_ATTACHMENTS[1],
    affine_inverse(_HAT_ATTACHMENTS[0]),
    affine_inverse(_HAT_ATTACHMENTS[1]),
    affine_multiply(rotation(math.pi / 3), _HAT_ATTACHMENTS[0]),
    affine_multiply(rotation(-math.pi / 3), _HAT_ATTACHMENTS[1]),
)
_IDENTITY: Affine = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0)


def _orientation_token(transform: Affine) -> str:
    angle = math.degrees(math.atan2(transform[3], transform[0]))
    return str(int(round(angle)) % 360)


def _chirality_token(transform: Affine) -> str:
    determinant = (transform[0] * transform[4]) - (transform[1] * transform[3])
    return "left" if determinant >= 0 else "right"


def _hat_record(cell_id: str, transform: Affine) -> PatchRecord:
    vertices = tuple(affine_apply(transform, vertex) for vertex in _HAT_OUTLINE)
    return {
        "id": cell_id,
        "kind": "hat",
        "center": rounded_point(polygon_centroid(vertices)),
        "vertices": tuple(rounded_point(vertex) for vertex in vertices),
        "tile_family": "hat",
        "orientation_token": _orientation_token(transform),
        "chirality_token": _chirality_token(transform),
    }


def _placement_key(transform: Affine) -> tuple[float, ...]:
    return tuple(round(value, 6) for value in transform)


def build_hat_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    frontier: deque[tuple[Affine, int]] = deque([(_IDENTITY, 0)])
    seen: dict[tuple[float, ...], Affine] = {_placement_key(_IDENTITY): _IDENTITY}

    while frontier:
        transform, depth = frontier.popleft()
        if depth >= resolved_depth:
            continue
        for move in _HAT_MOVES:
            child = affine_multiply(transform, move)
            key = _placement_key(child)
            if key in seen:
                continue
            seen[key] = child
            frontier.append((child, depth + 1))

    provisional_records = [
        _hat_record(f"hat:{index}", transform)
        for index, transform in enumerate(seen.values())
    ]
    patch = patch_from_records(resolved_depth, provisional_records)
    if not patch.cells:
        return patch

    neighbors_by_id = {cell.id: tuple(cell.neighbors) for cell in patch.cells}
    root_id = patch.cells[0].id
    connected: set[str] = {root_id}
    stack = [root_id]
    while stack:
        current = stack.pop()
        for neighbor in neighbors_by_id[current]:
            if neighbor in connected:
                continue
            connected.add(neighbor)
            stack.append(neighbor)

    records = [record for record in provisional_records if record["id"] in connected]
    return patch_from_records(resolved_depth, records)
