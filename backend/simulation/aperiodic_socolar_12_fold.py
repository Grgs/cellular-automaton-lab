"""Socolar 12-fold dodecagonal rhomb tiling (de Bruijn multigrid).

The Socolar tiling (Socolar, *Simple octagonal and dodecagonal quasicrystals*,
Phys. Rev. B 39, 1989) is a 12-fold quasiperiodic tiling. Its exact marked
substitution rule is published only as a rule diagram, so this module does not
reproduce that substitution. Instead it builds the **dodecagonal rhomb tiling**
-- the rhombus variant of the Socolar tiling, which is mutually locally
derivable from the already-shipped ``shield`` tiling -- via the de Bruijn
generalized-dual (multigrid) construction, the same method the Penrose
multigrid families use (:mod:`backend.simulation.aperiodic_penrose_multigrid`).

Construction: six line families spaced 30 degrees apart (a "dodecagrid":
``symmetry=12`` with six offsets so the families have normals at
``0, 30, ..., 150`` degrees). The de Bruijn dual of that multigrid is a
12-fold rhomb tiling whose tiles are the three dodecagonal rhombi -- the
30-degree (thin) rhombus, the 60-degree (wide) rhombus, and the 90-degree
square. Generic offsets keep the multigrid regular (only two lines cross at any
point), so every cell is a 4-vertex rhombus and the patch is edge-to-edge,
gap-free, and overlap-free. As with the Penrose multigrid families this is a
bounding-box crop: ``patch_depth`` scales the half-extent of the crop rather
than applying a substitution inflation.
"""

from __future__ import annotations

import math

from backend.simulation.aperiodic_family_manifest import (
    SOCOLAR_12_FOLD_RHOMB_30_KIND,
    SOCOLAR_12_FOLD_RHOMB_60_KIND,
    SOCOLAR_12_FOLD_SQUARE_KIND,
    SOCOLAR_12_FOLD_TILE_FAMILY,
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

# A dodecagrid: ``symmetry=12`` makes each family-normal step 30 degrees, and
# six offsets select the six families at 0, 30, ..., 150 degrees (their
# antiparallel partners would be redundant parallel lines).
_DODECAGRID_SYMMETRY = 12

# Six generic, distinct offsets keep the multigrid regular: no three lines are
# concurrent, so every dual cell is a 4-vertex rhombus (no singular star
# vertices). The exact values are arbitrary within that constraint; they only
# fix which finite crop of the (aperiodic) tiling is shown.
_DODECAGRID_OFFSETS: tuple[float, float, float, float, float, float] = (
    0.05,
    0.12,
    0.27,
    0.41,
    0.58,
    0.69,
)

# Depth-0 half-extent and per-depth growth of the crop. Growth is below the
# dodecagonal inflation factor (2 + sqrt(3) ~ 3.732) so the cell count rises at
# a usable pace: ~44 / 108 / 270 / 620 / 1450 cells at depths 0..4.
_BASE_HALF_EXTENT = 1.0
_DEPTH_GROWTH = 1.55

# Rhombus classification tolerance. Edges lie along exact 30-degree directions,
# so the three interior-angle classes (30 / 60 / 90) are well separated; 4
# degrees absorbs floating-point drift without ambiguity.
_ANGLE_TOLERANCE_DEGREES = 4.0

_KIND_PREFIX_BY_KIND = {
    SOCOLAR_12_FOLD_RHOMB_30_KIND: "sr30",
    SOCOLAR_12_FOLD_RHOMB_60_KIND: "sr60",
    SOCOLAR_12_FOLD_SQUARE_KIND: "ssq",
}

_Point = tuple[float, float]


def socolar_12_fold_half_extent(patch_depth: int) -> float:
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
    """Classify a rhombus by its smallest interior angle (30 / 60 / 90)."""
    if len(vertices) != 4:
        return None
    smallest = min(_interior_angles_degrees(vertices))
    if abs(smallest - 30.0) <= _ANGLE_TOLERANCE_DEGREES:
        return SOCOLAR_12_FOLD_RHOMB_30_KIND
    if abs(smallest - 60.0) <= _ANGLE_TOLERANCE_DEGREES:
        return SOCOLAR_12_FOLD_RHOMB_60_KIND
    if abs(smallest - 90.0) <= _ANGLE_TOLERANCE_DEGREES:
        return SOCOLAR_12_FOLD_SQUARE_KIND
    return None


def _orientation_token(vertices: tuple[_Point, ...]) -> str:
    """Stable orientation token from the rhombus's two edge directions.

    Edges lie along the six grid-family directions (multiples of 30 degrees);
    taking each edge direction modulo 180 degrees, snapping to the nearest 30
    degrees, and sorting the distinct values gives a deterministic, bounded
    label that distinguishes rhombus orientations across the 12-fold star.
    """
    directions: set[int] = set()
    count = len(vertices)
    for index in range(count):
        start = vertices[index]
        end = vertices[(index + 1) % count]
        angle = math.degrees(math.atan2(end[1] - start[1], end[0] - start[0])) % 180.0
        directions.add(int(round(angle / 30.0)) * 30 % 180)
    return "-".join(str(value) for value in sorted(directions))


def _cell_id(prefix: str, vertices: tuple[_Point, ...]) -> str:
    centroid = polygon_centroid(tuple(Vec(x, y) for x, y in vertices))
    return f"{prefix}:{encode_float(centroid.x)}:{encode_float(centroid.y)}"


def build_socolar_12_fold_patch(patch_depth: int) -> AperiodicPatch:
    """Build an :class:`AperiodicPatch` for the Socolar dodecagonal rhomb tiling."""
    depth = max(0, int(patch_depth))
    half_extent = socolar_12_fold_half_extent(depth)
    raw_cells = build_multigrid_cells(
        half_extent,
        symmetry=_DODECAGRID_SYMMETRY,
        offsets=_DODECAGRID_OFFSETS,
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
                "tile_family": SOCOLAR_12_FOLD_TILE_FAMILY,
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
