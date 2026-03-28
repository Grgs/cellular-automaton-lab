from __future__ import annotations

from backend.rules.base import AutomatonRule
from backend.simulation.models import SimulationStateData


def validate_state_value(rule: AutomatonRule, state: int) -> None:
    if not rule.is_valid_state(state):
        raise ValueError(
            f"State '{state}' is invalid for rule '{rule.name}'."
        )


def validate_state_values(rule: AutomatonRule, states: list[int]) -> None:
    for state in states:
        validate_state_value(rule, state)


def set_cells_by_id(state: SimulationStateData, cells: list[tuple[str, int]]) -> None:
    for cell_id, next_state in cells:
        if state.topology.has_cell(cell_id):
            state.board.set_state_for(cell_id, int(next_state))


def toggle_cells_by_id(state: SimulationStateData, cell_ids: list[str]) -> None:
    for cell_id in cell_ids:
        if not state.topology.has_cell(cell_id):
            continue
        current_state = state.board.state_for(cell_id)
        state.board.set_state_for(
            cell_id,
            0 if current_state else state.rule.default_paint_state,
        )
