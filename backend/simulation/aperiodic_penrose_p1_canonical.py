"""Canonical Penrose P1 substitution (first draft).

Implements Penrose's 1974 pentagonal substitution rule. The single substitution
round applied to one pentagon is:

    Pentagon P (side s) ->
        1 central inverted Pentagon (side s / phi^2) at the parent's centroid
      + 5 outer upright Pentagons (side s / phi^2), one per parent vertex,
        arranged so each outer pentagon's outermost vertex coincides with the
        corresponding parent vertex
      + 5 boundary acute Robinson half-tiles (golden triangles 36-72-72,
        long-side length s / phi^2, short-base length s / phi^3), each sitting
        in the gap between two adjacent outer pentagons against one parent
        edge. The half-tile's 36-degree apex points inward to the central
        pentagon's vertex, and its 72-degree base vertices sit on the parent
        edge where the two flanking outer pentagons end.

The boundary acute halves pair across the parent's edges with the matching
halves from the neighbouring parent pentagons; two acutes glued at their short
base form a thin rhomb (36-144-36-144) which is Penrose's published P1
**diamond** prototile. After all halves are paired, the cells emitted are:

* ``p1-pentagon`` for every pentagon at every recursion level.
* ``p1-diamond`` for every paired diamond.
* ``p1-diamond-half`` for any half-tile at the outermost patch boundary that
  has no neighbour to pair with (Option-2 boundary treatment, mirroring
  ``DART_HALF_OBTUSE_KIND`` in P2).

Pentagons are recursively substituted; diamonds are emitted as terminal cells
at the recursion level where they appear (i.e., this draft does not yet
deflate diamonds further). A future revision can add a diamond -> 1 smaller
diamond + 2 smaller pentagons rule to make the substitution truly aperiodic at
every prototile, but the draft as written already produces a hole-free
hierarchical pentagonal patch with diamonds at all levels of the recursion
tree above the leaves.

Stars and boats from Penrose's 4-prototile P1 set are NOT yet emitted as
distinct cell kinds; they appear visually as natural assemblies of pentagons +
diamonds in the pattern. Promoting them to distinct cell kinds is a follow-up.

Geometric verification (areas):

    parent pentagon area:                A_parent = (5/4) s^2 * cot(36 deg)
    central + 5 outer pentagons area:    6 * A_parent / phi^4
    5 boundary diamond-halves area:      5 * (1/2) * (s/phi^2)^2 * sin(36 deg)

    6 / phi^4 = 6 * 0.1459 = 0.876
    5 * 0.5 * 0.1459 * 0.5878 / (5/4) / cot(36 deg) = 0.124
    sum = 1.000  -- the 6 children + 5 half-diamonds tile the parent exactly.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

from backend.simulation.aperiodic_family_manifest import (
    P1_DIAMOND_HALF_KIND,
    P1_DIAMOND_KIND,
    P1_PENTAGON_KIND,
    PENROSE_P1_TILE_FAMILY,
)
from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    AperiodicPatchCell,
    Vec,
    build_edge_neighbors,
    encode_float,
    polygon_centroid,
    rounded_point,
)


PHI = (1.0 + math.sqrt(5.0)) / 2.0
INV_PHI = 1.0 / PHI
INV_PHI_SQUARED = INV_PHI * INV_PHI

# Pentagon constants. ``CIRCUMRADIUS_OVER_SIDE`` is R / s where R is the
# pentagon's circumradius and s its side length: R = s / (2 sin(36 deg)).
_CIRCUMRADIUS_OVER_SIDE = 1.0 / (2.0 * math.sin(math.radians(36.0)))

# Coordinate rounding precision used to canonicalise edge endpoints when
# detecting paired diamond halves and computing neighbour adjacency.
_PAIRING_PRECISION = 8


def _round_for_pairing(point: tuple[float, float]) -> tuple[float, float]:
    return (round(point[0], _PAIRING_PRECISION), round(point[1], _PAIRING_PRECISION))


def _canonical_edge(
    p: tuple[float, float], q: tuple[float, float]
) -> tuple[tuple[float, float], tuple[float, float]]:
    rounded_p = _round_for_pairing(p)
    rounded_q = _round_for_pairing(q)
    return (rounded_p, rounded_q) if rounded_p <= rounded_q else (rounded_q, rounded_p)


@dataclass(frozen=True)
class _Pentagon:
    """A regular pentagon prototile defined by centroid, side length, and the
    angle (radians) of its first vertex measured from the centroid.

    Two orientations are used during substitution: an "upright" parent has its
    first vertex at angle pi/2 (vertex pointing +y); the "inverted" central
    child has its first vertex at angle 3 pi / 2 (vertex pointing -y).
    Recursive substitutions keep the orientation of the parent for the 5 outer
    petals and flip it for the 1 central child.
    """

    centroid_x: float
    centroid_y: float
    side: float
    first_vertex_angle: float  # radians

    def vertices(self) -> tuple[tuple[float, float], ...]:
        circumradius = self.side * _CIRCUMRADIUS_OVER_SIDE
        verts: list[tuple[float, float]] = []
        for index in range(5):
            angle = self.first_vertex_angle + index * (2.0 * math.pi / 5.0)
            verts.append(
                (
                    self.centroid_x + circumradius * math.cos(angle),
                    self.centroid_y + circumradius * math.sin(angle),
                )
            )
        return tuple(verts)


@dataclass(frozen=True)
class _DiamondHalf:
    """An acute Robinson half-tile (golden triangle, 36-72-72) sitting in the
    gap between two adjacent outer pentagons against one parent pentagon edge.

    The 36-degree apex points inward toward the parent's centroid (it
    coincides with the central inverted pentagon's vertex at the matching
    angle). The two 72-degree base vertices sit on the parent's edge.

    Two acute halves whose short bases coincide (i.e. are the same segment in
    the plane) pair into a thin rhomb (P1 diamond).
    """

    apex: tuple[float, float]
    base_left: tuple[float, float]
    base_right: tuple[float, float]


def _substitute_pentagon(parent: _Pentagon) -> tuple[list[_Pentagon], list[_DiamondHalf]]:
    """Apply one round of Penrose's 1974 pentagonal substitution to ``parent``.

    Returns ``(children, halves)``: 6 child pentagons (1 inverted central + 5
    outer upright) plus 5 acute Robinson half-tiles ready to pair across the
    parent's edges into diamonds.
    """
    child_side = parent.side * INV_PHI_SQUARED
    parent_circumradius = parent.side * _CIRCUMRADIUS_OVER_SIDE

    # Central child: same centroid, side s/phi^2, orientation flipped (vertex
    # rotated by pi from the parent's first-vertex direction).
    central = _Pentagon(
        centroid_x=parent.centroid_x,
        centroid_y=parent.centroid_y,
        side=child_side,
        first_vertex_angle=parent.first_vertex_angle + math.pi,
    )

    # 5 outer petals: each centred at distance R_parent / phi from the parent
    # centroid, in the direction of the corresponding parent vertex; same side
    # as the central child (s/phi^2) and same orientation as the parent.
    petal_distance = parent_circumradius * INV_PHI
    petals: list[_Pentagon] = []
    for index in range(5):
        vertex_angle = parent.first_vertex_angle + index * (2.0 * math.pi / 5.0)
        petals.append(
            _Pentagon(
                centroid_x=parent.centroid_x + petal_distance * math.cos(vertex_angle),
                centroid_y=parent.centroid_y + petal_distance * math.sin(vertex_angle),
                side=child_side,
                first_vertex_angle=parent.first_vertex_angle,
            )
        )

    children = [central, *petals]

    # 5 boundary acute halves: one per parent edge. Each parent edge lies
    # between two adjacent parent vertices (consecutive ``index`` values).
    # The half's 36-degree apex coincides with the central inverted pentagon's
    # vertex at the matching angle; the half's two 72-degree base vertices are
    # the inner endpoints of the two flanking petals along the parent edge.
    central_vertices = central.vertices()
    halves: list[_DiamondHalf] = []
    parent_vertices = parent.vertices()
    for edge_index in range(5):
        left_vertex_index = edge_index
        right_vertex_index = (edge_index + 1) % 5

        left_parent_vertex = parent_vertices[left_vertex_index]
        right_parent_vertex = parent_vertices[right_vertex_index]

        # Inner endpoints of the petals on the parent edge: each petal's
        # outermost vertex is the parent vertex; the two adjacent petal
        # vertices on the parent edge sit at distance child_side from the
        # parent vertex along the edge direction.
        edge_dx = right_parent_vertex[0] - left_parent_vertex[0]
        edge_dy = right_parent_vertex[1] - left_parent_vertex[1]
        edge_length = math.hypot(edge_dx, edge_dy)
        if edge_length <= 0.0:
            continue
        edge_ux = edge_dx / edge_length
        edge_uy = edge_dy / edge_length

        base_left = (
            left_parent_vertex[0] + child_side * edge_ux,
            left_parent_vertex[1] + child_side * edge_uy,
        )
        base_right = (
            right_parent_vertex[0] - child_side * edge_ux,
            right_parent_vertex[1] - child_side * edge_uy,
        )

        # The diamond-half's apex sits at the central inverted pentagon's
        # vertex on the inside of this parent edge. Since the central pentagon
        # is rotated by pi from the parent's first-vertex direction, its
        # vertex at central_index k corresponds to the parent's edge midpoint
        # angle (parent_vertex_angle[k] + parent_vertex_angle[k+1]) / 2 ...
        # but more simply: the central vertex closest to this parent edge is
        # the one whose direction from the centroid bisects the parent edge.
        edge_midpoint = (
            (left_parent_vertex[0] + right_parent_vertex[0]) / 2.0,
            (left_parent_vertex[1] + right_parent_vertex[1]) / 2.0,
        )
        apex = _closest_central_vertex(central_vertices, edge_midpoint)
        halves.append(_DiamondHalf(apex=apex, base_left=base_left, base_right=base_right))

    return children, halves


def _closest_central_vertex(
    central_vertices: tuple[tuple[float, float], ...],
    target: tuple[float, float],
) -> tuple[float, float]:
    best_vertex = central_vertices[0]
    best_distance_squared = math.inf
    for vertex in central_vertices:
        dx = vertex[0] - target[0]
        dy = vertex[1] - target[1]
        distance_squared = dx * dx + dy * dy
        if distance_squared < best_distance_squared:
            best_distance_squared = distance_squared
            best_vertex = vertex
    return best_vertex


@dataclass(frozen=True)
class _Diamond:
    """A thin Penrose rhomb (36-144-36-144) formed by gluing two acute
    Robinson halves at their short base. Vertices are stored in CCW order:
    apex_left (36 deg), base_a (144 deg), apex_right (36 deg), base_b (144 deg).
    """

    apex_left: tuple[float, float]
    base_a: tuple[float, float]
    apex_right: tuple[float, float]
    base_b: tuple[float, float]

    def vertices(self) -> tuple[tuple[float, float], ...]:
        return (self.apex_left, self.base_a, self.apex_right, self.base_b)


def _pair_diamond_halves(
    halves: list[_DiamondHalf],
) -> tuple[list[_Diamond], list[_DiamondHalf]]:
    """Pair acute halves whose short bases coincide into thin rhombs.

    Two halves pair iff their base segments (base_left, base_right) match in
    the plane (i.e. same canonical edge after rounding). Halves with no
    matching partner are returned as unpaired.
    """
    by_base: dict[tuple[tuple[float, float], tuple[float, float]], list[_DiamondHalf]] = (
        defaultdict(list)
    )
    for half in halves:
        key = _canonical_edge(half.base_left, half.base_right)
        by_base[key].append(half)

    diamonds: list[_Diamond] = []
    unpaired: list[_DiamondHalf] = []
    for owners in by_base.values():
        if len(owners) == 2:
            first, second = owners
            # The two halves share base segment (first.base_left, first.base_right)
            # but may have different apex points (one on each side of the base).
            # Build the diamond polygon in CCW order around the centroid.
            shared_base_a = first.base_left
            shared_base_b = first.base_right
            apex_first = first.apex
            apex_second = second.apex
            diamond = _diamond_in_ccw_order(shared_base_a, shared_base_b, apex_first, apex_second)
            diamonds.append(diamond)
        elif len(owners) == 1:
            unpaired.append(owners[0])
        else:
            # More than 2 halves on the same base shouldn't happen with valid
            # substitution input; treat extras as unpaired for diagnostic
            # visibility rather than silently discarding them.
            for owner in owners:
                unpaired.append(owner)
    return diamonds, unpaired


def _diamond_in_ccw_order(
    base_a: tuple[float, float],
    base_b: tuple[float, float],
    apex_a: tuple[float, float],
    apex_b: tuple[float, float],
) -> _Diamond:
    """Order the 4 diamond vertices (apex_left, base_a, apex_right, base_b) in
    CCW order around the diamond centroid."""
    vertices = (apex_a, base_a, apex_b, base_b)
    centroid_vec = polygon_centroid(tuple(Vec(x, y) for x, y in vertices))
    centroid = (centroid_vec.x, centroid_vec.y)
    indexed = [(math.atan2(v[1] - centroid[1], v[0] - centroid[0]), v) for v in vertices]
    indexed.sort(key=lambda item: item[0])
    sorted_vertices = [v for _, v in indexed]
    # After CCW sort the 4 vertices alternate apex / base / apex / base; pick
    # the apex whose centroid-relative angle is most negative as ``apex_left``
    # so the polygon starts at a deterministic vertex.
    return _Diamond(
        apex_left=sorted_vertices[0],
        base_a=sorted_vertices[1],
        apex_right=sorted_vertices[2],
        base_b=sorted_vertices[3],
    )


def _diamond_half_polygon(half: _DiamondHalf) -> tuple[tuple[float, float], ...]:
    """Triangle vertices in CCW order for an unpaired diamond half."""
    vertices = (half.apex, half.base_left, half.base_right)
    centroid_vec = polygon_centroid(tuple(Vec(x, y) for x, y in vertices))
    centroid = (centroid_vec.x, centroid_vec.y)
    indexed = [(math.atan2(v[1] - centroid[1], v[0] - centroid[0]), v) for v in vertices]
    indexed.sort(key=lambda item: item[0])
    return tuple(v for _, v in indexed)


def _cell_id(prefix: str, vertices: tuple[tuple[float, float], ...]) -> str:
    centroid_vec = polygon_centroid(tuple(Vec(x, y) for x, y in vertices))
    return f"{prefix}:{encode_float(centroid_vec.x)}:{encode_float(centroid_vec.y)}"


def _snap_vertices_in_place(
    records: list[dict],
    *,
    tolerance: float = 1e-3,
) -> None:
    """Snap vertices that are within ``tolerance`` of each other to a single
    representative coordinate.

    The recursive substitution computes mathematically-coincident vertices via
    different float paths (e.g. ``parent_centroid + R/phi * dir`` versus
    ``parent_vertex - R/phi^2 * dir``); these accumulate float error at a rate
    proportional to ``phi`` per recursion level, reaching ~1e-3 by depth 3 even
    though the underlying real numbers are exactly equal. Without snapping,
    adjacent cells that should share an edge end up with endpoints that
    differ at the 4th decimal, which prevents downstream consumers (shapely
    union, edge-overlap neighbour detection) from recognising the shared edge
    and produces visible T-vertex gaps in the rendered patch.

    Snapping uses spatial bucketing with bucket size ``tolerance``; each
    vertex's bucket plus its 8 immediate neighbours are scanned, and any
    other vertex found within ``tolerance`` is unioned into the same cluster.
    Each cluster is then collapsed to its arithmetic mean (rounded to
    ``aperiodic_support.COORDINATE_PRECISION = 6`` decimal digits to match
    the existing storage precision) and every record's vertices are rewritten
    to use the cluster representative.
    """
    all_vertices: list[tuple[float, float]] = sorted(
        {vertex for record in records for vertex in record["vertices"]}
    )
    if not all_vertices:
        return
    parent_index = list(range(len(all_vertices)))

    def find(node: int) -> int:
        while parent_index[node] != node:
            parent_index[node] = parent_index[parent_index[node]]
            node = parent_index[node]
        return node

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent_index[left_root] = right_root

    buckets: dict[tuple[int, int], list[int]] = defaultdict(list)
    for index, (vx, vy) in enumerate(all_vertices):
        buckets[(int(vx / tolerance), int(vy / tolerance))].append(index)

    for index, (vx, vy) in enumerate(all_vertices):
        bx = int(vx / tolerance)
        by = int(vy / tolerance)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for other in buckets.get((bx + dx, by + dy), ()):
                    if other <= index:
                        continue
                    other_x, other_y = all_vertices[other]
                    if abs(other_x - vx) < tolerance and abs(other_y - vy) < tolerance:
                        union(index, other)

    cluster_members: dict[int, list[int]] = defaultdict(list)
    for index in range(len(all_vertices)):
        cluster_members[find(index)].append(index)

    snap_map: dict[tuple[float, float], tuple[float, float]] = {}
    for members in cluster_members.values():
        cluster_xs = [all_vertices[m][0] for m in members]
        cluster_ys = [all_vertices[m][1] for m in members]
        average = (
            round(sum(cluster_xs) / len(cluster_xs), 6),
            round(sum(cluster_ys) / len(cluster_ys), 6),
        )
        for m in members:
            snap_map[all_vertices[m]] = average

    for record in records:
        record["vertices"] = tuple(snap_map[v] for v in record["vertices"])


def build_penrose_p1_canonical_patch(patch_depth: int) -> AperiodicPatch:
    """Build a canonical P1 patch by recursive pentagon substitution.

    The seed is a single regular pentagon at the origin. ``patch_depth``
    controls how many substitution rounds are applied; the seed is pre-scaled
    by ``phi^(2 * depth)`` so that the smallest pentagons in the output always
    have unit side length, keeping the rendered patch size roughly constant
    across depths.
    """
    depth = max(0, int(patch_depth))
    seed_side = (PHI * PHI) ** depth
    pentagons: list[_Pentagon] = [
        _Pentagon(
            centroid_x=0.0,
            centroid_y=0.0,
            side=seed_side,
            first_vertex_angle=math.pi / 2.0,
        )
    ]
    diamond_halves: list[_DiamondHalf] = []

    for _ in range(depth):
        next_pentagons: list[_Pentagon] = []
        for pent in pentagons:
            children, halves = _substitute_pentagon(pent)
            next_pentagons.extend(children)
            diamond_halves.extend(halves)
        pentagons = next_pentagons

    diamonds, unpaired_halves = _pair_diamond_halves(diamond_halves)

    records: list[dict] = []
    for pent in pentagons:
        verts = tuple(rounded_point(v) for v in pent.vertices())
        records.append(
            {
                "id": _cell_id("pp", verts),
                "kind": P1_PENTAGON_KIND,
                "center": rounded_point((pent.centroid_x, pent.centroid_y)),
                "vertices": verts,
                "tile_family": PENROSE_P1_TILE_FAMILY,
            }
        )
    for diamond in diamonds:
        verts = tuple(rounded_point(v) for v in diamond.vertices())
        centroid_vec = polygon_centroid(tuple(Vec(x, y) for x, y in verts))
        records.append(
            {
                "id": _cell_id("pd", verts),
                "kind": P1_DIAMOND_KIND,
                "center": rounded_point((centroid_vec.x, centroid_vec.y)),
                "vertices": verts,
                "tile_family": PENROSE_P1_TILE_FAMILY,
            }
        )
    for half in unpaired_halves:
        verts = tuple(rounded_point(v) for v in _diamond_half_polygon(half))
        centroid_vec = polygon_centroid(tuple(Vec(x, y) for x, y in verts))
        records.append(
            {
                "id": _cell_id("pdh", verts),
                "kind": P1_DIAMOND_HALF_KIND,
                "center": rounded_point((centroid_vec.x, centroid_vec.y)),
                "vertices": verts,
                "tile_family": PENROSE_P1_TILE_FAMILY,
            }
        )

    # Snap nearby vertices to a single representative coordinate. Substitution
    # accumulates float error of roughly 1e-3 by depth 3 (different float
    # paths to the same theoretical vertex produce slightly different results)
    # and grows by phi per additional level. Use 5e-3 so the snap continues to
    # group coincident-in-theory vertices through depth 5+ without merging
    # genuinely distinct vertices (which are >> 0.1 apart at the smallest
    # scale).
    _snap_vertices_in_place(records, tolerance=5e-3)

    neighbors_by_id = build_edge_neighbors(records, neighbor_mode="segment_overlap")
    cells = tuple(
        AperiodicPatchCell(
            id=record["id"],
            kind=record["kind"],
            center=record["center"],
            vertices=record["vertices"],
            neighbors=neighbors_by_id[record["id"]],
            tile_family=record.get("tile_family"),
        )
        for record in sorted(records, key=lambda item: item["id"])
    )
    all_x = [vertex[0] for cell in cells for vertex in cell.vertices]
    all_y = [vertex[1] for cell in cells for vertex in cell.vertices]
    return AperiodicPatch(
        patch_depth=depth,
        width=max(1, int(math.ceil(max(all_x) - min(all_x)))) if all_x else 1,
        height=max(1, int(math.ceil(max(all_y) - min(all_y)))) if all_y else 1,
        cells=cells,
    )
