"""Canonical Robinson half-tile substitution for Penrose tilings.

This module implements the Conway / de Bruijn / Robinson canonical substitution on
golden-ratio half-triangles:

    a = 1 / phi
    b = 1 / phi**2  (so a + b = 1 since phi**2 = phi + 1)

Acute (golden triangle, 36-72-72) with apex P0, base vertices P1 (left) and P2 (right):
    Q = a * P0 + b * P1   (point on edge P0->P1, distance b from P0)
    R = b * P0 + a * P2   (point on edge P0->P2, distance a from P0)
    children:
        acute(P1, P2, R)
        acute(P1, Q,  R)
        obtuse(Q, R,  P0)

Obtuse (golden gnomon, 108-36-36) with apex P0, base vertices P1 (left) and P2 (right):
    S = b * P1 + a * P2   (point on edge P1->P2, distance a from P1)
    children:
        acute(P1, S,  P0)
        obtuse(S, P0, P2)

Mirrored cases are produced by swapping the input triangle's left and right vertices
before applying the same formulas; the formulas themselves are not chirality-aware.

This is the SOURCE OF TRUTH for the Penrose families: emitting all halves yields
the canonical Robinson Triangles tiling, and pairing acute halves at long edges
into kites + obtuse halves at short edges into darts yields the canonical Penrose
P2 kite-dart tiling. Boundary halves that cannot pair across the patch perimeter
are emitted as half-tile cells.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

PHI = (1 + math.sqrt(5)) / 2
A = 1.0 / PHI
B = 1.0 / (PHI * PHI)

ACUTE_HALF = "acute"
OBTUSE_HALF = "obtuse"

# Coordinate rounding precision used for edge canonicalisation. Eight digits is
# tighter than ``aperiodic_support.COORDINATE_PRECISION`` (six) so the pairing
# step is robust against accumulated floating-point drift, while still leaving
# enough headroom to remain distinct after rounding back to six digits for
# storage.
_PAIRING_PRECISION = 8


Point = tuple[float, float]


@dataclass(frozen=True)
class HalfTile:
    """An oriented Robinson half-triangle.

    ``apex`` is the 36-degree vertex for acute halves and the 108-degree vertex
    for obtuse halves. ``left`` and ``right`` carry the chirality marker: a
    mirrored half is produced by swapping ``left`` and ``right`` in the input.
    """

    kind: str  # ACUTE_HALF or OBTUSE_HALF
    apex: Point
    left: Point
    right: Point


def _lc(s: float, p: Point, t: float, q: Point) -> Point:
    """Linear combination ``s * p + t * q``."""
    return (s * p[0] + t * q[0], s * p[1] + t * q[1])


def substitute_one(half: HalfTile) -> tuple[HalfTile, ...]:
    """Apply one Robinson canonical substitution step to a single half-tile."""
    p0, p1, p2 = half.apex, half.left, half.right
    if half.kind == ACUTE_HALF:
        q = _lc(A, p0, B, p1)
        r = _lc(B, p0, A, p2)
        return (
            HalfTile(ACUTE_HALF, p1, p2, r),
            HalfTile(ACUTE_HALF, p1, q, r),
            HalfTile(OBTUSE_HALF, q, r, p0),
        )
    if half.kind == OBTUSE_HALF:
        s = _lc(B, p1, A, p2)
        return (
            HalfTile(ACUTE_HALF, p1, s, p0),
            HalfTile(OBTUSE_HALF, s, p0, p2),
        )
    raise ValueError(f"Unknown half-tile kind {half.kind!r}.")


def substitute_all(halves: list[HalfTile], depth: int) -> list[HalfTile]:
    """Apply ``depth`` rounds of substitution to a list of half-tiles."""
    if depth < 0:
        raise ValueError("Substitution depth must be non-negative.")
    current: list[HalfTile] = list(halves)
    for _ in range(depth):
        nxt: list[HalfTile] = []
        for half in current:
            nxt.extend(substitute_one(half))
        current = nxt
    return current


def build_p2_sun_seed(scale_factor: float) -> list[HalfTile]:
    """Build the canonical 5-kite sun seed at the requested scale.

    Each kite has its 72-degree apex at the origin. The two acute halves of a
    given kite share the kite's spine endpoint (the 144-degree tip). Both halves
    therefore have ``left = tip`` so that the spine cuts produced by the
    substitution coincide between the two halves at the same point on the spine.
    """
    seed: list[HalfTile] = []
    for kite_index in range(5):
        spine_radians = math.radians(72 * kite_index)
        tip = (
            scale_factor * math.cos(spine_radians),
            scale_factor * math.sin(spine_radians),
        )
        right_outer = (
            scale_factor * math.cos(spine_radians - math.radians(36)),
            scale_factor * math.sin(spine_radians - math.radians(36)),
        )
        left_outer = (
            scale_factor * math.cos(spine_radians + math.radians(36)),
            scale_factor * math.sin(spine_radians + math.radians(36)),
        )
        # Right (clockwise) half: outer corner is on the CW side of the spine.
        # Left  (counter-clockwise) half: outer corner is on the CCW side.
        # Both use ``left = tip`` so spine cuts (R for right half, R for left
        # half) coincide on the shared spine vertex.
        seed.append(HalfTile(ACUTE_HALF, (0.0, 0.0), tip, right_outer))
        seed.append(HalfTile(ACUTE_HALF, (0.0, 0.0), tip, left_outer))
    return seed


def long_edges(half: HalfTile) -> tuple[tuple[Point, Point], ...]:
    """Return the long edges of a half-tile as ordered point pairs.

    Acute long edges are apex->left and apex->right (both unit-scale length 1).
    Obtuse long edges are left->right (the long base, length 1).
    """
    if half.kind == ACUTE_HALF:
        return ((half.apex, half.left), (half.apex, half.right))
    return ((half.left, half.right),)


def short_edges(half: HalfTile) -> tuple[tuple[Point, Point], ...]:
    """Return the short edges of a half-tile.

    Acute short edges are left->right (the short base, length 1/phi).
    Obtuse short edges are apex->left and apex->right (the legs, length 1/phi).
    """
    if half.kind == ACUTE_HALF:
        return ((half.left, half.right),)
    return ((half.apex, half.left), (half.apex, half.right))


def _round_point(point: Point) -> Point:
    return (round(point[0], _PAIRING_PRECISION), round(point[1], _PAIRING_PRECISION))


def _canonical_edge(p: Point, q: Point) -> tuple[Point, Point]:
    rounded_p = _round_point(p)
    rounded_q = _round_point(q)
    return (rounded_p, rounded_q) if rounded_p <= rounded_q else (rounded_q, rounded_p)


@dataclass(frozen=True)
class PairingResult:
    """The pairing of half-tiles into full Penrose tiles."""

    # Each pair is an ordered (lower_index, higher_index) tuple into the original
    # halves list.
    kite_pairs: tuple[tuple[int, int], ...]
    dart_pairs: tuple[tuple[int, int], ...]
    unpaired_acute: tuple[int, ...]
    unpaired_obtuse: tuple[int, ...]


def _maximum_matching(neighbours: dict[int, list[int]]) -> dict[int, int]:
    """Compute a maximum matching for a graph whose nodes have at most degree 2.

    Such graphs are disjoint unions of paths and cycles, so a single greedy pass
    that starts from path endpoints (degree-1 nodes) gives a maximum matching;
    cycles are handled by an arbitrary endpoint after no degree-1 nodes remain.
    """
    matched: dict[int, int] = {}
    visited: set[int] = set()
    # Start with degree-1 nodes (path endpoints).
    starts = [node for node, nbrs in neighbours.items() if len(nbrs) == 1]
    starts.extend(node for node, nbrs in neighbours.items() if len(nbrs) != 1)
    for start in starts:
        if start in visited:
            continue
        component: list[int] = []
        stack = [start]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            component.append(node)
            for nbr in neighbours.get(node, ()):
                if nbr not in visited:
                    stack.append(nbr)
        # Greedily match within the component.
        for node in component:
            if node in matched:
                continue
            for nbr in neighbours.get(node, ()):
                if nbr not in matched:
                    matched[node] = nbr
                    matched[nbr] = node
                    break
    return matched


def pair_halves_into_kites_and_darts(halves: list[HalfTile]) -> PairingResult:
    """Pair half-tiles into kites and darts using the Penrose convention.

    A kite is two acute halves glued along a long edge.
    A dart is two obtuse halves glued along a short edge.
    Half-tiles whose pairing partner lies outside the patch (because the
    matching long/short edge lies on the patch boundary) are returned as
    unpaired half-tiles.
    """
    acute_neighbours: dict[int, list[int]] = defaultdict(list)
    obtuse_neighbours: dict[int, list[int]] = defaultdict(list)

    acute_long_owners: dict[tuple[Point, Point], list[int]] = defaultdict(list)
    obtuse_short_owners: dict[tuple[Point, Point], list[int]] = defaultdict(list)
    for index, half in enumerate(halves):
        if half.kind == ACUTE_HALF:
            for edge in long_edges(half):
                acute_long_owners[_canonical_edge(*edge)].append(index)
        else:
            for edge in short_edges(half):
                obtuse_short_owners[_canonical_edge(*edge)].append(index)
    for owners in acute_long_owners.values():
        if len(owners) == 2:
            a, b = owners
            acute_neighbours[a].append(b)
            acute_neighbours[b].append(a)
    for owners in obtuse_short_owners.values():
        if len(owners) == 2:
            a, b = owners
            obtuse_neighbours[a].append(b)
            obtuse_neighbours[b].append(a)

    acute_indices = [i for i, h in enumerate(halves) if h.kind == ACUTE_HALF]
    obtuse_indices = [i for i, h in enumerate(halves) if h.kind == OBTUSE_HALF]

    # Ensure every node appears in the neighbour map (degree-0 nodes need to
    # be visited so they show up as unpaired).
    for index in acute_indices:
        acute_neighbours.setdefault(index, [])
    for index in obtuse_indices:
        obtuse_neighbours.setdefault(index, [])

    acute_match = _maximum_matching(dict(acute_neighbours))
    obtuse_match = _maximum_matching(dict(obtuse_neighbours))

    seen_pairs: set[frozenset[int]] = set()
    kite_pairs: list[tuple[int, int]] = []
    for left, right in acute_match.items():
        key = frozenset((left, right))
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        a, b = sorted((left, right))
        kite_pairs.append((a, b))
    seen_pairs.clear()
    dart_pairs: list[tuple[int, int]] = []
    for left, right in obtuse_match.items():
        key = frozenset((left, right))
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        a, b = sorted((left, right))
        dart_pairs.append((a, b))

    unpaired_acute = tuple(i for i in acute_indices if i not in acute_match)
    unpaired_obtuse = tuple(i for i in obtuse_indices if i not in obtuse_match)

    return PairingResult(
        kite_pairs=tuple(sorted(kite_pairs)),
        dart_pairs=tuple(sorted(dart_pairs)),
        unpaired_acute=unpaired_acute,
        unpaired_obtuse=unpaired_obtuse,
    )


def kite_polygon(left: HalfTile, right: HalfTile) -> tuple[Point, Point, Point, Point]:
    """Construct the convex kite polygon from a pair of acute halves.

    The two halves share a long edge (kite spine). The kite's four outer
    vertices, in CCW order, are:

        kite-72-apex, outer-72, kite-144-tip, outer-72

    where the 72-degree apex and 144-degree tip lie on the spine, and the two
    outer 72-degree corners come from one half each.
    """
    left_long = {_round_point(left.apex), _round_point(left.left), _round_point(left.right)}
    right_long = {_round_point(right.apex), _round_point(right.left), _round_point(right.right)}
    shared_rounded = left_long & right_long
    if len(shared_rounded) != 2:
        raise ValueError("Kite halves must share exactly two vertices.")
    spine_endpoints = []
    for vertex in (left.apex, left.left, left.right):
        if _round_point(vertex) in shared_rounded:
            spine_endpoints.append(vertex)
    if len(spine_endpoints) != 2:
        raise ValueError("Could not recover spine endpoints for kite halves.")
    # The two halves' apexes are both on the spine: one is the kite's 72 apex,
    # the other is the spine endpoint of the OTHER half (the kite's 144 tip).
    # Identify the apex (72-degree) from the (apex, left) labelling: in
    # ``build_p2_sun_seed`` the apex coincides for the two halves of one kite,
    # while inside a substituted patch the spine apex is whichever common
    # spine endpoint coincides with both halves' ``apex`` field.
    rounded_left_apex = _round_point(left.apex)
    rounded_right_apex = _round_point(right.apex)
    if rounded_left_apex == rounded_right_apex:
        kite_apex = left.apex
        kite_tip = next(p for p in spine_endpoints if _round_point(p) != rounded_left_apex)
    elif rounded_left_apex in shared_rounded and rounded_right_apex in shared_rounded:
        # Each half's apex is a different spine endpoint. The kite's 72-apex is
        # the one whose interior angle at the spine sums to 72 (= the apex of
        # both half-tiles). Either common endpoint works; pick lexicographic.
        kite_apex = left.apex if rounded_left_apex < rounded_right_apex else right.apex
        kite_tip = next(p for p in spine_endpoints if _round_point(p) != _round_point(kite_apex))
    else:
        kite_apex = left.apex if rounded_left_apex in shared_rounded else right.apex
        kite_tip = next(p for p in spine_endpoints if _round_point(p) != _round_point(kite_apex))
    left_outer = next(
        p for p in (left.apex, left.left, left.right) if _round_point(p) not in shared_rounded
    )
    right_outer = next(
        p for p in (right.apex, right.left, right.right) if _round_point(p) not in shared_rounded
    )

    # Order the outer corners so the polygon is CCW: rotate so that the cross
    # product of (apex->outer_a) and (apex->tip) is positive on the first outer.
    def _cross(o: Point) -> float:
        ax = o[0] - kite_apex[0]
        ay = o[1] - kite_apex[1]
        tx = kite_tip[0] - kite_apex[0]
        ty = kite_tip[1] - kite_apex[1]
        return ax * ty - ay * tx

    if _cross(left_outer) >= 0:
        first_outer, second_outer = left_outer, right_outer
    else:
        first_outer, second_outer = right_outer, left_outer
    return (kite_apex, first_outer, kite_tip, second_outer)


def dart_polygon(left: HalfTile, right: HalfTile) -> tuple[Point, Point, Point, Point]:
    """Construct the (concave) dart polygon from a pair of obtuse halves.

    The two halves share a short edge (dart spine). The dart's four outer
    vertices in CCW order are:

        dart-72-tip, wing-36, dart-216-concave, wing-36

    where the 72-tip and 216-concave vertex are the spine endpoints, and the
    two 36-degree wings come from one half each (the obtuse halves' bases).
    """
    left_pts = {_round_point(left.apex), _round_point(left.left), _round_point(left.right)}
    right_pts = {_round_point(right.apex), _round_point(right.left), _round_point(right.right)}
    shared_rounded = left_pts & right_pts
    if len(shared_rounded) != 2:
        raise ValueError("Dart halves must share exactly two vertices.")
    spine_endpoints: list[Point] = []
    for vertex in (left.apex, left.left, left.right):
        if _round_point(vertex) in shared_rounded:
            spine_endpoints.append(vertex)
    if len(spine_endpoints) != 2:
        raise ValueError("Could not recover dart spine endpoints.")
    # In a dart formed by two obtuses glued at a short edge, the spine endpoints
    # are: one is a 36 (base) vertex contributing to the dart's 72-tip
    # (36 + 36 = 72), and the other is the apex contributing to the 216 reflex
    # angle (108 + 108 = 216). The apex (108-degree) of each half is the one
    # common to ``apex`` of both halves OR the other common endpoint -- it is
    # exactly the half's ``apex``.
    rounded_left_apex = _round_point(left.apex)
    rounded_right_apex = _round_point(right.apex)
    if rounded_left_apex == rounded_right_apex:
        dart_concave = left.apex
        dart_tip = next(p for p in spine_endpoints if _round_point(p) != rounded_left_apex)
    elif rounded_left_apex in shared_rounded and rounded_right_apex in shared_rounded:
        # Apex of one half coincides with a non-apex base vertex of the other.
        # The 108-degree concave vertex of the dart is the apex shared between
        # ``apex`` field of one half and ``left``/``right`` of the other.
        if rounded_left_apex == rounded_right_apex:
            dart_concave = left.apex
        else:
            # Pick the vertex that is ``apex`` in BOTH halves (canonical case).
            # If only one is shared via ``apex``, fall back to the lexicographic
            # smaller spine endpoint as the 72-tip.
            dart_concave = left.apex
        dart_tip = next(p for p in spine_endpoints if _round_point(p) != _round_point(dart_concave))
    else:
        dart_concave = left.apex if rounded_left_apex in shared_rounded else right.apex
        dart_tip = next(p for p in spine_endpoints if _round_point(p) != _round_point(dart_concave))
    left_wing = next(
        p for p in (left.apex, left.left, left.right) if _round_point(p) not in shared_rounded
    )
    right_wing = next(
        p for p in (right.apex, right.left, right.right) if _round_point(p) not in shared_rounded
    )

    # Order wings so the polygon dart-tip -> wing -> concave -> wing is CCW.
    def _cross(o: Point) -> float:
        ax = o[0] - dart_tip[0]
        ay = o[1] - dart_tip[1]
        cx = dart_concave[0] - dart_tip[0]
        cy = dart_concave[1] - dart_tip[1]
        return ax * cy - ay * cx

    if _cross(left_wing) >= 0:
        first_wing, second_wing = left_wing, right_wing
    else:
        first_wing, second_wing = right_wing, left_wing
    return (dart_tip, first_wing, dart_concave, second_wing)


def acute_polygon(half: HalfTile) -> tuple[Point, Point, Point]:
    """Return an unpaired acute half-tile's vertices in CCW order."""
    if half.kind != ACUTE_HALF:
        raise ValueError("Expected an acute half-tile.")
    cross = (half.left[0] - half.apex[0]) * (half.right[1] - half.apex[1]) - (
        half.left[1] - half.apex[1]
    ) * (half.right[0] - half.apex[0])
    if cross >= 0:
        return (half.apex, half.left, half.right)
    return (half.apex, half.right, half.left)


def obtuse_polygon(half: HalfTile) -> tuple[Point, Point, Point]:
    """Return an unpaired obtuse half-tile's vertices in CCW order."""
    if half.kind != OBTUSE_HALF:
        raise ValueError("Expected an obtuse half-tile.")
    cross = (half.left[0] - half.apex[0]) * (half.right[1] - half.apex[1]) - (
        half.left[1] - half.apex[1]
    ) * (half.right[0] - half.apex[0])
    if cross >= 0:
        return (half.apex, half.left, half.right)
    return (half.apex, half.right, half.left)


__all__ = [
    "A",
    "B",
    "ACUTE_HALF",
    "OBTUSE_HALF",
    "PHI",
    "HalfTile",
    "PairingResult",
    "acute_polygon",
    "build_p2_sun_seed",
    "dart_polygon",
    "kite_polygon",
    "long_edges",
    "obtuse_polygon",
    "pair_halves_into_kites_and_darts",
    "short_edges",
    "substitute_all",
    "substitute_one",
]
