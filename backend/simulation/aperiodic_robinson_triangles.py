from __future__ import annotations

from backend.simulation.aperiodic_golden_triangles import (
    split_penrose_p2_cell_to_robinson_records,
)
from backend.simulation.aperiodic_penrose_p2 import build_penrose_p2_patch
from backend.simulation.aperiodic_support import AperiodicPatch, PatchRecord, patch_from_records


def build_robinson_triangles_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = int(patch_depth)
    penrose_patch = build_penrose_p2_patch(resolved_depth)
    records: list[PatchRecord] = []
    for cell in penrose_patch.cells:
        records.extend(
            split_penrose_p2_cell_to_robinson_records(
                cell_id=cell.id,
                kind=cell.kind,
                vertices=cell.vertices,
            )
        )
    return patch_from_records(resolved_depth, records)
