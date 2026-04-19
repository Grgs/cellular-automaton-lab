from __future__ import annotations

from backend.simulation.aperiodic_prototiles import build_aperiodic_patch
from backend.simulation.periodic_face_tilings import build_periodic_face_cells
from backend.simulation.aperiodic_support import AperiodicPatch
from backend.simulation.topology_types import LatticeCell, LatticeTopology, topology_revision


def topology_from_aperiodic_patch(
    geometry: str,
    patch: AperiodicPatch,
    *,
    topology_revision_value: str | None = None,
) -> LatticeTopology:
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
    return LatticeTopology(
        geometry=geometry,
        width=patch.width,
        height=patch.height,
        cells=cells,
        topology_revision=(
            topology_revision_value
            if topology_revision_value is not None
            else topology_revision(geometry, patch.width, patch.height, patch.patch_depth)
        ),
        patch_depth=patch.patch_depth,
    )


def build_aperiodic_topology_cells(
    geometry: str,
    patch_depth: int,
) -> tuple[int, int, int, tuple[LatticeCell, ...]]:
    patch = build_aperiodic_patch(geometry, patch_depth)
    topology = topology_from_aperiodic_patch(geometry, patch)
    return topology.width, topology.height, topology.patch_depth or 0, topology.cells


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
