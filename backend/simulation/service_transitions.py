from __future__ import annotations

from collections.abc import Callable, Sequence

from backend.payload_types import TopologySpecInput, TopologySpecPatch
from backend.rules import RuleRegistry
from backend.rules.base import AutomatonRule
from backend.simulation.models import SimulationStateData
from backend.simulation.topology import SimulationBoard
from backend.simulation.transition_planner import plan_config_transition, plan_reset_transition

ChoiceFunction = Callable[..., Sequence[int]]
BoardFactory = Callable[[str, int, int, AutomatonRule, int | None, ChoiceFunction], SimulationBoard]
EmptyBoardFactory = Callable[[str, int, int, int | None], SimulationBoard]
TransferBoardFactory = Callable[[SimulationBoard, str, int, int, int | None], SimulationBoard]
CoerceBoardFactory = Callable[[SimulationBoard, AutomatonRule], SimulationBoard]


def apply_reset_transition(
    state: SimulationStateData,
    rule_registry: RuleRegistry,
    *,
    create_random_board: BoardFactory,
    create_empty_board: EmptyBoardFactory,
    choice_fn: ChoiceFunction,
    topology_spec: TopologySpecInput | None = None,
    rule_name: str | None = None,
    speed: float | None = None,
    randomize: bool = False,
) -> None:
    plan = plan_reset_transition(
        state,
        rule_registry,
        topology_spec=topology_spec,
        rule_name=rule_name,
        speed=speed,
        randomize=randomize,
    )

    state.running = False
    state.generation = 0
    state.rule = plan.rule
    next_board = (
        create_random_board(
            plan.config.geometry,
            plan.config.width,
            plan.config.height,
            plan.rule,
            plan.config.patch_depth,
            choice_fn,
        )
        if plan.board_mode == "randomize"
        else create_empty_board(
            plan.config.geometry,
            plan.config.width,
            plan.config.height,
            plan.config.patch_depth,
        )
    )
    state.board = next_board
    state.config = plan.config.updated(
        width=next_board.topology.width,
        height=next_board.topology.height,
    )


def apply_config_transition(
    state: SimulationStateData,
    rule_registry: RuleRegistry,
    *,
    transfer_board: TransferBoardFactory,
    coerce_board_to_rule: CoerceBoardFactory,
    topology_spec: TopologySpecPatch | None = None,
    speed: float | None = None,
    rule_name: str | None = None,
) -> None:
    plan = plan_config_transition(
        state,
        rule_registry,
        topology_spec=topology_spec,
        speed=speed,
        rule_name=rule_name,
    )

    if plan.board_mode == "transfer":
        state.running = False
        state.board = transfer_board(
            state.board,
            plan.config.geometry,
            plan.config.width,
            plan.config.height,
            plan.config.patch_depth,
        )
    if plan.coerce_rule_states:
        state.board = coerce_board_to_rule(state.board, plan.rule)
        state.rule = plan.rule
    state.config = plan.config.updated(
        width=state.board.topology.width,
        height=state.board.topology.height,
    )
