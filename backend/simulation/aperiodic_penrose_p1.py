"""Penrose P1 (pentagon / star / boat / diamond) tiling.

Built by the de Bruijn multigrid construction in
``aperiodic_penrose_multigrid``. Each P1 cell is the dual polygon of one
intersection point in a 5-fold pentagrid:

* Generic 2-line intersections -> 4-vertex rhomb. Classified into
  ``p1-diamond`` (thin rhomb, 36-144-36-144) or ``p1-pentagon`` (thick
  rhomb, 72-108-72-108) by interior-angle measurement.
* 3-line coincidences -> 6-vertex hexagonal ``p1-boat``.
* The central 5-line coincidence in the all-zero pentagrid -> 10-vertex
  pentagram ``p1-star``.

The pentagrid construction is intrinsically gap-free at every patch radius
and naturally produces all four canonical P1 prototiles, so the previous
substitution-based draft (with its visible boundary half-tiles, T-vertex
artefacts, and missing star / boat prototiles) is fully superseded.

The patch is a square of half-extent ``1.6 * phi^d`` at depth ``d``. The
half-extent at depth 0 is chosen to capture the central pentagram star
plus its immediate surrounding ring of pentagons + boats; subsequent
depths inflate the patch to expose more of the (infinite) tiling.
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
    P1_PENTAGON,
    P1_STAR,
    PENROSE_P1_OFFSETS,
    PHI,
    apply_p1_vertex_merge,
    build_multigrid_cells,
    classify_p1_prototile,
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


# Depth-0 half-extent: large enough to capture the central pentagram star
# plus the first ring of surrounding pentagons + boats, but small enough
# that depth 0 isn't an enormous patch. Subsequent depths scale by phi
# per round (so depth 4 covers the same area as depth 0 at four levels of
# zoom-out, matching the natural quasiperiodic scale hierarchy).
PENROSE_P1_BASE_HALF_EXTENT = 1.6


_MULTIGRID_KIND_TO_CELL_KIND = {
    P1_PENTAGON: P1_PENTAGON_KIND,
    P1_DIAMOND: P1_DIAMOND_KIND,
    P1_BOAT: P1_BOAT_KIND,
    P1_STAR: P1_STAR_KIND,
}


def penrose_p1_half_extent(patch_depth: int) -> float:
    return PENROSE_P1_BASE_HALF_EXTENT * (PHI ** int(patch_depth))


def _cell_id(prefix: str, vertices: tuple[tuple[float, float], ...]) -> str:
    centroid = polygon_centroid(tuple(Vec(x, y) for x, y in vertices))
    return f"{prefix}:{encode_float(centroid.x)}:{encode_float(centroid.y)}"


_CELL_ID_PREFIX_BY_KIND = {
    P1_PENTAGON_KIND: "pp",
    P1_DIAMOND_KIND: "pd",
    P1_BOAT_KIND: "pb",
    P1_STAR_KIND: "ps",
}


def build_penrose_p1_patch(patch_depth: int) -> AperiodicPatch:
    depth = max(0, int(patch_depth))
    half_extent = penrose_p1_half_extent(depth)
    raw_cells = build_multigrid_cells(half_extent, offsets=PENROSE_P1_OFFSETS)
    # Promote 5-rhomb sun and star vertex configurations to canonical P1
    # pentagon and pentagram cells. With ``PENROSE_P1_OFFSETS`` the raw
    # multigrid output is a regular Penrose P3 rhomb tiling (no central
    # singularity, with sun and star vertices scattered throughout); the
    # vertex-merge pass collapses each of those vertex configurations into
    # a single P1 prototile cell.
    cells = apply_p1_vertex_merge(raw_cells)

    records: list[dict] = []
    for cell in cells:
        kind_token = classify_p1_prototile(cell)
        cell_kind = _MULTIGRID_KIND_TO_CELL_KIND.get(kind_token)
        if cell_kind is None:
            # Polygon doesn't match any of the four P1 prototiles (e.g.
            # non-canonical 8- or 12-vertex shapes from unusual offset
            # choices). Skip rather than emit an unrecognized cell kind.
            continue
        prefix = _CELL_ID_PREFIX_BY_KIND[cell_kind]
        rounded_vertices = tuple(rounded_point(v) for v in cell.vertices)
        centroid_vec = polygon_centroid(tuple(Vec(x, y) for x, y in rounded_vertices))
        records.append(
            {
                "id": _cell_id(prefix, rounded_vertices),
                "kind": cell_kind,
                "center": rounded_point((centroid_vec.x, centroid_vec.y)),
                "vertices": rounded_vertices,
                "tile_family": PENROSE_P1_TILE_FAMILY,
            }
        )

    neighbors_by_id = build_edge_neighbors(records, neighbor_mode="full_edge")
    cells_tuple = tuple(
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

    if cells_tuple:
        all_x = [vertex[0] for cell in cells_tuple for vertex in cell.vertices]
        all_y = [vertex[1] for cell in cells_tuple for vertex in cell.vertices]
        width = max(1, int(math.ceil(max(all_x) - min(all_x))))
        height = max(1, int(math.ceil(max(all_y) - min(all_y))))
    else:
        width = 1
        height = 1

    return AperiodicPatch(
        patch_depth=depth,
        width=width,
        height=height,
        cells=cells_tuple,
    )
