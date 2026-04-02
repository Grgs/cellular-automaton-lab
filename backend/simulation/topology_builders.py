from __future__ import annotations

from functools import lru_cache
from typing import Iterable

from backend.simulation.periodic_face_tilings import is_periodic_face_tiling
from backend.simulation.topology_catalog import is_aperiodic_geometry
from backend.simulation.topology_regular import (
    build_hex_cells,
    build_square_cells,
    build_triangle_cells,
)
from backend.simulation.topology_specialized import (
    build_aperiodic_topology_cells,
    build_periodic_face_topology_cells,
)
from backend.simulation.topology_types import LatticeCell, LatticeTopology, topology_revision

TOPOLOGY_CACHE_SIZE = 24


def _mixed_topology(
    geometry: str,
    width: int,
    height: int,
    cells: Iterable[LatticeCell],
    *,
    patch_depth: int | None = None,
) -> LatticeTopology:
    return LatticeTopology(
        geometry=geometry,
        width=width,
        height=height,
        cells=tuple(cells),
        topology_revision=topology_revision(geometry, width, height, patch_depth),
        patch_depth=patch_depth,
    )


def _build_topology_uncached(
    geometry: str,
    width: int,
    height: int,
    patch_depth: int | None = None,
) -> LatticeTopology:
    if geometry == "hex":
        return _mixed_topology(geometry, width, height, build_hex_cells(width, height))
    if geometry == "triangle":
        return _mixed_topology(geometry, width, height, build_triangle_cells(width, height))
    if is_periodic_face_tiling(geometry):
        return _mixed_topology(
            geometry,
            width,
            height,
            build_periodic_face_topology_cells(geometry, width, height),
        )
    if is_aperiodic_geometry(geometry):
        patch_width, patch_height, resolved_patch_depth, cells = build_aperiodic_topology_cells(
            geometry,
            0 if patch_depth is None else int(patch_depth),
        )
        return _mixed_topology(
            geometry,
            patch_width,
            patch_height,
            cells,
            patch_depth=resolved_patch_depth,
        )
    return _mixed_topology(geometry, width, height, build_square_cells(width, height))


@lru_cache(maxsize=TOPOLOGY_CACHE_SIZE)
def _build_topology_cached(
    geometry: str,
    width: int,
    height: int,
    patch_depth: int | None = None,
) -> LatticeTopology:
    return _build_topology_uncached(geometry, width, height, patch_depth)


def build_topology(
    geometry: str,
    width: int,
    height: int,
    patch_depth: int | None = None,
) -> LatticeTopology:
    return _build_topology_cached(
        str(geometry),
        int(width),
        int(height),
        None if patch_depth is None else int(patch_depth),
    )
