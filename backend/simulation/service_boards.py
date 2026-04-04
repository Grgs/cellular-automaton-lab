from __future__ import annotations

import random
from collections.abc import Callable, Sequence

from backend.defaults import DEFAULT_GEOMETRY
from backend.rules import RuleRegistry
from backend.rules.base import AutomatonRule
from backend.rules.constraints import normalize_rule_dimensions
from backend.simulation.engine import SimulationEngine
from backend.simulation.models import SimulationConfig, SimulationStateData
from backend.simulation.topology import SimulationBoard, empty_board


def build_initial_state(rule_registry: RuleRegistry) -> SimulationStateData:
    default_config = SimulationConfig()
    default_rule = rule_registry.default_for_geometry(DEFAULT_GEOMETRY)
    default_width, default_height = normalize_rule_dimensions(
        default_rule,
        default_config.width,
        default_config.height,
    )
    default_config = default_config.updated(width=default_width, height=default_height)
    return SimulationStateData(
        config=default_config,
        running=False,
        generation=0,
        rule=default_rule,
        board=empty_service_board(DEFAULT_GEOMETRY, default_config.width, default_config.height),
    )


def empty_service_board(
    geometry: str,
    width: int,
    height: int,
    patch_depth: int | None = None,
) -> SimulationBoard:
    return empty_board(geometry, width, height, patch_depth=patch_depth)


def random_service_board(
    geometry: str,
    width: int,
    height: int,
    rule: AutomatonRule,
    patch_depth: int | None = None,
    choice_fn: Callable[..., Sequence[int]] = random.choices,
) -> SimulationBoard:
    if not rule.supports_randomize or not rule.randomize_weights:
        raise ValueError(f"Rule '{rule.name}' does not support random reset.")
    state_values = list(rule.randomize_weights.keys())
    state_weights = list(rule.randomize_weights.values())
    board = empty_service_board(geometry, width, height, patch_depth=patch_depth)
    board.cell_states = list(choice_fn(state_values, weights=state_weights, k=board.topology.cell_count))
    return board


def clone_service_board(board: SimulationBoard) -> SimulationBoard:
    return board.clone()


def coerce_board_to_rule(board: SimulationBoard, rule: AutomatonRule) -> SimulationBoard:
    allowed_states = rule.state_values()
    return SimulationBoard(
        topology=board.topology,
        cell_states=[
            cell_state if cell_state in allowed_states else 0
            for cell_state in board.cell_states
        ],
    )


def transfer_board(
    board: SimulationBoard,
    geometry: str,
    width: int,
    height: int,
    patch_depth: int | None = None,
) -> SimulationBoard:
    resized = empty_service_board(geometry, width, height, patch_depth=patch_depth)
    old_lookup = {
        cell.id: board.cell_states[index]
        for index, cell in enumerate(board.topology.cells)
    }
    for index, cell in enumerate(resized.topology.cells):
        resized.cell_states[index] = old_lookup.get(cell.id, 0)
    return resized


def step_board(engine: SimulationEngine, state: SimulationStateData) -> None:
    state.board = engine.step_board(state.board, state.rule)
    state.generation += 1
