"""Canonical cell-ID orderings used to map a seed onto any topology.

A *traversal* turns a built topology frame into a deterministic list of cell
IDs. Seeds are then painted by walking that order bit-by-bit, so the same seed
marks the same *number* of cells on every topology and the placement is
reproducible regardless of geometry.

Two orderings ship today:

``bfs`` (the universal default)
    Concentric graph rings from the centre-most cell, ties broken by clockwise
    angle then stable cell ID. This reuses the per-cell ``shell_rank`` and
    ``polar_angle`` already computed on :class:`TopologyFrame`, so it works
    unchanged on regular grids, periodic mixed tilings, and aperiodic patches.

``row-major``
    A best-effort scanline (top-to-bottom, left-to-right) over cell centres.
    Intuitive for grid-like tilings where a 2-D bit pattern should map to rows;
    on irregular/aperiodic patches prefer ``bfs``.
"""

from __future__ import annotations

from collections.abc import Callable

from backend.simulation.rule_context_frames import TopologyFrame
from backend.simulation.rule_context_geometry import clockwise_sort_key

# A traversal maps a built topology frame to a canonical cell-ID ordering.
Traversal = Callable[[TopologyFrame], list[str]]

# Rounding tolerance (in geometry units) used to bucket cell centres into rows
# for the scanline traversal. Centres within this distance share a row.
_ROW_BUCKET = 0.25


def bfs_ring_order(frame: TopologyFrame) -> list[str]:
    """Concentric BFS-ring ordering (the universal default).

    Cells are ordered by ``(shell_rank, clockwise angle, cell id)``. ``shell_rank``
    is the graph distance from the centre-most cell(s), already flooded onto the
    frame; ``polar_angle`` is measured from the board centroid. The trailing cell
    ID makes the order fully deterministic even when angle and rank tie.
    """
    return [
        cell.id
        for cell in sorted(
            frame.cells,
            key=lambda cell: (
                cell.shell_rank,
                clockwise_sort_key(cell.polar_angle),
                cell.id,
            ),
        )
    ]


def row_major_order(frame: TopologyFrame) -> list[str]:
    """Best-effort top-to-bottom, left-to-right scanline over cell centres.

    Centres are bucketed into rows by quantising ``y`` so a near-horizontal band
    of cells shares a row, then ordered left-to-right within the row. Suited to
    grid-like tilings; use :func:`bfs_ring_order` for irregular patches.
    """
    return [
        cell.id
        for cell in sorted(
            frame.cells,
            key=lambda cell: (
                round(cell.center[1] / _ROW_BUCKET),
                round(cell.center[0] / _ROW_BUCKET),
                cell.id,
            ),
        )
    ]


TRAVERSALS: dict[str, Traversal] = {
    "bfs": bfs_ring_order,
    "row-major": row_major_order,
}

DEFAULT_TRAVERSAL = "bfs"


def normalize_bits(seed: str) -> str:
    """Strip everything but ``0``/``1`` so seeds can carry readable separators.

    ``"01100 11000 01000"``, ``"01100,11000,01000"`` and ``"011001100001000"``
    all normalize to the same bit string.
    """
    return "".join(char for char in seed if char in "01")


def paint_bits(order: list[str], bits: str, *, live: int = 1) -> dict[str, int]:
    """Walk ``order`` and mark a cell live for each ``1`` bit.

    The result maps cell ID to ``live`` for every set bit that has a cell to land
    on. Extra bits beyond ``len(order)`` are dropped (see ``seed-truncated`` in
    the comparison layer); extra cells beyond ``len(bits)`` stay dead. The live
    cell count is therefore identical across topologies for a given seed,
    provided the seed fits.
    """
    return {
        cell_id: live
        for cell_id, bit in zip(order, normalize_bits(bits), strict=False)
        if bit == "1"
    }
