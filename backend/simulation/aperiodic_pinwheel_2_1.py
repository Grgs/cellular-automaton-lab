"""Exact-arithmetic generator for the Pinwheel 2-1 substitution.

This is the two-prototile pinwheel variant from the Bielefeld Tilings
Encyclopedia (``pinwheel-2-1``): a 1:4:sqrt(17) right triangle that
subdivides into five similar children of two different sizes -- one
small child at the right-angle corner (scale 1/sqrt(17)) plus four
large children (scale 2/sqrt(17)) filling the remaining area.

This is structurally distinct from the Conway-Radin pinwheel implemented
in ``aperiodic_pinwheel.py``, which uses 1:2:sqrt(5) prototiles and a
five-equal-children subdivision at scale 1/sqrt(5).
"""

from __future__ import annotations

import math
from fractions import Fraction

from backend.simulation.aperiodic_family_manifest import (
    PINWHEEL_2_1_LARGE_KIND,
    PINWHEEL_2_1_SMALL_KIND,
    PINWHEEL_2_1_TILE_FAMILY,
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
_FOUR = Fraction(4, 1)
_SEVENTEEN = Fraction(17, 1)

# Kind / tile-family tokens are sourced from the aperiodic family manifest
# so the registered topology, frontend palette, and reference specs all
# share the same canonical strings.
TILE_FAMILY = PINWHEEL_2_1_TILE_FAMILY
KIND_SMALL = PINWHEEL_2_1_SMALL_KIND
KIND_LARGE = PINWHEEL_2_1_LARGE_KIND

# Canonical (small-angle, right-angle, large-angle) vertex ordering for the
# 1:4:sqrt(17) prototile. The long leg runs from vertex[0] to vertex[1]
# (length 4), the short leg from vertex[1] to vertex[2] (length 1). With
# this ordering, ``_map_local`` is a similarity transform whenever the
# parent triangle is itself a 1:4:sqrt(17) right triangle in canonical
# orientation, which is what the substitution rule preserves for all five
# children. See the matching note in ``aperiodic_pinwheel.py`` for the
# analogous Conway-Radin convention.
_BASE_TRIANGLE: ExactTriangle = (
    (_ZERO, _ZERO),
    (_FOUR, _ZERO),
    (_FOUR, _ONE),
)

# Children expressed in local coordinates of the base triangle above.
# Construction (translating the GLSL shader at
# https://tilings.math.uni-bielefeld.de/substitution/pinwheel-2-1/ into
# local coords with c=(4,0), a=(0,0), b=(4,1)):
#
#   e = midpoint of c-a                  = (2, 0)
#   d = foot of altitude from c to ab    = (64/17, 16/17)
#   f = midpoint of d-a                  = (32/17, 8/17)
#   g = midpoint of d-c                  = (66/17, 8/17)
#
# Then the five children, each reordered into canonical (small-angle,
# right-angle, large-angle) vertex order so the recursion stays a
# similarity:
#
#   1. (c, d, b)  -- small child at parent's right-angle corner, scale 1/sqrt(17)
#   2. (a, f, e)  -- large child at parent's small-angle corner,  scale 2/sqrt(17)
#   3. (e, g, c)  -- large child along the long leg,              scale 2/sqrt(17)
#   4. (e, g, d)  -- large child interior,                        scale 2/sqrt(17)
#   5. (d, f, e)  -- large child along the hypotenuse,            scale 2/sqrt(17)
_E: ExactPoint = (_TWO, _ZERO)
_D: ExactPoint = (Fraction(64, 17), Fraction(16, 17))
_F: ExactPoint = (Fraction(32, 17), Fraction(8, 17))
_G: ExactPoint = (Fraction(66, 17), Fraction(8, 17))
_C: ExactPoint = (_FOUR, _ZERO)
_A: ExactPoint = (_ZERO, _ZERO)
_B: ExactPoint = (_FOUR, _ONE)

_SMALL_CHILD: ExactTriangle = (_C, _D, _B)
_LARGE_CHILDREN: tuple[ExactTriangle, ...] = (
    (_A, _F, _E),
    (_E, _G, _C),
    (_E, _G, _D),
    (_D, _F, _E),
)
_ALL_CHILDREN: tuple[tuple[str, ExactTriangle], ...] = (
    (KIND_SMALL, _SMALL_CHILD),
    *((KIND_LARGE, child) for child in _LARGE_CHILDREN),
)

INFLATION_FACTOR = math.sqrt(17) / 2
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
    """Map a point in local (base-triangle) coordinates into parent space.

    With ``parent`` in canonical (small-angle, right-angle, large-angle)
    order, the linear part of this map is a rotation + uniform scale --
    i.e. a similarity -- which is what the pinwheel-2-1 subdivision rule
    requires for shape-preserving children.
    """
    (ax, ay), (bx, by), (cx, cy) = parent
    x_value, y_value = point
    delta_x = bx - ax
    delta_y = by - ay
    return (
        ax + (delta_x * x_value / _FOUR) + ((cx - bx) * y_value),
        ay + (delta_y * x_value / _FOUR) + ((cy - by) * y_value),
    )


def _subdivide(parent: ExactTriangle) -> tuple[tuple[str, ExactTriangle], ...]:
    return tuple(
        (
            kind,
            (
                _map_local(parent, child[0]),
                _map_local(parent, child[1]),
                _map_local(parent, child[2]),
            ),
        )
        for kind, child in _ALL_CHILDREN
    )


def _pinwheel_record(path: str, kind: str, vertices: ExactTriangle) -> ExactPatchRecord:
    return {
        "id": f"pinwheel-2-1:{path}",
        "kind": kind,
        "vertices": vertices,
        "tile_family": TILE_FAMILY,
        "orientation_token": _orientation_token(vertices),
        "chirality_token": _chirality_token(vertices),
    }


def _collect_records(
    kind: str,
    vertices: ExactTriangle,
    remaining_depth: int,
    path: str,
    records: list[ExactPatchRecord],
) -> None:
    if remaining_depth <= 0:
        records.append(_pinwheel_record(path, kind, vertices))
        return
    for index, (child_kind, child_vertices) in enumerate(_subdivide(vertices)):
        _collect_records(
            child_kind, child_vertices, remaining_depth - 1, f"{path}.{index}", records
        )


def collect_pinwheel_2_1_exact_records(patch_depth: int) -> tuple[ExactPatchRecord, ...]:
    resolved_depth = max(0, int(patch_depth))
    records: list[ExactPatchRecord] = []
    _collect_records(KIND_LARGE, _BASE_TRIANGLE, resolved_depth, "root", records)
    return tuple(records)


def build_pinwheel_2_1_patch(patch_depth: int) -> AperiodicPatch:
    """Build an AperiodicPatch for the pinwheel-2-1 substitution.

    Note: the resulting patch is not registered with the topology catalog
    or any family manifest. It uses ``segment_overlap`` neighbor mode
    because, like the Conway-Radin pinwheel, the subdivision is not
    edge-to-edge.
    """
    resolved_depth = max(0, int(patch_depth))
    inflation_scale = INFLATION_FACTOR**resolved_depth
    patch = patch_from_exact_records(
        resolved_depth,
        list(collect_pinwheel_2_1_exact_records(resolved_depth)),
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
