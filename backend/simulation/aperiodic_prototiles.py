from __future__ import annotations

from backend.simulation.aperiodic_registry import build_registered_aperiodic_patch
from backend.simulation.aperiodic_support import AperiodicPatch, AperiodicPatchCell
from backend.simulation.penrose import (
    PENROSE_EDGE_ADJACENCY,
    PENROSE_VERTEX_ADJACENCY,
    build_penrose_patch,
)
from backend.simulation.topology_catalog import (
    PENROSE_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
)


def _build_penrose_patch_as_aperiodic(geometry: str, patch_depth: int) -> AperiodicPatch:
    penrose_patch = build_penrose_patch(
        patch_depth,
        adjacency_mode=(
            PENROSE_VERTEX_ADJACENCY if geometry == PENROSE_VERTEX_GEOMETRY else PENROSE_EDGE_ADJACENCY
        ),
    )
    return AperiodicPatch(
        patch_depth=penrose_patch.patch_depth,
        width=penrose_patch.width,
        height=penrose_patch.height,
        cells=tuple(
            AperiodicPatchCell(
                id=cell.id,
                kind=cell.kind,
                center=cell.center,
                vertices=cell.vertices,
                neighbors=cell.neighbors,
            )
            for cell in penrose_patch.cells
        ),
    )


def build_aperiodic_patch(geometry: str, patch_depth: int) -> AperiodicPatch:
    if geometry in {PENROSE_GEOMETRY, PENROSE_VERTEX_GEOMETRY}:
        return _build_penrose_patch_as_aperiodic(geometry, patch_depth)
    return build_registered_aperiodic_patch(geometry, patch_depth)


__all__ = [
    "AperiodicPatch",
    "AperiodicPatchCell",
    "build_aperiodic_patch",
]
