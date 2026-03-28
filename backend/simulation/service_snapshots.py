from __future__ import annotations

from backend.simulation.models import RuleSnapshot, SimulationSnapshot, SimulationStateData
from backend.simulation.service_boards import clone_service_board


def snapshot_state(state: SimulationStateData) -> SimulationSnapshot:
    return SimulationSnapshot(
        board=clone_service_board(state.board),
        config=state.config,
        running=state.running,
        generation=state.generation,
        rule=RuleSnapshot.from_rule(state.rule),
    )
