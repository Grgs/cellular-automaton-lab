from __future__ import annotations

from backend.rules.base import AutomatonRule
from backend.simulation.rule_context import RuleContext, topology_frame_for
from backend.simulation.topology import SimulationBoard


class SimulationEngine:
    """Pure simulation logic that is independent from API and rule loading."""

    def step_board(
        self,
        board: SimulationBoard,
        rule: AutomatonRule,
    ) -> SimulationBoard:
        frame = topology_frame_for(board.topology)
        if frame.cell_count == 0:
            return board.clone()
        next_states = [
            rule.next_state(RuleContext(frame, board.cell_states, index))
            for index in range(frame.cell_count)
        ]
        return SimulationBoard(topology=board.topology, cell_states=next_states)
