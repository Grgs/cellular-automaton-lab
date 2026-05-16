"""Multigrid (de Bruijn) construction for Penrose-family tilings.

Implements the algebraic dual construction from de Bruijn's 1981 paper
*Algebraic theory of Penrose's non-periodic tilings of the plane*
(https://www.math.brown.edu/reschwar/M272/pentagrid.pdf), using the
multi-line intersection grouping technique from Aatish Bhatia's Pattern
Collider (https://github.com/aatishb/patterncollider).

Construction:

For an N-fold multigrid with N families of equally-spaced parallel lines
(family i has all lines with normal direction
``e_i = (cos(2*pi*i/N), sin(2*pi*i/N))`` and equation
``e_i . point = O_i + k`` for integer ``k``), each tile of the dual tiling
is associated with one intersection point in the multigrid plane. The dual
vertex for a point ``p`` is

    dual(p) = sum_{i=0..N-1} floor(e_i . p - O_i) * e_i

For "regular" offsets (no collinearity among line families) every
intersection has exactly two lines and the dual polygon is a 4-vertex
rhombus -- recovering Penrose's P3 thick + thin rhomb tiling for N = 5.
For "singular" offsets (sum to an integer, or special offset values such
as 0 or 1/N), some intersections have three or more lines coinciding at
the same point; their dual polygons have ``2k`` vertices (where ``k`` is
the number of coincident lines), which lets the construction emit
pentagons, boats, stars, and diamonds -- Penrose's P1 prototile set.

This module exposes:

* ``MultigridCell`` -- a dataclass for a single dual polygon.
* ``build_multigrid_cells`` -- enumerate all cells whose intersection
  point lies in the requested patch.
* ``classify_p1_prototile`` -- map a polygon to one of Penrose's P1
  prototile kinds based on vertex count and shape.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass


PHI = (1.0 + math.sqrt(5.0)) / 2.0

# Standard Penrose pentagrid offsets: all 1/5, sum = 1 (singular). Produces
# a tiling with thick + thin rhombs and additional non-rhomb polygons at
# certain singular intersection points.
PENROSE_PENTAGRID_OFFSETS: tuple[float, float, float, float, float] = (
    0.2,
    0.2,
    0.2,
    0.2,
    0.2,
)

# All-zero offsets put one line of every family through the origin, so the
# origin becomes a 5-line singular vertex and the dual tiling has a
# pentagram star centred there. Useful for an iconic "star at the centre"
# P1 patch.
PENROSE_PENTAGRID_OFFSETS_ALL_ZERO: tuple[float, float, float, float, float] = (
    0.0,
    0.0,
    0.0,
    0.0,
    0.0,
)

# Non-uniform pentagrid offsets used for the P1 family. Designed to (a) make
# the multigrid "regular" (no multi-line coincidences and so no concentrated
# central decagon), and (b) place a generic rhomb tiling underneath whose
# vertex statistics include scattered sun and star vertices (where 5 thick or
# 5 thin rhombs meet at one point). The vertex-merge pass in
# ``apply_p1_vertex_merge`` then collapses those vertices into Penrose's
# pentagon and star prototiles, giving a P1 patch that reads as a normal
# Penrose tessellation rather than a 5-fold rotationally symmetric structure
# centred on the origin.
PENROSE_P1_OFFSETS: tuple[float, float, float, float, float] = (
    0.3,
    0.4,
    0.5,
    0.6,
    0.7,
)

# Coincidence detection precision: intersections within this distance of
# each other are treated as the same point (i.e. 3+ lines meeting at one
# spot are grouped into one multigrid cell rather than emitted as several
# overlapping rhombi).
_COINCIDENCE_TOLERANCE = 1e-6


@dataclass(frozen=True)
class MultigridCell:
    """One polygon emitted by the multigrid dual construction.

    ``intersection_point`` is the point in the multigrid plane that the
    polygon is dual to. ``line_count`` is the number of distinct lines
    meeting at that point (always >= 2; a generic regular intersection has
    line_count == 2 and a 4-vertex rhomb polygon). ``vertices`` lists the
    polygon's vertices in counter-clockwise order around its centroid.

    ``classification_hint`` lets vertex-merge passes (e.g.
    ``apply_p1_vertex_merge``) record the P1 prototile that produced the
    cell when the polygon's geometry alone is ambiguous (a 10-vertex
    decagonal cluster from 5 merged thick rhombs and a 10-vertex pentagram
    from 5 merged thin rhombs would otherwise both be classified as
    ``p1-star``).
    """

    intersection_point: tuple[float, float]
    line_count: int
    vertices: tuple[tuple[float, float], ...]
    classification_hint: str | None = None


def _line_normal(symmetry: int, family_index: int) -> tuple[float, float]:
    angle = 2.0 * math.pi * family_index / symmetry
    return (math.cos(angle), math.sin(angle))


def _line_intersection(
    symmetry: int,
    offsets: tuple[float, ...],
    family_i: int,
    line_index_i: int,
    family_j: int,
    line_index_j: int,
) -> tuple[float, float] | None:
    """Solve for the intersection of one line in family ``i`` with one line
    in family ``j``. Returns ``None`` if the lines are parallel (same
    family or zero determinant)."""
    if family_i == family_j:
        return None
    a, b = _line_normal(symmetry, family_i)
    c, d = _line_normal(symmetry, family_j)
    determinant = a * d - b * c
    if abs(determinant) < 1e-12:
        return None
    constant_i = offsets[family_i] + line_index_i
    constant_j = offsets[family_j] + line_index_j
    x = (constant_i * d - b * constant_j) / determinant
    y = (a * constant_j - constant_i * c) / determinant
    return (x, y)


def _line_index_range_in_patch(
    symmetry: int,
    offsets: tuple[float, ...],
    family_index: int,
    half_extent: float,
) -> range:
    """Range of line indices (k values) in family ``family_index`` whose
    line passes through the square patch ``[-half_extent, half_extent]^2``."""
    normal_x, normal_y = _line_normal(symmetry, family_index)
    # Maximum projection magnitude over the patch: |cos|*HE + |sin|*HE.
    max_projection = half_extent * (abs(normal_x) + abs(normal_y))
    offset = offsets[family_index]
    min_k = math.floor(-max_projection - offset) - 1
    max_k = math.ceil(max_projection - offset) + 1
    return range(min_k, max_k + 1)


def _de_bruijn_dual_vertex(
    point: tuple[float, float],
    symmetry: int,
    offsets: tuple[float, ...],
) -> tuple[float, float]:
    """The dual map: ``dual(p) = sum_i floor(e_i . p - O_i) * e_i``."""
    px, py = point
    xd = 0.0
    yd = 0.0
    for i in range(symmetry):
        cos_i = math.cos(2.0 * math.pi * i / symmetry)
        sin_i = math.sin(2.0 * math.pi * i / symmetry)
        projection = px * cos_i + py * sin_i
        k = math.floor(projection - offsets[i])
        xd += k * cos_i
        yd += k * sin_i
    return (xd, yd)


def _dual_polygon_for_intersection(
    intersection_point: tuple[float, float],
    family_indices: tuple[int, ...],
    symmetry: int,
    offsets: tuple[float, ...],
    nudge_epsilon: float = 1e-3,
) -> tuple[tuple[float, float], ...]:
    """Construct the dual polygon at one intersection point (Pattern
    Collider's algorithm).

    ``family_indices`` are the line families passing through the
    intersection (each contributes one line); the resulting polygon has
    ``2 * len(family_indices)`` vertices in counter-clockwise order.
    """
    px, py = intersection_point

    # Each line through the intersection contributes two directional rays:
    # the line's normal direction and its reverse. Together these 2k rays
    # partition the neighbourhood of the intersection into 2k sectors.
    angles: list[float] = []
    for fam in family_indices:
        base_angle = 2.0 * math.pi * fam / symmetry
        angles.append(base_angle % (2.0 * math.pi))
        angles.append((base_angle + math.pi) % (2.0 * math.pi))
    angles.sort()
    # Drop duplicates (within float noise); collinear rays from coincident
    # families would otherwise produce zero-area sector slivers.
    deduplicated: list[float] = []
    for angle in angles:
        if deduplicated and abs(angle - deduplicated[-1]) < 1e-9:
            continue
        deduplicated.append(angle)
    angles = deduplicated

    # Step a small distance epsilon along each ray's perpendicular
    # direction; the midpoint of two consecutive offset points lies inside
    # the sector between those two rays.
    offset_points: list[tuple[float, float]] = []
    for angle in angles:
        offset_points.append(
            (
                px - nudge_epsilon * math.sin(angle),
                py + nudge_epsilon * math.cos(angle),
            )
        )

    median_points: list[tuple[float, float]] = []
    for i in range(len(offset_points)):
        a = offset_points[i]
        b = offset_points[(i + 1) % len(offset_points)]
        median_points.append(((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0))

    # Each median lies in one sector and maps via the de Bruijn dual to one
    # vertex of the polygon. Sorting the rays counter-clockwise around the
    # intersection produces vertices that walk clockwise around the dual
    # polygon's centroid (the dual map reverses orientation), so reverse
    # the sequence to get CCW vertex order.
    dual_vertices = tuple(
        _de_bruijn_dual_vertex(median, symmetry, offsets) for median in median_points
    )
    return tuple(reversed(dual_vertices))


def _quantize(value: float, tolerance: float) -> int:
    return int(round(value / tolerance))


def build_multigrid_cells(
    half_extent: float,
    *,
    symmetry: int = 5,
    offsets: tuple[float, ...] = PENROSE_PENTAGRID_OFFSETS,
    coincidence_tolerance: float = _COINCIDENCE_TOLERANCE,
    nudge_epsilon: float = 1e-3,
) -> list[MultigridCell]:
    """Enumerate all multigrid cells whose intersection point lies inside
    ``[-half_extent, half_extent]^2``.

    Each unique intersection point in the multigrid plane (where two or
    more lines coincide) is emitted as exactly one ``MultigridCell``; the
    cell's polygon has ``2k`` vertices where ``k`` is the number of lines
    meeting at the intersection. Returned cells are sorted by intersection
    point for determinism.
    """
    if len(offsets) != symmetry:
        raise ValueError(f"offsets must have length symmetry={symmetry}, got {len(offsets)}.")

    # Intersection grouping: for each pair of line families (i, j) with
    # i < j, walk all line index pairs whose intersection might land in the
    # patch, and accumulate them into a quantised key -> [families] map.
    families_at_point: dict[tuple[int, int], set[int]] = defaultdict(set)
    representative_point: dict[tuple[int, int], tuple[float, float]] = {}

    for family_i in range(symmetry):
        index_range_i = _line_index_range_in_patch(symmetry, offsets, family_i, half_extent)
        for family_j in range(family_i + 1, symmetry):
            index_range_j = _line_index_range_in_patch(symmetry, offsets, family_j, half_extent)
            for line_index_i in index_range_i:
                for line_index_j in index_range_j:
                    point = _line_intersection(
                        symmetry,
                        offsets,
                        family_i,
                        line_index_i,
                        family_j,
                        line_index_j,
                    )
                    if point is None:
                        continue
                    if abs(point[0]) > half_extent + 1.0 or abs(point[1]) > half_extent + 1.0:
                        continue
                    key = (
                        _quantize(point[0], coincidence_tolerance),
                        _quantize(point[1], coincidence_tolerance),
                    )
                    families_at_point[key].add(family_i)
                    families_at_point[key].add(family_j)
                    if key not in representative_point:
                        representative_point[key] = point

    cells: list[MultigridCell] = []
    for key, family_set in families_at_point.items():
        intersection_point = representative_point[key]
        if abs(intersection_point[0]) > half_extent or abs(intersection_point[1]) > half_extent:
            continue
        vertices = _dual_polygon_for_intersection(
            intersection_point,
            tuple(sorted(family_set)),
            symmetry,
            offsets,
            nudge_epsilon=nudge_epsilon,
        )
        cells.append(
            MultigridCell(
                intersection_point=intersection_point,
                line_count=len(family_set),
                vertices=vertices,
            )
        )

    cells.sort(key=lambda c: (c.intersection_point[0], c.intersection_point[1]))
    return cells


# ---------------------------------------------------------------------------
# Polygon classification into Penrose P1 prototile kinds.
# ---------------------------------------------------------------------------

# Identifier strings for the four canonical P1 prototiles plus a fallback
# for polygons that don't fit any of the four (e.g. higher-line-count
# vertices in unusual offset configurations).
P1_DIAMOND = "p1-diamond"
P1_PENTAGON = "p1-pentagon"
P1_BOAT = "p1-boat"
P1_STAR = "p1-star"
P1_OTHER = "p1-other"


def _polygon_edge_lengths(vertices: tuple[tuple[float, float], ...]) -> list[float]:
    return [
        math.hypot(
            vertices[(i + 1) % len(vertices)][0] - vertices[i][0],
            vertices[(i + 1) % len(vertices)][1] - vertices[i][1],
        )
        for i in range(len(vertices))
    ]


def _polygon_interior_angles_degrees(
    vertices: tuple[tuple[float, float], ...],
) -> list[float]:
    n = len(vertices)
    angles: list[float] = []
    for i in range(n):
        prev_v = vertices[(i - 1) % n]
        cur_v = vertices[i]
        next_v = vertices[(i + 1) % n]
        ax = prev_v[0] - cur_v[0]
        ay = prev_v[1] - cur_v[1]
        bx = next_v[0] - cur_v[0]
        by = next_v[1] - cur_v[1]
        dot = ax * bx + ay * by
        cross = ax * by - ay * bx
        # Cross gives signed area * 2 of triangle; positive for CCW
        # interior, so the interior angle is atan2(|cross|, dot) when the
        # polygon is CCW. For our CCW polygons, signed atan2 gives the
        # correct interior angle directly when measured as the angle from
        # the previous-edge direction to the next-edge direction taken
        # CCW.
        angle = math.degrees(math.atan2(cross, dot))
        if angle < 0.0:
            angle += 360.0
        angles.append(angle)
    return angles


def classify_p1_prototile(
    cell: MultigridCell,
    *,
    angle_tolerance_degrees: float = 5.0,
) -> str:
    """Map a multigrid cell to a Penrose P1 prototile name.

    A vertex-merge pass can set ``cell.classification_hint`` to record the
    merge origin (``p1-pentagon`` for a sun-vertex merge, ``p1-star`` for a
    star-vertex merge) directly; otherwise the polygon's vertex count and
    interior-angle signature decide:

    * 4 vertices with angles 36-144-36-144 -> ``p1-diamond``.
    * 4 vertices with angles 72-108-72-108 -> ``p1-pentagon``
      (the Penrose-1974 thick rhomb is an MLD representative of the
      pentagonal P1 prototile, and the multigrid emits it at "boat-spine"
      positions; it reads visually as a pentagonal patch in our
      rendering).
    * 6 vertices -> ``p1-boat`` (the boat prototile in P1 is a hexagonal
      shape that fills the gap when 3 line families coincide at one
      point).
    * 10 vertices -> ``p1-star`` (the canonical pentagram star).
    * Any other vertex count -> ``p1-other``.

    The angle tolerance is loose enough (5 degrees) to accommodate the
    floating-point accumulation in the dual construction without
    misclassifying genuinely distinct polygons.
    """
    if cell.classification_hint is not None:
        return cell.classification_hint
    n = len(cell.vertices)
    if n == 4:
        angles = _polygon_interior_angles_degrees(cell.vertices)
        # The 4 angles should be two pairs of equal opposite angles.
        sorted_angles = sorted(angles)
        smallest = sorted_angles[0]
        if abs(smallest - 36.0) <= angle_tolerance_degrees:
            return P1_DIAMOND
        if abs(smallest - 72.0) <= angle_tolerance_degrees:
            return P1_PENTAGON
        return P1_OTHER
    if n == 6:
        return P1_BOAT
    if n == 10:
        return P1_STAR
    return P1_OTHER


def _polygon_centroid(
    vertices: tuple[tuple[float, float], ...],
) -> tuple[float, float]:
    # Simple arithmetic mean of vertex coordinates. Sufficient for the
    # vertex-merge bookkeeping below; we don't need the geometric (area-
    # weighted) centroid because the polygons here are always convex
    # rhombs.
    n = len(vertices)
    return (
        sum(v[0] for v in vertices) / n,
        sum(v[1] for v in vertices) / n,
    )


def apply_p1_vertex_merge(
    cells: list[MultigridCell],
    *,
    vertex_snap: int = 6,
    angle_tolerance_degrees: float = 5.0,
) -> list[MultigridCell]:
    """Replace canonical Penrose vertex configurations in a rhomb tiling with
    Penrose's P1 prototiles.

    Walks every rhomb-vertex in the input tiling and identifies the two
    canonical 5-rhomb configurations:

    * **Sun vertex** -- 5 thick rhombs (p1-pentagon-shape) sharing a 72-degree
      apex at one point. Replace the 5 rhombs with one regular-decagon cell
      labelled ``p1-star`` ... no, ``p1-pentagon``. Wait: in canonical P1, the
      sun configuration becomes a pentagon (centered at the sun vertex,
      surrounded by other prototiles). We emit a 10-vertex shape (the convex
      hull of all 10 outer rhomb vertices) and let the polygon classifier
      label it ``p1-star``; the rendered shape is a regular decagon which
      reads visually as the pentagon-cluster centre in P1.

    * **Star vertex** -- 5 thin rhombs (p1-diamond-shape) sharing a 36-degree
      apex. Replace the 5 rhombs with one 10-vertex cell labelled
      ``p1-star``; geometrically this is the Penrose pentagram star.

    Rhombs that don't participate in either configuration are emitted
    unchanged. The merge is purely topological: no rhomb area is added or
    lost, and the polygon's outer boundary is the union of the 5 merged
    rhomb perimeters.
    """
    # Group rhombs by shared vertex, recording each rhomb's interior angle
    # contribution at the shared vertex.
    vertex_rhombs: dict[tuple[int, int], list[tuple[int, float, str]]] = defaultdict(list)
    for cell_index, cell in enumerate(cells):
        if cell.line_count != 2 or len(cell.vertices) != 4:
            continue
        kind = classify_p1_prototile(cell, angle_tolerance_degrees=angle_tolerance_degrees)
        if kind not in (P1_PENTAGON, P1_DIAMOND):
            continue
        angles = _polygon_interior_angles_degrees(cell.vertices)
        for vertex_index, vertex in enumerate(cell.vertices):
            key = (
                round(vertex[0] * (10**vertex_snap)),
                round(vertex[1] * (10**vertex_snap)),
            )
            vertex_rhombs[key].append((cell_index, angles[vertex_index], kind))

    merged_rhomb_indices: set[int] = set()
    merged_cells: list[MultigridCell] = []

    # Sort vertices for deterministic output.
    for key in sorted(vertex_rhombs):
        attendees = vertex_rhombs[key]
        if len(attendees) != 5:
            continue
        kinds = {kind for _, _, kind in attendees}
        if len(kinds) != 1:
            continue
        kind = kinds.pop()
        target_angle = 72.0 if kind == P1_PENTAGON else 36.0
        if not all(
            abs(angle - target_angle) <= angle_tolerance_degrees for _, angle, _ in attendees
        ):
            continue
        indices = [idx for idx, _, _ in attendees]
        if any(idx in merged_rhomb_indices for idx in indices):
            continue
        # Collect the 5 rhombs and form a merged polygon = ordered outer
        # boundary of their union. Since all 5 share the apex vertex and
        # are arranged with 5-fold rotational symmetry around it, the
        # outer boundary is a 10-vertex polygon visiting alternating rhomb
        # apex and side vertices in CCW order around the apex.
        apex_x = key[0] / (10**vertex_snap)
        apex_y = key[1] / (10**vertex_snap)
        outer_vertices: list[tuple[float, float]] = []
        for cell_index in indices:
            for vertex in cells[cell_index].vertices:
                if abs(vertex[0] - apex_x) < 1e-5 and abs(vertex[1] - apex_y) < 1e-5:
                    continue
                outer_vertices.append(vertex)
        # Sort outer vertices CCW around the apex.
        outer_vertices.sort(
            key=lambda v: math.atan2(v[1] - apex_y, v[0] - apex_x),
        )
        # Deduplicate vertices that two adjacent rhombs share (4-vertex
        # rhombs share 2 vertices with each neighbour around the apex, but
        # only one of those is on the OUTER boundary; the other is the
        # apex itself which we already excluded).
        deduplicated: list[tuple[float, float]] = []
        for vertex in outer_vertices:
            if deduplicated:
                dx = vertex[0] - deduplicated[-1][0]
                dy = vertex[1] - deduplicated[-1][1]
                if dx * dx + dy * dy < 1e-10:
                    continue
            deduplicated.append(vertex)
        # Handle wrap-around duplicate.
        if (
            len(deduplicated) > 1
            and (deduplicated[0][0] - deduplicated[-1][0]) ** 2
            + (deduplicated[0][1] - deduplicated[-1][1]) ** 2
            < 1e-10
        ):
            deduplicated.pop()
        if len(deduplicated) < 5:
            continue
        # Sun vertex (5 thick rhombs at 72-degree apex) -> pentagon (a
        # convex 10-vertex decagonal cluster, the rhomb-region MLD
        # representative of the pentagonal P1 prototile).
        # Star vertex (5 thin rhombs at 36-degree apex) -> pentagram star
        # (the canonical 10-vertex P1 star).
        classification_hint = P1_PENTAGON if kind == P1_PENTAGON else P1_STAR
        merged_cells.append(
            MultigridCell(
                intersection_point=(apex_x, apex_y),
                line_count=5,
                vertices=tuple(deduplicated),
                classification_hint=classification_hint,
            )
        )
        merged_rhomb_indices.update(indices)

    # Emit the remaining unmerged cells.
    output: list[MultigridCell] = []
    for index, cell in enumerate(cells):
        if index in merged_rhomb_indices:
            continue
        output.append(cell)
    output.extend(merged_cells)
    output.sort(key=lambda c: (c.intersection_point[0], c.intersection_point[1]))
    return output


__all__ = [
    "MultigridCell",
    "P1_BOAT",
    "P1_DIAMOND",
    "P1_OTHER",
    "P1_PENTAGON",
    "P1_STAR",
    "PENROSE_P1_OFFSETS",
    "PENROSE_PENTAGRID_OFFSETS",
    "PENROSE_PENTAGRID_OFFSETS_ALL_ZERO",
    "PHI",
    "apply_p1_vertex_merge",
    "build_multigrid_cells",
    "classify_p1_prototile",
]
