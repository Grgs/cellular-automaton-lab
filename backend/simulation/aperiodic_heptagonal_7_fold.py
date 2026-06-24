"""Heptagonal 7-fold rhomb tiling (de Bruijn multigrid).

This module builds the **7-fold rhomb tiling** -- the heptagonal analogue of
the Penrose (5-fold) and Socolar (12-fold) rhomb tilings -- via the de Bruijn
generalized-dual (multigrid) construction, the same method the Penrose
multigrid families use (:mod:`backend.simulation.aperiodic_penrose_multigrid`).

Construction: seven line families spaced ``2*pi/7`` apart (a "heptagrid":
``symmetry=7`` with seven offsets so the families have normals at
``0, 2*pi/7, ..., 12*pi/7``). Seven is odd, so -- unlike an even-symmetry grid
where antiparallel families ``i`` and ``i + N/2`` would be redundant -- all
seven families are distinct and used directly. The de Bruijn dual of that
multigrid is a 7-fold rhomb tiling whose tiles are the three heptagonal rhombi:
the thin rhombus (acute angle ``pi/7 ~ 25.7 deg``), the medium rhombus
(``2*pi/7 ~ 51.4 deg``), and the wide rhombus (``3*pi/7 ~ 77.1 deg``). Generic
offsets keep the multigrid regular (only two lines cross at any point), so
every cell is a 4-vertex rhombus and the patch is edge-to-edge, gap-free, and
overlap-free. As with the Penrose multigrid families this is a bounding-box
crop: ``patch_depth`` scales the half-extent of the crop rather than applying a
substitution inflation.

This is the de Bruijn heptagrid rhombus tiling. It is *not* the
Goodman-Strauss 7-fold tiling, which is a different (marked-prototile,
substitution) construction; see ``docs/TILING_KNOWN_DEVIATIONS.md``.
"""

from __future__ import annotations

import math

from backend.simulation.aperiodic_family_manifest import (
    HEPTAGONAL_7_FOLD_MEDIUM_KIND,
    HEPTAGONAL_7_FOLD_THIN_KIND,
    HEPTAGONAL_7_FOLD_TILE_FAMILY,
    HEPTAGONAL_7_FOLD_WIDE_KIND,
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

# A heptagrid: ``symmetry=7`` makes each family-normal step 2*pi/7, and seven
# offsets select the seven families at 0, 2*pi/7, ..., 12*pi/7. Because 7 is
# odd there are no antiparallel partners to drop, so all seven families are
# used directly.
_HEPTAGRID_SYMMETRY = 7

# Seven generic, distinct offsets keep the multigrid regular: no three lines
# are concurrent, so every dual cell is a 4-vertex rhombus (no singular star
# vertices). Their sum is non-integer, which also avoids a singular vertex at
# the origin. The exact values are arbitrary within those constraints; they
# only fix which finite crop of the (aperiodic) tiling is shown.
_HEPTAGRID_OFFSETS: tuple[float, float, float, float, float, float, float] = (
    0.05,
    0.13,
    0.24,
    0.38,
    0.51,
    0.63,
    0.79,
)

# Depth-0 half-extent and per-depth growth of the crop. Growth is tuned to a
# usable cell-count pace.
_BASE_HALF_EXTENT = 1.0
_DEPTH_GROWTH = 1.5

# The shared multigrid builder samples each intersection's sectors by stepping a
# small perpendicular nudge off every ray. The default 1e-3 is too coarse for
# the 7-fold star: consecutive family normals are only ~25.7 degrees apart, so
# the thin-rhombus sectors are narrow enough that a 1e-3 nudge lands in the
# wrong sector for a few intersections and yields a malformed (non-equilateral)
# quadrilateral. 1e-5 is comfortably inside every sector while staying well
# above float-cancellation noise, so every emitted cell is a true unit rhombus.
_NUDGE_EPSILON = 1e-5

# The acute interior angle of the k-th heptagonal rhombus is k * 180/7 degrees
# for k in {1, 2, 3}; the three classes are ~25.7 / ~51.4 / ~77.1 deg, spaced
# ~25.7 deg apart, so 4 degrees of tolerance absorbs float drift without
# ambiguity.
_HEPTAGON_ANGLE_STEP_DEGREES = 180.0 / 7.0
_ANGLE_TOLERANCE_DEGREES = 4.0

_KIND_BY_ANGLE_INDEX = {
    1: HEPTAGONAL_7_FOLD_THIN_KIND,
    2: HEPTAGONAL_7_FOLD_MEDIUM_KIND,
    3: HEPTAGONAL_7_FOLD_WIDE_KIND,
}
_KIND_PREFIX_BY_KIND = {
    HEPTAGONAL_7_FOLD_THIN_KIND: "h7thin",
    HEPTAGONAL_7_FOLD_MEDIUM_KIND: "h7med",
    HEPTAGONAL_7_FOLD_WIDE_KIND: "h7wide",
}

_Point = tuple[float, float]


def heptagonal_7_fold_half_extent(patch_depth: int) -> float:
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
    """Classify a heptagonal rhombus by its acute (smallest) interior angle.

    The acute angle is ``k * 180/7`` degrees for ``k`` in {1, 2, 3}; round the
    measured angle to the nearest such multiple and map it to the thin / medium
    / wide kind, rejecting anything that is not within tolerance of one of the
    three valid classes.
    """
    if len(vertices) != 4:
        return None
    smallest = min(_interior_angles_degrees(vertices))
    index = round(smallest / _HEPTAGON_ANGLE_STEP_DEGREES)
    if index not in _KIND_BY_ANGLE_INDEX:
        return None
    if abs(smallest - index * _HEPTAGON_ANGLE_STEP_DEGREES) > _ANGLE_TOLERANCE_DEGREES:
        return None
    return _KIND_BY_ANGLE_INDEX[index]


def _orientation_token(vertices: tuple[_Point, ...]) -> str:
    """Stable orientation token from the rhombus's two edge directions.

    Edges lie along the seven grid-family directions. Taking each edge
    direction modulo 180 degrees and snapping to the nearest 180/14-degree
    bucket (fine enough to separate the seven-fold star, which steps by
    180/7 degrees) gives a deterministic, bounded label that distinguishes
    rhombus orientations across the 7-fold star.
    """
    bucket = 180.0 / 14.0
    directions: set[int] = set()
    count = len(vertices)
    for index in range(count):
        start = vertices[index]
        end = vertices[(index + 1) % count]
        angle = math.degrees(math.atan2(end[1] - start[1], end[0] - start[0])) % 180.0
        directions.add(int(round(angle / bucket)) % 14)
    return "-".join(str(value) for value in sorted(directions))


def _cell_id(prefix: str, vertices: tuple[_Point, ...]) -> str:
    centroid = polygon_centroid(tuple(Vec(x, y) for x, y in vertices))
    return f"{prefix}:{encode_float(centroid.x)}:{encode_float(centroid.y)}"


def build_heptagonal_7_fold_patch(patch_depth: int) -> AperiodicPatch:
    """Build an :class:`AperiodicPatch` for the 7-fold heptagonal rhomb tiling."""
    depth = max(0, int(patch_depth))
    half_extent = heptagonal_7_fold_half_extent(depth)
    raw_cells = build_multigrid_cells(
        half_extent,
        symmetry=_HEPTAGRID_SYMMETRY,
        offsets=_HEPTAGRID_OFFSETS,
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
                "tile_family": HEPTAGONAL_7_FOLD_TILE_FAMILY,
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
