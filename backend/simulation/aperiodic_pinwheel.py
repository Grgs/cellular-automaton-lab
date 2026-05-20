"""Exact-arithmetic generator for the Conway-Radin pinwheel substitution.

Uses the shared ``ExactSimilaritySubstitution`` scaffold from
``aperiodic_exact_similarity.py``; this module just declares the
substitution parameters (base triangle, children, roots, inflation
factor) and wires the legacy public function names through to the
helper for backwards-compatible imports.
"""

from __future__ import annotations

import math
from fractions import Fraction

from backend.simulation.aperiodic_exact_similarity import (
    ExactSimilaritySubstitution,
    ExactTriangle,
)
from backend.simulation.aperiodic_family_manifest import (
    PINWHEEL_TILE_FAMILY,
    PINWHEEL_TRIANGLE_KIND,
)
from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    ExactPatchRecord,
)


_ZERO = Fraction(0, 1)
_ONE = Fraction(1, 1)
_TWO = Fraction(2, 1)

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
    # The second root is the upper-left half of the 2x1 seed rectangle. To
    # keep ``map_local`` a similarity transform (which is what the pinwheel
    # subdivision rule requires for shape-preserving children), the vertices
    # must follow the same (small-angle, right-angle, large-angle) ordering
    # as ``_BASE_TRIANGLE`` -- ``(2,1)`` is the small-angle (~26 deg) corner,
    # ``(0,1)`` is the right-angle corner, and ``(0,0)`` is the large-angle
    # (~63 deg) corner. The naive ordering ``((0,0), (0,1), (2,1))`` reversed
    # the small/large endpoints and produced non-similarity children that
    # were not Pinwheel triangles.
    (
        (_TWO, _ONE),
        (_ZERO, _ONE),
        (_ZERO, _ZERO),
    ),
)

REFERENCE_ROOT_SEED_POLICY = "paired-right-triangle-rectangle"
USES_EXACT_REFERENCE_PATH = True


_SUBSTITUTION = ExactSimilaritySubstitution(
    base_triangle=_BASE_TRIANGLE,
    # Pinwheel has one prototile kind; the helper expects ``(kind, vertices)``
    # tuples, so label every child uniformly.
    children=tuple((PINWHEEL_TRIANGLE_KIND, child) for child in _PINWHEEL_CHILDREN),
    roots=_ROOT_TRIANGLES,
    id_prefix="pinwheel",
    tile_family=PINWHEEL_TILE_FAMILY,
    root_kind=PINWHEEL_TRIANGLE_KIND,
    inflation_factor=math.sqrt(5),
)


def collect_pinwheel_exact_records(patch_depth: int) -> tuple[ExactPatchRecord, ...]:
    return _SUBSTITUTION.collect_exact_records(patch_depth)


def build_pinwheel_patch(patch_depth: int) -> AperiodicPatch:
    # The published pinwheel subdivision introduces T-junctions, so adjacency
    # is derived from exact segment overlap rather than identical whole edges
    # (configured via ``_SUBSTITUTION.neighbor_mode``).
    return _SUBSTITUTION.build_patch(patch_depth)
