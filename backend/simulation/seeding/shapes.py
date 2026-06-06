"""Named geometric seed patterns (Policy A: shape-faithful seeding).

A pattern is a small set of integer ``(x, y)`` cell offsets. :func:`place_pattern`
centres the pattern on a topology's centroid, scales it to the tiling's
characteristic cell spacing, and lights the cell nearest to each offset.

Unlike the traversal seed -- which walks a bit string into canonical order and
preserves the live-cell *count* across tilings -- this preserves the 2-D *shape*:
a glider lands like a glider on hex or penrose, modulo how each tiling samples
the points. Offsets use screen coordinates (y increases downward), matching the
rest of the geometry pipeline.
"""

from __future__ import annotations

from backend.simulation.rule_context_frames import TopologyFrame

# Recognisable Life patterns as (x, y) cell offsets.
NAMED_PATTERNS: dict[str, tuple[tuple[int, int], ...]] = {
    "single": ((0, 0),),
    "blinker": ((-1, 0), (0, 0), (1, 0)),
    "block": ((0, 0), (1, 0), (0, 1), (1, 1)),
    "glider": ((1, 0), (2, 1), (0, 2), (1, 2), (2, 2)),
    "r-pentomino": ((1, 0), (2, 0), (0, 1), (1, 1), (1, 2)),
    "toad": ((1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1)),
    "acorn": ((1, 0), (3, 1), (0, 2), (1, 2), (4, 2), (5, 2), (6, 2)),
}

PATTERN_NAMES: tuple[str, ...] = tuple(NAMED_PATTERNS)


def _characteristic_pitch(frame: TopologyFrame) -> float:
    """Median nearest-neighbour centre distance -- the tiling's cell spacing."""
    distances: list[float] = []
    for cell in frame.cells:
        cx, cy = cell.center
        nearest: float | None = None
        for neighbor in cell.neighbors:
            ncx, ncy = frame.cells[neighbor.index].center
            distance = ((ncx - cx) ** 2 + (ncy - cy) ** 2) ** 0.5
            if distance > 0 and (nearest is None or distance < nearest):
                nearest = distance
        if nearest is not None:
            distances.append(nearest)
    if not distances:
        return 1.0
    distances.sort()
    return distances[len(distances) // 2]


def place_pattern(frame: TopologyFrame, offsets: tuple[tuple[int, int], ...]) -> dict[str, int]:
    """Light the cell nearest to each pattern offset, centred on the board."""
    if not offsets or frame.cell_count == 0:
        return {}

    pitch = _characteristic_pitch(frame)
    mean_x = sum(dx for dx, _ in offsets) / len(offsets)
    mean_y = sum(dy for _, dy in offsets) / len(offsets)
    center_x, center_y = frame.center

    cells_by_id: dict[str, int] = {}
    for dx, dy in offsets:
        target_x = center_x + (dx - mean_x) * pitch
        target_y = center_y + (dy - mean_y) * pitch
        best_index = -1
        best_distance: float | None = None
        for index, cell in enumerate(frame.cells):
            distance = (cell.center[0] - target_x) ** 2 + (cell.center[1] - target_y) ** 2
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_index = index
        if best_index >= 0:
            cells_by_id[frame.cells[best_index].id] = 1
    return cells_by_id
