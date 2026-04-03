from __future__ import annotations

from backend.simulation.aperiodic_golden_triangles import (
    TUEBINGEN_THICK_KIND,
    TUEBINGEN_THIN_KIND,
    triangle_orientation_token,
    triangle_record,
)
from backend.simulation.aperiodic_penrose_p2 import build_penrose_p2_patch
from backend.simulation.aperiodic_support import AperiodicPatch, PatchRecord, patch_from_records


def build_tuebingen_triangle_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = int(patch_depth)
    penrose_patch = build_penrose_p2_patch(resolved_depth)
    records: list[PatchRecord] = []
    for cell in penrose_patch.cells:
        if len(cell.vertices) != 4:
            continue
        triangle_kind = TUEBINGEN_THICK_KIND if cell.kind == "kite" else TUEBINGEN_THIN_KIND
        triangles = (
            (cell.vertices[0], cell.vertices[1], cell.vertices[2]),
            (cell.vertices[0], cell.vertices[2], cell.vertices[3]),
        )
        for index, triangle in enumerate(triangles):
            orientation_token = triangle_orientation_token(triangle)
            records.append(
                triangle_record(
                    cell_id=f"tuebingen:{cell.id}:{index}",
                    kind=triangle_kind,
                    vertices=triangle,
                    tile_family="tuebingen",
                    orientation_token=orientation_token,
                    chirality_token="left" if index == 0 else "right",
                )
            )
    return patch_from_records(resolved_depth, records)
