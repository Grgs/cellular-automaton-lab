from __future__ import annotations

from typing import Iterable

from backend.simulation.topology_builders import build_topology
from backend.simulation.topology_types import SimulationBoard


def empty_board(
    geometry: str,
    width: int,
    height: int,
    patch_depth: int | None = None,
) -> SimulationBoard:
    topology = build_topology(geometry, width, height, patch_depth)
    return SimulationBoard(
        topology=topology,
        cell_states=[0] * topology.cell_count,
    )


def board_from_states(
    geometry: str,
    width: int,
    height: int,
    cell_states: Iterable[int],
    patch_depth: int | None = None,
) -> SimulationBoard:
    topology = build_topology(geometry, width, height, patch_depth)
    normalized_states = list(cell_states)
    if len(normalized_states) < topology.cell_count:
        normalized_states.extend([0] * (topology.cell_count - len(normalized_states)))
    elif len(normalized_states) > topology.cell_count:
        normalized_states = normalized_states[:topology.cell_count]
    return SimulationBoard(topology=topology, cell_states=normalized_states)


def board_from_cells_by_id(
    geometry: str,
    width: int,
    height: int,
    cells_by_id: dict[str, int],
    patch_depth: int | None = None,
) -> SimulationBoard:
    board = empty_board(geometry, width, height, patch_depth)
    if not cells_by_id:
        return board
    for cell_id, state in cells_by_id.items():
        if board.topology.has_cell(cell_id):
            board.set_state_for(cell_id, int(state))
    return board
