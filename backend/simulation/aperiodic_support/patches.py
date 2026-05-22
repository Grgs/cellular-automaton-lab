"""High-level patch constructors that combine records, neighbours, and metadata
into ``AperiodicPatch`` values.
"""

from __future__ import annotations

from typing import Iterable

from .geometry import compatibility_extent, polygon_centroid, rounded_point
from .neighbors import build_edge_neighbors, build_exact_neighbors
from .types import (
    COORDINATE_PRECISION,
    AperiodicPatch,
    AperiodicPatchCell,
    ExactNeighborMode,
    ExactPatchRecord,
    NeighborMode,
    PatchRecord,
    Vec,
)


def patch_from_records(
    patch_depth: int,
    records: list[PatchRecord],
    *,
    edge_precision: int = COORDINATE_PRECISION,
    neighbor_mode: NeighborMode = "full_edge",
) -> AperiodicPatch:
    neighbors_by_id = build_edge_neighbors(
        records,
        edge_precision=edge_precision,
        neighbor_mode=neighbor_mode,
    )
    cells = tuple(
        AperiodicPatchCell(
            id=record["id"],
            kind=record["kind"],
            center=record["center"],
            vertices=record["vertices"],
            neighbors=neighbors_by_id[record["id"]],
            tile_family=record.get("tile_family"),
            orientation_token=record.get("orientation_token"),
            chirality_token=record.get("chirality_token"),
            decoration_tokens=record.get("decoration_tokens"),
        )
        for record in sorted(records, key=lambda item: item["id"])
    )
    all_x = [vertex[0] for cell in cells for vertex in cell.vertices]
    all_y = [vertex[1] for cell in cells for vertex in cell.vertices]
    return AperiodicPatch(
        patch_depth=int(patch_depth),
        width=compatibility_extent(all_x),
        height=compatibility_extent(all_y),
        cells=cells,
    )


def patch_from_exact_records(
    patch_depth: int,
    records: list[ExactPatchRecord],
    *,
    float_scale: float = 1.0,
    vertex_precision: int | None = COORDINATE_PRECISION,
    neighbor_mode: ExactNeighborMode = "full_edge",
) -> AperiodicPatch:
    neighbors_by_id = build_exact_neighbors(records, neighbor_mode=neighbor_mode)

    float_records: list[PatchRecord] = []
    for record in records:
        raw_vertices = tuple(
            (
                float(vertex[0]) * float_scale,
                float(vertex[1]) * float_scale,
            )
            for vertex in record["vertices"]
        )
        if vertex_precision is None:
            float_vertices = raw_vertices
        else:
            float_vertices = tuple(
                (
                    round(vertex[0], vertex_precision),
                    round(vertex[1], vertex_precision),
                )
                for vertex in raw_vertices
            )
        centroid = polygon_centroid(tuple(Vec(vertex[0], vertex[1]) for vertex in float_vertices))
        float_records.append(
            {
                "id": record["id"],
                "kind": record["kind"],
                "center": rounded_point(centroid),
                "vertices": float_vertices,
                "tile_family": record.get("tile_family"),
                "orientation_token": record.get("orientation_token"),
                "chirality_token": record.get("chirality_token"),
                "decoration_tokens": record.get("decoration_tokens"),
            }
        )

    cells = tuple(
        AperiodicPatchCell(
            id=record["id"],
            kind=record["kind"],
            center=record["center"],
            vertices=record["vertices"],
            neighbors=neighbors_by_id[record["id"]],
            tile_family=record.get("tile_family"),
            orientation_token=record.get("orientation_token"),
            chirality_token=record.get("chirality_token"),
            decoration_tokens=record.get("decoration_tokens"),
        )
        for record in sorted(float_records, key=lambda item: item["id"])
    )
    all_x = [vertex[0] for cell in cells for vertex in cell.vertices]
    all_y = [vertex[1] for cell in cells for vertex in cell.vertices]
    return AperiodicPatch(
        patch_depth=int(patch_depth),
        width=compatibility_extent(all_x),
        height=compatibility_extent(all_y),
        cells=cells,
    )


def patch_from_cells(
    patch_depth: int,
    cells: Iterable[AperiodicPatchCell],
) -> AperiodicPatch:
    resolved_cells = tuple(cells)
    all_x = [vertex[0] for cell in resolved_cells for vertex in cell.vertices]
    all_y = [vertex[1] for cell in resolved_cells for vertex in cell.vertices]
    return AperiodicPatch(
        patch_depth=int(patch_depth),
        width=compatibility_extent(all_x),
        height=compatibility_extent(all_y),
        cells=resolved_cells,
    )
