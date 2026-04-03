from __future__ import annotations

from backend.simulation.aperiodic_support import (
    PatchRecord,
    Vec,
    polygon_centroid,
    rounded_point,
)


ROBINSON_THICK_KIND = "robinson-thick"
ROBINSON_THIN_KIND = "robinson-thin"


def split_penrose_p2_cell_to_robinson_records(
    *,
    cell_id: str,
    kind: str,
    vertices: tuple[tuple[float, float], ...],
) -> tuple[PatchRecord, PatchRecord]:
    if len(vertices) != 4:
        raise ValueError("Penrose P2 cells must have four vertices.")

    triangle_kind = ROBINSON_THICK_KIND if kind == "kite" else ROBINSON_THIN_KIND
    triangles = (
        (vertices[0], vertices[1], vertices[2]),
        (vertices[0], vertices[2], vertices[3]),
    )

    records: list[PatchRecord] = []
    for index, triangle in enumerate(triangles):
        triangle_vertices = tuple(rounded_point(vertex) for vertex in triangle)
        centroid = polygon_centroid(tuple(Vec(x, y) for x, y in triangle_vertices))
        records.append(
            {
                "id": f"{cell_id}:{index}",
                "kind": triangle_kind,
                "center": rounded_point(centroid),
                "vertices": triangle_vertices,
            }
        )
    return records[0], records[1]
