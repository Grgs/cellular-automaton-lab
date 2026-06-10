"""Exact-arithmetic generator for the Bielefeld pinwheel-2-1 substitution.

Uses the shared ``ExactSimilaritySubstitution`` scaffold from
``aperiodic_exact_similarity.py``. The substitution mixes one small child
(scale 1/sqrt(17)) at the right-angle corner with four large children
(scale 2/sqrt(17)) filling the rest of each 1:4:sqrt(17) parent. The
two prototile sizes are emitted as distinct cell kinds so renderer,
palette, and CA rules can target them separately.

Structurally distinct from the Conway-Radin pinwheel implemented in
``aperiodic_pinwheel.py`` (1:2:sqrt(5) prototile, single kind, 5
equal-size children at scale 1/sqrt(5)).

Source: https://tilings.math.uni-bielefeld.de/substitution/pinwheel-2-1/
"""

from __future__ import annotations

import math
from fractions import Fraction

from backend.simulation.aperiodic_exact_similarity import (
    ExactPoint,
    ExactSimilaritySubstitution,
    ExactTriangle,
)
from backend.simulation.aperiodic_family_manifest import (
    PINWHEEL_2_1_LARGE_KIND,
    PINWHEEL_2_1_SMALL_KIND,
    PINWHEEL_2_1_TILE_FAMILY,
)
from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    ExactPatchRecord,
)

# Tokens re-exported for callers that already imported them from this module.
TILE_FAMILY = PINWHEEL_2_1_TILE_FAMILY
KIND_SMALL = PINWHEEL_2_1_SMALL_KIND
KIND_LARGE = PINWHEEL_2_1_LARGE_KIND


_ZERO = Fraction(0, 1)
_ONE = Fraction(1, 1)
_TWO = Fraction(2, 1)
_FOUR = Fraction(4, 1)


# Canonical (small-angle, right-angle, large-angle) vertex ordering for the
# 1:4:sqrt(17) prototile. The long leg runs from vertex[0] to vertex[1]
# (length 4), the short leg from vertex[1] to vertex[2] (length 1). The
# shared ``ExactSimilaritySubstitution.map_local`` derives the long-leg
# divisor from ``base_triangle[1][0] - base_triangle[0][0]``.
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

# Paired-rectangle seed: the lower-right and upper-left halves of a 4x1
# rectangle, both in canonical (small, right, large) order. See
# ``aperiodic_pinwheel.py`` for the matching convention.
_ROOT_TRIANGLES: tuple[ExactTriangle, ...] = (
    _BASE_TRIANGLE,
    (
        (_FOUR, _ONE),
        (_ZERO, _ONE),
        (_ZERO, _ZERO),
    ),
)

REFERENCE_ROOT_SEED_POLICY = "paired-right-triangle-rectangle"
INFLATION_FACTOR = math.sqrt(17) / 2
USES_EXACT_REFERENCE_PATH = True


_SUBSTITUTION = ExactSimilaritySubstitution(
    base_triangle=_BASE_TRIANGLE,
    children=_ALL_CHILDREN,
    roots=_ROOT_TRIANGLES,
    id_prefix="pinwheel-2-1",
    tile_family=TILE_FAMILY,
    root_kind=KIND_LARGE,
    inflation_factor=INFLATION_FACTOR,
)


def _subdivide(parent: ExactTriangle) -> tuple[tuple[str, ExactTriangle], ...]:
    """Per-parent subdivision (re-exported for legacy test imports)."""
    return _SUBSTITUTION.subdivide(parent)


def collect_pinwheel_2_1_exact_records(patch_depth: int) -> tuple[ExactPatchRecord, ...]:
    return _SUBSTITUTION.collect_exact_records(patch_depth)


def build_pinwheel_2_1_patch(patch_depth: int) -> AperiodicPatch:
    """Build an AperiodicPatch for the pinwheel-2-1 substitution.

    Uses ``segment_overlap`` neighbor mode (configured on the shared
    ``_SUBSTITUTION``) because, like the Conway-Radin pinwheel, the
    subdivision is not edge-to-edge.
    """
    return _SUBSTITUTION.build_patch(patch_depth)
