from __future__ import annotations

from functools import lru_cache
from typing import Iterable

from backend.simulation.topology_implementation_registry import get_topology_implementation
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
    implementation = get_topology_implementation(geometry)
    built = implementation.builder_ref(geometry, width, height, patch_depth)
    return _mixed_topology(
        geometry,
        built.width,
        built.height,
        built.cells,
        patch_depth=built.patch_depth,
    )


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
