from __future__ import annotations

from backend.simulation.aperiodic_prototiles import build_aperiodic_patch
from backend.simulation.periodic_face_tilings import build_periodic_face_cells
from backend.simulation.topology_types import LatticeCell


def build_aperiodic_topology_cells(
    geometry: str,
    patch_depth: int,
) -> tuple[int, int, int, tuple[LatticeCell, ...]]:
    patch = build_aperiodic_patch(geometry, patch_depth)
    cells = tuple(
        LatticeCell(
            id=cell.id,
            kind=cell.kind,
            neighbors=cell.neighbors,
            center=cell.center,
            vertices=cell.vertices,
            tile_family=cell.tile_family,
            orientation_token=cell.orientation_token,
            chirality_token=cell.chirality_token,
            decoration_tokens=cell.decoration_tokens,
        )
        for cell in patch.cells
    )
    return patch.width, patch.height, patch.patch_depth, cells


def build_periodic_face_topology_cells(
    geometry: str,
    width: int,
    height: int,
) -> tuple[LatticeCell, ...]:
    return tuple(
        LatticeCell(
            id=cell.id,
            kind=cell.kind,
            neighbors=cell.neighbors,
            slot=cell.slot,
            center=cell.center,
            vertices=cell.vertices,
        )
        for cell in build_periodic_face_cells(geometry, width, height)
    )
