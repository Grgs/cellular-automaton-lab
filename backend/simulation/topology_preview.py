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

from backend.simulation.rule_context_frames import topology_frame_for
from backend.simulation.rule_context_geometry import cell_geometry
from backend.simulation.seeding.comparison import board_size_for
from backend.simulation.seeding.shapes import NAMED_PATTERNS, place_pattern
from backend.simulation.seeding.traversal import TRAVERSALS
from backend.simulation.topology import build_topology
from backend.simulation.topology_catalog import SUPPORTED_GEOMETRIES

# A thumbnail of a very large patch is neither useful nor cheap to ship, so the
# preview refuses oversized topologies. The frontend also gates on cell_count.
# The cap covers the default sweep size of most tilings (so their begin/end
# preview is offered); only a few extra-dense aperiodic/Archimedean tilings whose
# default patch runs into the tens of thousands of cells stay above it, where the
# ~5 MiB payload and DOM cost would not earn a useful 132 px thumbnail.
_MAX_PREVIEW_CELLS = 10000
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

    grid_size_value = payload.get("grid_size")
    if grid_size_value not in (None, ""):
        # Match the size a comparison sweep would use for this geometry, so a
        # live seed preview lands cells exactly where the run will.
        grid_size = _bounded_int(
            grid_size_value, default=16, low=_MIN_DIMENSION, high=_MAX_DIMENSION, name="grid_size"
        )
        width, height, patch_depth = board_size_for(geometry, grid_size)
    else:
        width = _bounded_int(
            payload.get("width"), default=16, low=_MIN_DIMENSION, high=_MAX_DIMENSION, name="width"
        )
        height = _bounded_int(
            payload.get("height"),
            default=16,
            low=_MIN_DIMENSION,
            high=_MAX_DIMENSION,
            name="height",
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

    result: dict[str, Any] = {"topology_revision": topology.topology_revision, "cells": cells}

    # When a traversal is requested, also return the canonical cell-id order so a
    # caller can place a seed bit-string onto this tiling client-side (the same
    # mapping the comparison uses), e.g. for a live seed preview.
    traversal = payload.get("traversal")
    if traversal is not None:
        if not isinstance(traversal, str) or traversal not in TRAVERSALS:
            raise ValueError(f"'traversal' must be one of: {', '.join(sorted(TRAVERSALS))}.")
        frame = topology_frame_for(topology)
        result["order"] = list(TRAVERSALS[traversal](frame))

    # When a named shape is requested, return the exact cells the comparison would
    # light (Policy A geometric placement), so a live preview matches the run.
    pattern = payload.get("pattern")
    if pattern not in (None, ""):
        if not isinstance(pattern, str) or pattern not in NAMED_PATTERNS:
            raise ValueError(f"'pattern' must be one of: {', '.join(sorted(NAMED_PATTERNS))}.")
        frame = topology_frame_for(topology)
        result["shape_cells"] = place_pattern(frame, NAMED_PATTERNS[pattern])

    return result
