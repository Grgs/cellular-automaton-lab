from __future__ import annotations

from backend.simulation.topology_types import (
    LatticeCell,
    REGULAR_CELL_KIND,
    regular_cell_id,
)

SQUARE_NEIGHBOR_OFFSETS = (
    (-1, -1),
    (0, -1),
    (1, -1),
    (-1, 0),
    (1, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
)
HEX_NEIGHBOR_OFFSETS_EVEN_ROW = (
    (-1, -1),
    (0, -1),
    (1, 0),
    (0, 1),
    (-1, 1),
    (-1, 0),
)
HEX_NEIGHBOR_OFFSETS_ODD_ROW = (
    (0, -1),
    (1, -1),
    (1, 0),
    (1, 1),
    (0, 1),
    (-1, 0),
)
TRIANGLE_NEIGHBOR_OFFSETS_UP = (
    (-2, 0),
    (-1, 0),
    (1, 0),
    (2, 0),
    (-1, -1),
    (0, -1),
    (1, -1),
    (-2, 1),
    (-1, 1),
    (0, 1),
    (1, 1),
    (2, 1),
)
TRIANGLE_NEIGHBOR_OFFSETS_DOWN = (
    (-2, -1),
    (-1, -1),
    (0, -1),
    (1, -1),
    (2, -1),
    (-2, 0),
    (-1, 0),
    (1, 0),
    (2, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
)


def _regular_neighbor_id(
    x: int,
    y: int,
    width: int,
    height: int,
) -> str | None:
    if 0 <= x < width and 0 <= y < height:
        return regular_cell_id(x, y)
    return None


def build_square_cells(width: int, height: int) -> tuple[LatticeCell, ...]:
    cells: list[LatticeCell] = []
    for y in range(height):
        for x in range(width):
            neighbors = tuple(
                _regular_neighbor_id(x + dx, y + dy, width, height)
                for dx, dy in SQUARE_NEIGHBOR_OFFSETS
            )
            cells.append(
                LatticeCell(
                    id=regular_cell_id(x, y),
                    kind=REGULAR_CELL_KIND,
                    neighbors=neighbors,
                )
            )
    return tuple(cells)


def build_hex_cells(width: int, height: int) -> tuple[LatticeCell, ...]:
    cells: list[LatticeCell] = []
    for y in range(height):
        offsets = HEX_NEIGHBOR_OFFSETS_ODD_ROW if y % 2 == 1 else HEX_NEIGHBOR_OFFSETS_EVEN_ROW
        for x in range(width):
            neighbors = tuple(
                _regular_neighbor_id(x + dx, y + dy, width, height) for dx, dy in offsets
            )
            cells.append(
                LatticeCell(
                    id=regular_cell_id(x, y),
                    kind=REGULAR_CELL_KIND,
                    neighbors=neighbors,
                )
            )
    return tuple(cells)


def build_triangle_cells(width: int, height: int) -> tuple[LatticeCell, ...]:
    cells: list[LatticeCell] = []
    for y in range(height):
        even_offsets, odd_offsets = (
            (TRIANGLE_NEIGHBOR_OFFSETS_UP, TRIANGLE_NEIGHBOR_OFFSETS_DOWN)
            if y % 2 == 0
            else (TRIANGLE_NEIGHBOR_OFFSETS_DOWN, TRIANGLE_NEIGHBOR_OFFSETS_UP)
        )
        for x in range(width):
            offsets = even_offsets if x % 2 == 0 else odd_offsets
            neighbors = tuple(
                _regular_neighbor_id(x + dx, y + dy, width, height) for dx, dy in offsets
            )
            cells.append(
                LatticeCell(
                    id=regular_cell_id(x, y),
                    kind=REGULAR_CELL_KIND,
                    neighbors=neighbors,
                )
            )
    return tuple(cells)
