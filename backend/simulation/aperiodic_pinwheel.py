from __future__ import annotations

import math
from fractions import Fraction

from backend.simulation.aperiodic_family_manifest import (
    PINWHEEL_TILE_FAMILY,
    PINWHEEL_TRIANGLE_KIND,
)
from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    ExactPatchRecord,
    patch_from_exact_records,
)


ExactPoint = tuple[Fraction, Fraction]
ExactTriangle = tuple[ExactPoint, ExactPoint, ExactPoint]

_ZERO = Fraction(0, 1)
_ONE = Fraction(1, 1)
_TWO = Fraction(2, 1)
_THREE = Fraction(3, 1)
_FOUR = Fraction(4, 1)
_FIVE = Fraction(5, 1)

_BASE_TRIANGLE: ExactTriangle = (
    (_ZERO, _ZERO),
    (_TWO, _ZERO),
    (_TWO, _ONE),
)
_PINWHEEL_CHILDREN: tuple[ExactTriangle, ...] = (
    ((_ZERO, _ZERO), (Fraction(4, 5), Fraction(2, 5)), (_ONE, _ZERO)),
    ((Fraction(4, 5), Fraction(2, 5)), (_ONE, _ZERO), (Fraction(8, 5), Fraction(4, 5))),
    ((_ONE, _ZERO), (Fraction(8, 5), Fraction(4, 5)), (Fraction(9, 5), Fraction(2, 5))),
    ((_ONE, _ZERO), (Fraction(9, 5), Fraction(2, 5)), (_TWO, _ZERO)),
    ((Fraction(8, 5), Fraction(4, 5)), (_TWO, _ZERO), (_TWO, _ONE)),
)
_ROOT_TRIANGLES: tuple[ExactTriangle, ...] = (
    _BASE_TRIANGLE,
    (
        (_ZERO, _ZERO),
        (_ZERO, _ONE),
        (_TWO, _ONE),
    ),
)
REFERENCE_ROOT_SEED_POLICY = "paired-right-triangle-rectangle"
USES_EXACT_REFERENCE_PATH = True


def _orientation_token(vertices: ExactTriangle) -> str:
    edges: list[tuple[Fraction, ExactPoint, ExactPoint]] = []
    for index, start in enumerate(vertices):
        end = vertices[(index + 1) % len(vertices)]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        edges.append((dx * dx + dy * dy, start, end))
    _, start, end = max(edges, key=lambda item: item[0])
    angle = math.degrees(math.atan2(float(end[1] - start[1]), float(end[0] - start[0])))
    return str(int(round(angle)) % 360)


def _chirality_token(vertices: ExactTriangle) -> str:
    (ax, ay), (bx, by), (cx, cy) = vertices
    area_twice = ((bx - ax) * (cy - ay)) - ((cx - ax) * (by - ay))
    return "left" if area_twice >= 0 else "right"


def _map_local(parent: ExactTriangle, point: ExactPoint) -> ExactPoint:
    (ax, ay), (bx, by), (cx, cy) = parent
    x_value, y_value = point
    delta_x = bx - ax
    delta_y = by - ay
    return (
        ax + (delta_x * x_value / _TWO) + ((cx - bx) * y_value),
        ay + (delta_y * x_value / _TWO) + ((cy - by) * y_value),
    )


def _subdivide(parent: ExactTriangle) -> tuple[ExactTriangle, ...]:
    return tuple(
        (
            _map_local(parent, child[0]),
            _map_local(parent, child[1]),
            _map_local(parent, child[2]),
        )
        for child in _PINWHEEL_CHILDREN
    )


def _pinwheel_record(path: str, vertices: ExactTriangle) -> ExactPatchRecord:
    return {
        "id": f"pinwheel:{path}",
        "kind": PINWHEEL_TRIANGLE_KIND,
        "vertices": vertices,
        "tile_family": PINWHEEL_TILE_FAMILY,
        "orientation_token": _orientation_token(vertices),
        "chirality_token": _chirality_token(vertices),
    }


def _collect_records(
    vertices: ExactTriangle,
    remaining_depth: int,
    path: str,
    records: list[ExactPatchRecord],
) -> None:
    if remaining_depth <= 0:
        records.append(_pinwheel_record(path, vertices))
        return
    for index, child in enumerate(_subdivide(vertices)):
        _collect_records(child, remaining_depth - 1, f"{path}.{index}", records)


def collect_pinwheel_exact_records(patch_depth: int) -> tuple[ExactPatchRecord, ...]:
    resolved_depth = max(0, int(patch_depth))
    records: list[ExactPatchRecord] = []
    for index, root in enumerate(_ROOT_TRIANGLES):
        _collect_records(root, resolved_depth, f"root{index}", records)
    return tuple(records)


def build_pinwheel_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    inflation_scale = math.sqrt(5) ** resolved_depth
    # The published pinwheel subdivision introduces T-junctions, so adjacency must
    # be derived from exact segment overlap rather than identical whole edges.
    patch = patch_from_exact_records(
        resolved_depth,
        list(collect_pinwheel_exact_records(resolved_depth)),
        float_scale=inflation_scale,
        vertex_precision=None,
        neighbor_mode="segment_overlap",
    )
    return AperiodicPatch(
        patch_depth=patch.patch_depth,
        width=max(3, patch.width),
        height=max(3, patch.height),
        cells=patch.cells,
    )
