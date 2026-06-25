"""Hendecagonal 11-fold rhomb tiling (de Bruijn multigrid).

This module builds the **11-fold rhomb tiling** -- the hendecagonal analogue of
the Penrose (5-fold), heptagonal (7-fold), enneagonal (9-fold), and Socolar
(12-fold) rhomb tilings -- via the de Bruijn generalized-dual (multigrid)
construction, the same method the Penrose multigrid families use
(:mod:`backend.simulation.aperiodic_penrose_multigrid`).

Construction: eleven line families spaced ``2*pi/11`` apart (a "hendecagrid":
``symmetry=11`` with eleven offsets so the families have normals at
``0, 2*pi/11, ..., 20*pi/11``). Eleven is prime, so -- unlike an even-symmetry
grid where antiparallel families ``i`` and ``i + N/2`` would be redundant, and
unlike 9-fold where families 0/3/6 share a 120-degree sub-symmetry -- all
eleven families are fully independent and used directly. The de Bruijn dual of
that multigrid is an 11-fold rhomb tiling whose tiles are the five hendecagonal
rhombi with acute angles ``k * 180/11`` degrees for ``k = 1..5`` (~16.4, ~32.7,
~49.1, ~65.5, ~81.8 degrees). Generic offsets keep the multigrid regular (only
two lines cross at any point), so every cell is a 4-vertex rhombus and the patch
is edge-to-edge, gap-free, and overlap-free. As with the Penrose multigrid
families this is a bounding-box crop: ``patch_depth`` scales the half-extent of
the crop rather than applying a substitution inflation.

This is the de Bruijn hendecagrid rhombus tiling. It is *not* a marked-prototile
substitution tiling; see ``docs/TILING_KNOWN_DEVIATIONS.md``.
"""

from __future__ import annotations

import math

from backend.simulation.aperiodic_family_manifest import (
    HENDECAGONAL_11_FOLD_RHOMB_1_KIND,
    HENDECAGONAL_11_FOLD_RHOMB_2_KIND,
    HENDECAGONAL_11_FOLD_RHOMB_3_KIND,
    HENDECAGONAL_11_FOLD_RHOMB_4_KIND,
    HENDECAGONAL_11_FOLD_RHOMB_5_KIND,
    HENDECAGONAL_11_FOLD_TILE_FAMILY,
)
from backend.simulation.aperiodic_penrose_multigrid import build_multigrid_cells
from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    AperiodicPatchCell,
    PatchRecord,
    Vec,
    build_edge_neighbors,
    encode_float,
    polygon_centroid,
    rounded_point,
)

# A hendecagrid: ``symmetry=11`` makes each family-normal step 2*pi/11, and
# eleven offsets select the eleven families. Because 11 is prime there are no
# antiparallel partners to drop and no sub-symmetry concurrences, so all eleven
# families are used directly.
_HENDECAGRID_SYMMETRY = 11

# Eleven generic, distinct offsets keep the multigrid regular: no three lines
# are concurrent, so every dual cell is a 4-vertex rhombus (no singular star
# vertices). Their sum is non-integer, which also avoids a singular vertex at
# the origin. The exact values are arbitrary within those constraints; they only
# fix which finite crop of the (aperiodic) tiling is shown.
_HENDECAGRID_OFFSETS: tuple[
    float, float, float, float, float, float, float, float, float, float, float
] = (
    0.04,
    0.12,
    0.19,
    0.27,
    0.36,
    0.44,
    0.53,
    0.61,
    0.68,
    0.77,
    0.86,
)

# Depth-0 half-extent and per-depth growth of the crop. Growth is tuned to a
# usable cell-count pace: ~57/127/268/634 cells at depths 0..3.
_BASE_HALF_EXTENT = 0.6
_DEPTH_GROWTH = 1.5

# The shared multigrid builder samples each intersection's sectors by stepping a
# small perpendicular nudge off every ray. The default 1e-3 is too coarse for
# the dense 11-fold star (consecutive family normals are only ~16.4 degrees
# apart), where the narrow thin-rhombus sectors can otherwise receive a nudge
# that lands in the wrong sector and yields a malformed (non-equilateral)
# quadrilateral. 1e-5 is comfortably inside every sector while staying well
# above float-cancellation noise, so every emitted cell is a true unit rhombus.
_NUDGE_EPSILON = 1e-5

# The acute interior angle of the k-th hendecagonal rhombus is k * 180/11
# degrees for k in {1, 2, 3, 4, 5}; the five classes are ~16.4 / ~32.7 / ~49.1 /
# ~65.5 / ~81.8 deg, spaced ~16.4 deg apart, so 4 degrees of tolerance absorbs
# float drift without ambiguity.
_HENDECAGON_ANGLE_STEP_DEGREES = 180.0 / 11.0
_ANGLE_TOLERANCE_DEGREES = 4.0

_KIND_BY_ANGLE_INDEX = {
    1: HENDECAGONAL_11_FOLD_RHOMB_1_KIND,
    2: HENDECAGONAL_11_FOLD_RHOMB_2_KIND,
    3: HENDECAGONAL_11_FOLD_RHOMB_3_KIND,
    4: HENDECAGONAL_11_FOLD_RHOMB_4_KIND,
    5: HENDECAGONAL_11_FOLD_RHOMB_5_KIND,
}
_KIND_PREFIX_BY_KIND = {
    HENDECAGONAL_11_FOLD_RHOMB_1_KIND: "h11r1",
    HENDECAGONAL_11_FOLD_RHOMB_2_KIND: "h11r2",
    HENDECAGONAL_11_FOLD_RHOMB_3_KIND: "h11r3",
    HENDECAGONAL_11_FOLD_RHOMB_4_KIND: "h11r4",
    HENDECAGONAL_11_FOLD_RHOMB_5_KIND: "h11r5",
}

_Point = tuple[float, float]


def hendecagonal_11_fold_half_extent(patch_depth: int) -> float:
    return _BASE_HALF_EXTENT * (_DEPTH_GROWTH ** max(0, int(patch_depth)))


def _interior_angles_degrees(vertices: tuple[_Point, ...]) -> list[float]:
    count = len(vertices)
    angles: list[float] = []
    for index in range(count):
        previous = vertices[(index - 1) % count]
        current = vertices[index]
        following = vertices[(index + 1) % count]
        ax, ay = previous[0] - current[0], previous[1] - current[1]
        bx, by = following[0] - current[0], following[1] - current[1]
        dot = ax * bx + ay * by
        magnitude = math.hypot(ax, ay) * math.hypot(bx, by)
        if magnitude == 0.0:
            angles.append(0.0)
            continue
        angles.append(math.degrees(math.acos(max(-1.0, min(1.0, dot / magnitude)))))
    return angles


def _rhomb_kind(vertices: tuple[_Point, ...]) -> str | None:
    """Classify a hendecagonal rhombus by its acute (smallest) interior angle.

    The acute angle is ``k * 180/11`` degrees for ``k`` in {1, 2, 3, 4, 5};
    round the measured angle to the nearest such multiple and map it to the
    corresponding rhomb-k kind, rejecting anything that is not within tolerance
    of one of the five valid classes.
    """
    if len(vertices) != 4:
        return None
    smallest = min(_interior_angles_degrees(vertices))
    index = round(smallest / _HENDECAGON_ANGLE_STEP_DEGREES)
    if index not in _KIND_BY_ANGLE_INDEX:
        return None
    if abs(smallest - index * _HENDECAGON_ANGLE_STEP_DEGREES) > _ANGLE_TOLERANCE_DEGREES:
        return None
    return _KIND_BY_ANGLE_INDEX[index]


def _orientation_token(vertices: tuple[_Point, ...]) -> str:
    """Stable orientation token from the rhombus's two edge directions.

    Edges lie along the eleven grid-family directions (multiples of 180/11
    degrees). Taking each edge direction modulo 180 degrees and snapping to the
    nearest 180/11-degree bucket, then sorting the distinct values, gives a
    deterministic, bounded label that distinguishes rhombus orientations across
    the 11-fold star.
    """
    bucket = 180.0 / 11.0
    directions: set[int] = set()
    count = len(vertices)
    for index in range(count):
        start = vertices[index]
        end = vertices[(index + 1) % count]
        angle = math.degrees(math.atan2(end[1] - start[1], end[0] - start[0])) % 180.0
        directions.add(int(round(angle / bucket)) % 11)
    return "-".join(str(value) for value in sorted(directions))


def _cell_id(prefix: str, vertices: tuple[_Point, ...]) -> str:
    centroid = polygon_centroid(tuple(Vec(x, y) for x, y in vertices))
    return f"{prefix}:{encode_float(centroid.x)}:{encode_float(centroid.y)}"


def build_hendecagonal_11_fold_patch(patch_depth: int) -> AperiodicPatch:
    """Build an :class:`AperiodicPatch` for the 11-fold hendecagonal rhomb tiling."""
    depth = max(0, int(patch_depth))
    half_extent = hendecagonal_11_fold_half_extent(depth)
    raw_cells = build_multigrid_cells(
        half_extent,
        symmetry=_HENDECAGRID_SYMMETRY,
        offsets=_HENDECAGRID_OFFSETS,
        nudge_epsilon=_NUDGE_EPSILON,
    )

    records: list[PatchRecord] = []
    for cell in raw_cells:
        kind = _rhomb_kind(cell.vertices)
        if kind is None:
            # With generic offsets the multigrid is regular (rhombi only); guard
            # against any degenerate sliver from float drift rather than emit an
            # unrecognized cell.
            continue
        rounded_vertices = tuple(rounded_point(vertex) for vertex in cell.vertices)
        centroid = polygon_centroid(tuple(Vec(x, y) for x, y in rounded_vertices))
        records.append(
            {
                "id": _cell_id(_KIND_PREFIX_BY_KIND[kind], rounded_vertices),
                "kind": kind,
                "center": rounded_point((centroid.x, centroid.y)),
                "vertices": rounded_vertices,
                "tile_family": HENDECAGONAL_11_FOLD_TILE_FAMILY,
                "orientation_token": _orientation_token(rounded_vertices),
            }
        )

    neighbors_by_id = build_edge_neighbors(records, neighbor_mode="full_edge")
    cells = tuple(
        AperiodicPatchCell(
            id=record["id"],
            kind=record["kind"],
            center=record["center"],
            vertices=record["vertices"],
            neighbors=neighbors_by_id[record["id"]],
            tile_family=record.get("tile_family"),
            orientation_token=record.get("orientation_token"),
        )
        for record in sorted(records, key=lambda item: item["id"])
    )

    if cells:
        all_x = [vertex[0] for cell in cells for vertex in cell.vertices]
        all_y = [vertex[1] for cell in cells for vertex in cell.vertices]
        width = max(1, int(math.ceil(max(all_x) - min(all_x))))
        height = max(1, int(math.ceil(max(all_y) - min(all_y))))
    else:
        width = 1
        height = 1

    return AperiodicPatch(patch_depth=depth, width=width, height=height, cells=cells)
