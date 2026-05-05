from __future__ import annotations

from typing import Iterable

from backend.simulation.topology import (
    SimulationBoard,
    build_topology,
    parse_regular_cell_id,
)


def board_from_grid(grid: list[list[int]], geometry: str = "square") -> SimulationBoard:
    height = len(grid)
    width = len(grid[0]) if height else 0
    topology = build_topology(geometry, width, height)
    cell_states = [
        int(grid[coords[1]][coords[0]])
        for cell in topology.cells
        for coords in [parse_regular_cell_id(cell.id)]
        if coords is not None
    ]
    return SimulationBoard(topology=topology, cell_states=cell_states)


def regular_grid_from_board(board: SimulationBoard) -> list[list[int]] | None:
    topology = board.topology
    if topology.geometry not in {"square", "hex", "triangle"}:
        return None
    grid = [
        [0] * topology.width
        for _ in range(topology.height)
    ]
    for index, cell in enumerate(topology.cells):
        coords = parse_regular_cell_id(cell.id)
        if coords is None:
            continue
        grid[coords[1]][coords[0]] = int(board.cell_states[index])
    return grid


def board_with_states(
    geometry: str,
    width: int,
    height: int,
    states: Iterable[int],
) -> SimulationBoard:
    topology = build_topology(geometry, width, height)
    normalized = list(states)
    if len(normalized) < topology.cell_count:
        normalized.extend([0] * (topology.cell_count - len(normalized)))
    return SimulationBoard(topology=topology, cell_states=normalized[:topology.cell_count])
