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
    """

    intersection_point: tuple[float, float]
    line_count: int
    vertices: tuple[tuple[float, float], ...]


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

    Classification by vertex count and interior-angle signature:

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


__all__ = [
    "MultigridCell",
    "P1_BOAT",
    "P1_DIAMOND",
    "P1_OTHER",
    "P1_PENTAGON",
    "P1_STAR",
    "PENROSE_PENTAGRID_OFFSETS",
    "PENROSE_PENTAGRID_OFFSETS_ALL_ZERO",
    "PHI",
    "build_multigrid_cells",
    "classify_p1_prototile",
]
