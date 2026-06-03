"""Build a single topology and return its cells enriched with geometry.

Stateless helper behind ``POST /api/topology/preview`` (and the standalone
``/api/topology/preview`` worker command). The compare-mode thumbnails use it to
draw a tiling's begin/end board: every cell is returned with a polygon
(``vertices``) so the frontend renders all families uniformly, including regular
grids whose geometry is otherwise computed client-side.

Validation failures raise ``ValueError`` for the host layer to turn into a 4xx
response.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from backend.simulation.rule_context_geometry import cell_geometry
from backend.simulation.topology import build_topology
from backend.simulation.topology_catalog import SUPPORTED_GEOMETRIES

# A thumbnail of a very large patch is neither useful nor cheap to ship, so the
# preview refuses oversized topologies. The frontend also gates on cell_count.
_MAX_PREVIEW_CELLS = 4000
_MIN_DIMENSION = 2
_MAX_DIMENSION = 64
_MAX_PATCH_DEPTH = 12


def _bounded_int(value: Any, *, default: int, low: int, high: int, name: str) -> int:
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"'{name}' must be an integer.") from error
    if parsed < low or parsed > high:
        raise ValueError(f"'{name}' must be between {low} and {high}.")
    return parsed


def build_topology_preview(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate ``payload`` and return ``{topology_revision, cells:[...]}``."""
    geometry = payload.get("geometry")
    if not isinstance(geometry, str) or geometry not in SUPPORTED_GEOMETRIES:
        raise ValueError("'geometry' must be a supported geometry key.")

    width = _bounded_int(
        payload.get("width"), default=16, low=_MIN_DIMENSION, high=_MAX_DIMENSION, name="width"
    )
    height = _bounded_int(
        payload.get("height"), default=16, low=_MIN_DIMENSION, high=_MAX_DIMENSION, name="height"
    )
    patch_depth_value = payload.get("patch_depth")
    patch_depth = (
        None
        if patch_depth_value in (None, "")
        else _bounded_int(
            patch_depth_value, default=0, low=0, high=_MAX_PATCH_DEPTH, name="patch_depth"
        )
    )

    topology = build_topology(geometry, width, height, patch_depth)
    if topology.cell_count > _MAX_PREVIEW_CELLS:
        raise ValueError(
            f"Topology has {topology.cell_count} cells; preview limit is {_MAX_PREVIEW_CELLS}."
        )

    cells: list[dict[str, Any]] = []
    for cell in topology.cells:
        kind, center, vertices = cell_geometry(topology, cell)
        cells.append(
            {
                "id": cell.id,
                "kind": kind,
                "center": {"x": center[0], "y": center[1]},
                "vertices": [{"x": vertex[0], "y": vertex[1]} for vertex in (vertices or ())],
            }
        )
    return {"topology_revision": topology.topology_revision, "cells": cells}
