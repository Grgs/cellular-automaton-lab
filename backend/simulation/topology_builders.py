from __future__ import annotations

import os
from collections.abc import Iterable
from functools import lru_cache

from backend.public_errors import PublicApiError
from backend.simulation.topology_implementation_registry import get_topology_implementation
from backend.simulation.topology_types import LatticeCell, LatticeTopology, topology_revision

TOPOLOGY_CACHE_SIZE = 24
INTERACTIVE_TOPOLOGY_CELL_BUDGET = 20_000
INTERNAL_ALLOW_OVERSIZED_TOPOLOGIES_ENV = "CAL_INTERNAL_ALLOW_OVERSIZED_TOPOLOGIES"


def interactive_topology_cell_budget() -> int | None:
    allow_oversized = str(os.environ.get(INTERNAL_ALLOW_OVERSIZED_TOPOLOGIES_ENV, ""))
    if allow_oversized.strip().lower() in {"1", "true", "yes", "on"}:
        return None
    return INTERACTIVE_TOPOLOGY_CELL_BUDGET


class TopologyCellBudgetExceeded(PublicApiError):
    """Raised before an oversized topology enters interactive runtime state."""

    code = "topology_cell_budget_exceeded"

    def __init__(
        self,
        *,
        limit: int,
        estimated_cells: int | None = None,
        actual_cells: int | None = None,
    ) -> None:
        self.limit = int(limit)
        self.estimated_cells = estimated_cells
        self.actual_cells = actual_cells
        count = estimated_cells if estimated_cells is not None else actual_cells
        count_label = "estimated" if estimated_cells is not None else "actual"
        super().__init__(
            f"Topology exceeds the interactive {self.limit:,}-cell limit "
            f"({count_label} cell count: {int(count or 0):,})."
        )

    def to_payload(self) -> dict[str, str | int]:
        payload: dict[str, str | int] = {
            "error": str(self),
            "code": self.code,
            "limit": self.limit,
        }
        if self.estimated_cells is not None:
            payload["estimated_cells"] = self.estimated_cells
        if self.actual_cells is not None:
            payload["actual_cells"] = self.actual_cells
        return payload


def _validate_estimated_cell_count(
    geometry: str,
    width: int,
    height: int,
    patch_depth: int | None,
    max_cells: int | None,
) -> None:
    if max_cells is None:
        return
    implementation = get_topology_implementation(geometry)
    estimator = implementation.estimate_cell_count_ref
    if estimator is None:
        return
    estimated_cells = estimator(geometry, width, height, patch_depth)
    if estimated_cells > max_cells:
        raise TopologyCellBudgetExceeded(
            limit=max_cells,
            estimated_cells=estimated_cells,
        )


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
    *,
    max_cells: int | None = None,
) -> LatticeTopology:
    normalized_geometry = str(geometry)
    normalized_width = int(width)
    normalized_height = int(height)
    normalized_patch_depth = None if patch_depth is None else int(patch_depth)
    _validate_estimated_cell_count(
        normalized_geometry,
        normalized_width,
        normalized_height,
        normalized_patch_depth,
        max_cells,
    )
    topology = _build_topology_cached(
        normalized_geometry,
        normalized_width,
        normalized_height,
        normalized_patch_depth,
    )
    if max_cells is not None and topology.cell_count > max_cells:
        raise TopologyCellBudgetExceeded(
            limit=max_cells,
            actual_cells=topology.cell_count,
        )
    return topology
