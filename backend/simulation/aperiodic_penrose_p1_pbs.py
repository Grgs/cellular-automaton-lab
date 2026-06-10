"""Centered Penrose P1 pentagon-boat-star patch.

This family uses the singular de Bruijn pentagrid with all-zero offsets, so one
line from each of the five strip families passes through the origin. The dual
cells then form a deterministic, gap-free Penrose P1 representative patch with
the iconic central star and the surrounding boat ring visible from depth 0.

The emitted polygons are the direct multigrid dual cells:

* 4-vertex thin rhombs -> ``p1-diamond``
* 4-vertex thick-rhomb representatives -> ``p1-pentagon``
* 6-vertex singular cells -> ``p1-boat``
* 10-vertex central singular cell -> ``p1-star``

This is a canonical patch / MLD-style Penrose P1 manifestation rather than the
literal decorated six-state substitution from the original rule figure, but it
ships the full P1 prototile vocabulary and validates cleanly under the repo's
shared topology checks.
"""

from __future__ import annotations

import math

from backend.simulation.aperiodic_family_manifest import (
    P1_BOAT_KIND,
    P1_DIAMOND_KIND,
    P1_PENTAGON_KIND,
    P1_STAR_KIND,
    PENROSE_P1_TILE_FAMILY,
)
from backend.simulation.aperiodic_penrose_multigrid import (
    P1_BOAT,
    P1_DIAMOND,
    P1_OTHER,
    P1_PENTAGON,
    P1_STAR,
    PENROSE_PENTAGRID_OFFSETS_ALL_ZERO,
    PHI,
    build_multigrid_cells,
    classify_p1_prototile,
)
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

PENROSE_P1_PBS_BASE_HALF_EXTENT = 1.6

_MULTIGRID_KIND_TO_CELL_KIND = {
    P1_PENTAGON: P1_PENTAGON_KIND,
    P1_DIAMOND: P1_DIAMOND_KIND,
    P1_BOAT: P1_BOAT_KIND,
    P1_STAR: P1_STAR_KIND,
}

_CELL_ID_PREFIX_BY_KIND = {
    P1_PENTAGON_KIND: "ppbs-p",
    P1_DIAMOND_KIND: "ppbs-d",
    P1_BOAT_KIND: "ppbs-b",
    P1_STAR_KIND: "ppbs-s",
}


def penrose_p1_pbs_half_extent(patch_depth: int) -> float:
    return PENROSE_P1_PBS_BASE_HALF_EXTENT * (PHI ** int(patch_depth))


def _cell_id(prefix: str, vertices: tuple[tuple[float, float], ...]) -> str:
    centroid = polygon_centroid(tuple(Vec(x, y) for x, y in vertices))
    return f"{prefix}:{encode_float(centroid.x)}:{encode_float(centroid.y)}"


def build_penrose_p1_pbs_patch(patch_depth: int) -> AperiodicPatch:
    depth = max(0, int(patch_depth))
    half_extent = penrose_p1_pbs_half_extent(depth)
    raw_cells = build_multigrid_cells(
        half_extent,
        offsets=PENROSE_PENTAGRID_OFFSETS_ALL_ZERO,
    )

    records: list[PatchRecord] = []
    for cell in raw_cells:
        kind_token = classify_p1_prototile(cell)
        if kind_token == P1_OTHER:
            continue
        cell_kind = _MULTIGRID_KIND_TO_CELL_KIND[kind_token]
        rounded_vertices = tuple(rounded_point(vertex) for vertex in cell.vertices)
        centroid_vec = polygon_centroid(tuple(Vec(x, y) for x, y in rounded_vertices))
        records.append(
            {
                "id": _cell_id(_CELL_ID_PREFIX_BY_KIND[cell_kind], rounded_vertices),
                "kind": cell_kind,
                "center": rounded_point((centroid_vec.x, centroid_vec.y)),
                "vertices": rounded_vertices,
                "tile_family": PENROSE_P1_TILE_FAMILY,
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
            tile_family=record["tile_family"],
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

    return AperiodicPatch(
        patch_depth=depth,
        width=width,
        height=height,
        cells=cells,
    )
