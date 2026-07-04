from __future__ import annotations

import math
from collections import defaultdict, deque
from functools import lru_cache

from backend.simulation.aperiodic_family_manifest import (
    DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND,
    DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY,
    DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND,
)
from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    PatchRecord,
    patch_from_records,
)

# Schlottmann quasi-periodic square-triangle substitution (12-fold).
#
# The marked substitution uses five prototiles -- three marked unit
# equilateral triangles (red / yellow / blue) and two marked unit squares
# (plain / marked) -- with linear inflation factor 2 + sqrt(3). The rule is
# a pseudo substitution: supertiles interlock, so children on a supertile
# boundary are emitted by both adjacent supertiles and must be deduplicated.
#
# The child placements below were extracted from the substitution-rule figure
# of the Tilings Encyclopedia "square-triangle" entry (M. Schlottmann) and
# verified tile-for-tile (colors included) against the encyclopedia's own
# 4999-cell finite patch via a two-level supertile decomposition: every child
# pose is pinned by that decomposition, expansion of the decomposed coarse
# configuration reproduces the literature patch exactly, sigma^2 patches are
# gap- and overlap-free, and the triangle:square census converges to the
# canonical 4/sqrt(3) ratio.
#
# Sources:
# https://tilings.math.uni-bielefeld.de/substitution/square-triangle/
#
# Coordinates live in the ring Z[zeta], zeta = exp(i*pi/6): a point is an
# integer 4-tuple (a, b, c, d) representing a + b*zeta + c*zeta^2 + d*zeta^3
# (zeta^4 = zeta^2 - 1). All tile vertices are exact; floats appear only in
# the emitted records. A placed tile is (label, (k, m, t)): reflect across
# the y axis if m, rotate by k*30 degrees, then translate by t.

_SQRT3 = math.sqrt(3.0)
_COS30 = _SQRT3 / 2.0
_COORD_DECIMALS = 6

_TRIANGLE_RED = "triangle-red"
_TRIANGLE_YELLOW = "triangle-yellow"
_TRIANGLE_BLUE = "triangle-blue"
_SQUARE_PLAIN = "square-plain"
_SQUARE_MARKED = "square-marked"

_TILE_FAMILY = DODECAGONAL_SQUARE_TRIANGLE_TILE_FAMILY
_SQUARE_KIND = DODECAGONAL_SQUARE_TRIANGLE_SQUARE_KIND
_TRIANGLE_KIND = DODECAGONAL_SQUARE_TRIANGLE_TRIANGLE_KIND

_PUBLIC_KIND = {
    _TRIANGLE_RED: _TRIANGLE_KIND,
    _TRIANGLE_YELLOW: _TRIANGLE_KIND,
    _TRIANGLE_BLUE: _TRIANGLE_KIND,
    _SQUARE_PLAIN: _SQUARE_KIND,
    _SQUARE_MARKED: _SQUARE_KIND,
}
_TRIANGLE_CHIRALITY = {
    _TRIANGLE_RED: "red",
    _TRIANGLE_YELLOW: "yellow",
    _TRIANGLE_BLUE: "blue",
}
_ID_CODE = {
    _TRIANGLE_RED: "tr",
    _TRIANGLE_YELLOW: "ty",
    _TRIANGLE_BLUE: "tb",
    _SQUARE_PLAIN: "sp",
    _SQUARE_MARKED: "sm",
}

_PROTOTILE_VERTICES: dict[str, tuple[tuple[int, int, int, int], ...]] = {
    _TRIANGLE_RED: ((0, 0, 0, 0), (0, 0, -1, 0), (1, 0, -1, 0)),
    _TRIANGLE_BLUE: ((0, 0, 0, 0), (0, 0, -1, 0), (1, 0, -1, 0)),
    _TRIANGLE_YELLOW: ((0, 0, 0, 0), (0, 0, -1, 0), (1, 0, -1, 0)),
    _SQUARE_MARKED: ((0, 0, 0, 0), (-1, 0, 0, 0), (-1, 0, 0, -1), (0, 0, 0, -1)),
    _SQUARE_PLAIN: ((0, 0, 0, 0), (-1, 0, 0, 0), (-1, 0, 0, -1), (0, 0, 0, -1)),
}

_SUBSTITUTION_RULES: dict[
    str,
    tuple[tuple[str, int, int, tuple[int, int, int, int]], ...],
] = {
    _TRIANGLE_RED: (
        (_SQUARE_PLAIN, 6, 0, (0, 0, -1, -1)),
        (_SQUARE_PLAIN, 10, 0, (1, 0, -2, -1)),
        (_SQUARE_PLAIN, 2, 0, (1, 0, -1, -1)),
        (_TRIANGLE_RED, 0, 0, (0, 0, 0, 0)),
        (_TRIANGLE_RED, 0, 0, (1, 1, -1, -2)),
        (_TRIANGLE_RED, 0, 0, (0, -1, -1, -1)),
        (_TRIANGLE_BLUE, 11, 0, (0, 0, -1, 0)),
        (_TRIANGLE_BLUE, 1, 0, (1, 0, -1, 0)),
        (_TRIANGLE_BLUE, 7, 0, (1, 1, -1, -2)),
        (_TRIANGLE_BLUE, 5, 0, (0, -1, -1, -1)),
        (_TRIANGLE_BLUE, 3, 0, (1, -1, -2, -1)),
        (_TRIANGLE_BLUE, 9, 0, (1, 1, -2, -2)),
        (_TRIANGLE_YELLOW, 2, 0, (0, 0, -1, -1)),
    ),
    _TRIANGLE_BLUE: (
        (_SQUARE_PLAIN, 5, 0, (0, -1, -1, 0)),
        (_SQUARE_PLAIN, 7, 0, (1, 0, -1, -1)),
        (_TRIANGLE_RED, 3, 0, (0, -1, 0, 0)),
        (_TRIANGLE_RED, 1, 0, (0, 0, 0, 0)),
        (_TRIANGLE_RED, 0, 0, (0, -1, -1, -1)),
        (_TRIANGLE_RED, 0, 0, (1, 1, -1, -2)),
        (_TRIANGLE_BLUE, 0, 0, (0, 0, 0, -1)),
        (_TRIANGLE_BLUE, 6, 0, (1, 0, -2, -1)),
        (_TRIANGLE_BLUE, 3, 0, (1, -1, -2, -1)),
        (_TRIANGLE_BLUE, 9, 0, (1, 1, -2, -2)),
        (_SQUARE_MARKED, 10, 1, (0, 0, -1, -1)),
        (_SQUARE_MARKED, 2, 0, (1, 0, -1, -1)),
        (_TRIANGLE_YELLOW, 3, 0, (1, 0, -1, -1)),
        (_TRIANGLE_YELLOW, 1, 0, (0, -1, -1, 0)),
    ),
    _TRIANGLE_YELLOW: (
        (_SQUARE_PLAIN, 5, 0, (0, -1, -1, 0)),
        (_SQUARE_PLAIN, 7, 0, (1, 0, -1, -1)),
        (_SQUARE_PLAIN, 1, 0, (1, 1, -1, -1)),
        (_SQUARE_PLAIN, 11, 0, (0, 0, -1, -1)),
        (_SQUARE_PLAIN, 9, 0, (1, 0, -2, -2)),
        (_SQUARE_PLAIN, 3, 0, (1, 0, -2, -1)),
        (_TRIANGLE_RED, 3, 0, (0, -1, 0, 0)),
        (_TRIANGLE_RED, 1, 0, (0, 0, 0, 0)),
        (_TRIANGLE_RED, 2, 0, (0, 0, -1, -1)),
        (_TRIANGLE_RED, 1, 0, (0, -1, -2, 0)),
        (_TRIANGLE_RED, 3, 0, (2, 0, -2, -1)),
        (_TRIANGLE_RED, 3, 0, (0, -1, -2, -1)),
        (_TRIANGLE_RED, 1, 0, (2, 0, -2, -1)),
        (_TRIANGLE_BLUE, 0, 0, (0, 0, 0, -1)),
        (_TRIANGLE_BLUE, 4, 0, (0, 0, -2, -1)),
        (_TRIANGLE_BLUE, 8, 0, (2, 0, -2, -1)),
    ),
    _SQUARE_MARKED: (
        (_SQUARE_PLAIN, 9, 0, (-1, -1, 0, 0)),
        (_SQUARE_PLAIN, 6, 0, (0, 0, -1, -1)),
        (_SQUARE_PLAIN, 0, 0, (-1, -2, -1, 0)),
        (_SQUARE_PLAIN, 0, 0, (1, 0, -1, -1)),
        (_SQUARE_PLAIN, 10, 0, (0, -1, -2, -1)),
        (_SQUARE_PLAIN, 2, 0, (0, -1, -1, -1)),
        (_TRIANGLE_RED, 3, 0, (-2, -2, 0, 1)),
        (_TRIANGLE_RED, 2, 0, (-1, 0, 0, 0)),
        (_TRIANGLE_RED, 1, 0, (-2, -2, 0, 1)),
        (_TRIANGLE_RED, 0, 0, (0, 0, 0, 0)),
        (_TRIANGLE_RED, 1, 0, (0, -1, -1, 0)),
        (_TRIANGLE_RED, 2, 0, (-2, -2, -1, -1)),
        (_TRIANGLE_RED, 2, 0, (0, 0, -1, -2)),
        (_TRIANGLE_RED, 0, 0, (-1, -2, -1, -1)),
        (_TRIANGLE_RED, 0, 0, (0, 0, -1, -2)),
        (_TRIANGLE_BLUE, 2, 0, (-2, -1, 0, 0)),
        (_TRIANGLE_BLUE, 8, 0, (0, -1, -1, 0)),
        (_TRIANGLE_BLUE, 11, 0, (0, 0, -1, 0)),
        (_TRIANGLE_BLUE, 11, 0, (-1, -1, -1, 0)),
        (_TRIANGLE_BLUE, 5, 0, (-1, -2, -1, -1)),
        (_TRIANGLE_BLUE, 7, 0, (0, 0, -1, -2)),
        (_TRIANGLE_BLUE, 3, 0, (0, -2, -2, -1)),
        (_TRIANGLE_BLUE, 9, 0, (0, 0, -2, -2)),
        (_SQUARE_MARKED, 4, 0, (-1, -1, 0, 0)),
        (_SQUARE_MARKED, 7, 0, (-1, -2, -1, 0)),
        (_SQUARE_MARKED, 3, 1, (-1, -1, -1, -1)),
        (_TRIANGLE_YELLOW, 1, 0, (-1, -1, 0, 1)),
        (_TRIANGLE_YELLOW, 0, 0, (-2, -2, 0, 0)),
        (_TRIANGLE_YELLOW, 2, 0, (-1, -1, -1, -1)),
    ),
    _SQUARE_PLAIN: (
        (_SQUARE_PLAIN, 9, 0, (-1, -1, 0, 0)),
        (_SQUARE_PLAIN, 3, 0, (-1, -1, 0, 1)),
        (_SQUARE_PLAIN, 6, 0, (-1, -1, -1, -1)),
        (_SQUARE_PLAIN, 0, 0, (-1, -2, -1, 0)),
        (_SQUARE_PLAIN, 0, 0, (1, 0, -1, -1)),
        (_SQUARE_PLAIN, 10, 0, (0, -1, -2, -1)),
        (_SQUARE_PLAIN, 2, 0, (0, -1, -1, -1)),
        (_TRIANGLE_RED, 3, 0, (-2, -2, 0, 1)),
        (_TRIANGLE_RED, 1, 0, (0, -1, 0, 1)),
        (_TRIANGLE_RED, 1, 0, (-2, -2, 0, 1)),
        (_TRIANGLE_RED, 3, 0, (0, -1, 0, 0)),
        (_TRIANGLE_RED, 0, 0, (-1, -1, 0, 0)),
        (_TRIANGLE_RED, 2, 0, (-2, -2, -1, -1)),
        (_TRIANGLE_RED, 2, 0, (0, 0, -1, -2)),
        (_TRIANGLE_RED, 0, 0, (-1, -2, -1, -1)),
        (_TRIANGLE_RED, 0, 0, (0, 0, -1, -2)),
        (_TRIANGLE_BLUE, 2, 0, (-2, -1, 0, 0)),
        (_TRIANGLE_BLUE, 10, 0, (0, -1, 0, 0)),
        (_TRIANGLE_BLUE, 11, 0, (-1, -1, -1, 0)),
        (_TRIANGLE_BLUE, 1, 0, (0, -1, -1, 0)),
        (_TRIANGLE_BLUE, 5, 0, (-1, -2, -1, -1)),
        (_TRIANGLE_BLUE, 7, 0, (0, 0, -1, -2)),
        (_TRIANGLE_BLUE, 9, 0, (0, 0, -2, -2)),
        (_TRIANGLE_BLUE, 3, 0, (0, -2, -2, -1)),
        (_SQUARE_MARKED, 7, 0, (-1, -2, -1, 0)),
        (_SQUARE_MARKED, 5, 1, (0, 0, -1, -1)),
        (_TRIANGLE_YELLOW, 0, 0, (-2, -2, 0, 0)),
        (_TRIANGLE_YELLOW, 0, 0, (0, 0, 0, -1)),
        (_TRIANGLE_YELLOW, 2, 0, (-1, -1, -1, -1)),
    ),
}

# The blue triangle's rule contains a blue-triangle child at the identity
# pose strictly inside the supertile: (_TRIANGLE_BLUE, 0, 0, _SELF_SLOT_T).
# Iterating that slot yields a substitution fixed point, so patches of any
# requested depth converge around one anchor tile and cell ids stay stable.
_SEED_LABEL = _TRIANGLE_BLUE
_SELF_SLOT_T = (0, 0, 0, -1)

Module = tuple[int, int, int, int]
Pose = tuple[int, int, Module]


def _madd(v: Module, w: Module) -> Module:
    return (v[0] + w[0], v[1] + w[1], v[2] + w[2], v[3] + w[3])


def _mmulz(v: Module) -> Module:
    a, b, c, d = v
    return (-d, a, b + d, c)


def _mrot(v: Module, k: int) -> Module:
    for _ in range(k % 12):
        v = _mmulz(v)
    return v


def _mmirror(v: Module) -> Module:
    a, b, c, d = v
    return (-a - c, -b, c, b + d)


def _mscale_lam(v: Module) -> Module:
    """Multiply by 2 + sqrt(3) = 2 + 2*zeta - zeta^3."""
    vz = _mmulz(v)
    vz3 = _mmulz(_mmulz(vz))
    return (
        2 * v[0] + 2 * vz[0] - vz3[0],
        2 * v[1] + 2 * vz[1] - vz3[1],
        2 * v[2] + 2 * vz[2] - vz3[2],
        2 * v[3] + 2 * vz[3] - vz3[3],
    )


def _mscale_lam_inv(v: Module) -> Module:
    """Multiply by 2 - sqrt(3) = 2 - 2*zeta + zeta^3."""
    vz = _mmulz(v)
    vz3 = _mmulz(_mmulz(vz))
    return (
        2 * v[0] - 2 * vz[0] + vz3[0],
        2 * v[1] - 2 * vz[1] + vz3[1],
        2 * v[2] - 2 * vz[2] + vz3[2],
        2 * v[3] - 2 * vz[3] + vz3[3],
    )


def _module_xy(v: Module) -> tuple[float, float]:
    a, b, c, d = v
    return (a + b * _COS30 + c * 0.5, b * 0.5 + c * _COS30 + d)


def _pose_apply(pose: Pose, v: Module) -> Module:
    k, m, t = pose
    w = _mmirror(v) if m else v
    return _madd(_mrot(w, k), t)


def _pose_compose(outer: Pose, inner: Pose) -> Pose:
    k2, m2, t2 = outer
    k1, m1, t1 = inner
    k = (k2 + (k1 if not m2 else -k1)) % 12
    m = (m1 + m2) % 2
    tt = _mmirror(t1) if m2 else t1
    return (k, m, _madd(_mrot(tt, k2), t2))


@lru_cache(maxsize=8)
def _seed_pose_translation(levels: int) -> Module:
    """Top-level translation T with lam^levels * T + sum(lam^i * tau) = 0, so
    the recurrent self-slot leaf lands exactly at the identity pose."""
    t: Module = (0, 0, 0, 0)
    for _ in range(levels):
        t = _mscale_lam_inv(
            (
                t[0] - _SELF_SLOT_T[0],
                t[1] - _SELF_SLOT_T[1],
                t[2] - _SELF_SLOT_T[2],
                t[3] - _SELF_SLOT_T[3],
            )
        )
    return t


def _expand_pruned(
    levels: int,
    ball_radius: float,
) -> dict[tuple[Module, ...], tuple[str, Pose]]:
    """Expand the anchored seed, pruning subtrees that cannot reach the ball
    of ball_radius around the origin. Returns tiles deduplicated by exact
    geometry (boundary children are emitted by both adjacent supertiles)."""
    lam = 2.0 + _SQRT3
    tiles: dict[tuple[Module, ...], tuple[str, Pose]] = {}

    def region_reaches_ball(t: Module, remaining: int) -> bool:
        x, y = _module_xy(t)
        scale = lam**remaining
        return math.hypot(x * scale, y * scale) - scale * 3.0 <= ball_radius + 1.0

    def walk(label: str, pose: Pose, remaining: int) -> None:
        if not region_reaches_ball(pose[2], remaining):
            return
        if remaining == 0:
            verts = tuple(sorted(_pose_apply(pose, v) for v in _PROTOTILE_VERTICES[label]))
            existing = tiles.get(verts)
            if existing is not None:
                if existing[0] != label:
                    raise AssertionError(
                        f"substitution conflict at {verts}: {existing[0]} vs {label}"
                    )
                return
            tiles[verts] = (label, pose)
            return
        k, m, t = pose
        scaled = (k, m, _mscale_lam(t))
        for child_label, ck, cm, ct in _SUBSTITUTION_RULES[label]:
            walk(child_label, _pose_compose(scaled, (ck, cm, ct)), remaining - 1)

    walk(_SEED_LABEL, (0, 0, _seed_pose_translation(levels)), levels)
    return tiles


def _levels_for_radius(ball_radius: float) -> int:
    """The anchor tile sits >= 0.5 * lam^(n-1) units inside its level-n
    supertile, so pick n with that margin beyond the requested ball."""
    lam = 2.0 + _SQRT3
    levels = 1
    while 0.5 * lam ** (levels - 1) < ball_radius + 2.0:
        levels += 1
    return levels


def _canonical_vertex_order(
    verts_sorted: tuple[Module, ...],
) -> tuple[Module, ...]:
    """Counter-clockwise cyclic order starting from the lexicographic-min
    vertex: representative-independent, so records are deterministic."""
    xy = [_module_xy(v) for v in verts_sorted]
    cx = sum(p[0] for p in xy) / len(xy)
    cy = sum(p[1] for p in xy) / len(xy)
    order = sorted(
        range(len(verts_sorted)),
        key=lambda i: math.atan2(xy[i][1] - cy, xy[i][0] - cx),
    )
    start = min(range(len(order)), key=lambda j: verts_sorted[order[j]])
    return tuple(verts_sorted[order[(start + j) % len(order)]] for j in range(len(order)))


def _orientation_token_from_first_edge(
    vertices: tuple[tuple[float, float], ...],
) -> str:
    edge = (
        vertices[1][0] - vertices[0][0],
        vertices[1][1] - vertices[0][1],
    )
    angle = math.degrees(math.atan2(edge[1], edge[0])) % 360.0
    return str(int(round(angle / 30.0) * 30) % 360)


def _record_for_tile(
    label: str,
    verts_sorted: tuple[Module, ...],
) -> PatchRecord:
    ordered = _canonical_vertex_order(verts_sorted)
    float_verts = tuple(
        (
            round(_module_xy(v)[0], _COORD_DECIMALS),
            round(_module_xy(v)[1], _COORD_DECIMALS),
        )
        for v in ordered
    )
    center = (
        round(sum(v[0] for v in float_verts) / len(float_verts), _COORD_DECIMALS),
        round(sum(v[1] for v in float_verts) / len(float_verts), _COORD_DECIMALS),
    )
    anchor = ordered[0]
    tile_id = (
        f"dst:st:{_ID_CODE[label]}:{anchor[0]}:{anchor[1]}:{anchor[2]}:{anchor[3]}:"
        f"{_orientation_token_from_first_edge(float_verts)}"
    )
    return {
        "id": tile_id,
        "kind": _PUBLIC_KIND[label],
        "center": center,
        "vertices": float_verts,
        "tile_family": _TILE_FAMILY,
        "orientation_token": _orientation_token_from_first_edge(float_verts),
        "chirality_token": _TRIANGLE_CHIRALITY.get(label),
        "decoration_tokens": None,
    }


def _bfs_distances(
    tiles: dict[tuple[Module, ...], tuple[str, Pose]],
    seed_key: tuple[Module, ...],
) -> dict[tuple[Module, ...], int]:
    edge_owners: dict[
        tuple[Module, Module],
        list[tuple[Module, ...]],
    ] = defaultdict(list)
    for key in tiles:
        ordered = _canonical_vertex_order(key)
        count = len(ordered)
        for index in range(count):
            head = ordered[index]
            tail = ordered[(index + 1) % count]
            edge_key = (head, tail) if head < tail else (tail, head)
            edge_owners[edge_key].append(key)

    adjacency: dict[tuple[Module, ...], set[tuple[Module, ...]]] = defaultdict(set)
    for owners in edge_owners.values():
        for left_index in range(len(owners)):
            for right_index in range(left_index + 1, len(owners)):
                left = owners[left_index]
                right = owners[right_index]
                if left == right:
                    continue
                adjacency[left].add(right)
                adjacency[right].add(left)

    distances: dict[tuple[Module, ...], int] = {seed_key: 0}
    queue: deque[tuple[Module, ...]] = deque((seed_key,))
    while queue:
        current = queue.popleft()
        for neighbor in adjacency[current]:
            if neighbor in distances:
                continue
            distances[neighbor] = distances[current] + 1
            queue.append(neighbor)
    return distances


def _seed_key(
    tiles: dict[tuple[Module, ...], tuple[str, Pose]],
) -> tuple[Module, ...]:
    """The square nearest the anchor point, for parity with the previous
    runtime's square-seeded crop."""

    def centre_radius(key: tuple[Module, ...]) -> float:
        xy = [_module_xy(v) for v in key]
        cx = sum(p[0] for p in xy) / len(xy)
        cy = sum(p[1] for p in xy) / len(xy)
        return math.hypot(cx, cy)

    squares = [key for key, (label, _) in tiles.items() if _PUBLIC_KIND[label] == _SQUARE_KIND]
    pool = squares if squares else list(tiles)
    return min(pool, key=lambda key: (centre_radius(key), key))


def build_dodecagonal_square_triangle_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = int(patch_depth)
    if resolved_depth < 0:
        raise ValueError("patch_depth must be non-negative")

    ball_radius = 0.75 * resolved_depth + 4.0
    for _ in range(4):
        levels = _levels_for_radius(ball_radius)
        tiles = _expand_pruned(levels, ball_radius)
        seed_key = _seed_key(tiles)
        distances = _bfs_distances(tiles, seed_key)
        if distances and max(distances.values()) >= resolved_depth:
            break
        ball_radius *= 1.5

    selected = [key for key, distance in distances.items() if distance <= resolved_depth]
    records = [_record_for_tile(tiles[key][0], key) for key in selected]
    return patch_from_records(
        resolved_depth,
        records,
        edge_precision=_COORD_DECIMALS,
    )
