from __future__ import annotations

from backend.rules.base import AutomatonRule, CellStateDefinition
from backend.simulation.rule_context import RuleContext
from backend.simulation.rule_context_frames import TopologyFrame
from backend.simulation.rule_frame_capabilities import ADJACENCY_FRAME_CAPABILITIES


class PenroseGreenbergHastingsRule(AutomatonRule):
    frame_capabilities = ADJACENCY_FRAME_CAPABILITIES
    RESTING = 0
    EXCITED = 1
    TRAILING = 2
    REFRACTORY = 3

    name = "penrose-greenberg-hastings"
    display_name = "Excitable: Penrose Greenberg-Hastings"
    description = (
        "A 4-state excitable-wave rule on Penrose P3 rhombs with edge-adjacent activation."
    )
    states = (
        CellStateDefinition(RESTING, "Resting", "#f8f1e5"),
        CellStateDefinition(EXCITED, "Excited", "#2f80ed"),
        CellStateDefinition(TRAILING, "Trailing", "#4ecdc4"),
        CellStateDefinition(REFRACTORY, "Refractory", "#243042"),
    )
    default_paint_state = EXCITED
    randomize_weights = {
        RESTING: 0.8,
        EXCITED: 0.2,
    }

    def next_state(self, ctx: RuleContext) -> int:
        if ctx.current_state == self.EXCITED:
            return self.TRAILING
        if ctx.current_state == self.TRAILING:
            return self.REFRACTORY
        if ctx.current_state == self.REFRACTORY:
            return self.RESTING
        if ctx.current_state != self.RESTING:
            return self.RESTING
        return self.EXCITED if ctx.has_neighbor_state(self.EXCITED) else self.RESTING

    def next_states(self, frame: TopologyFrame, cell_states: list[int]) -> list[int]:
        next_states: list[int] = []
        append_state = next_states.append
        for index, cell in enumerate(frame.cells):
            current_state = cell_states[index]
            if current_state == self.EXCITED:
                append_state(self.TRAILING)
            elif current_state == self.TRAILING:
                append_state(self.REFRACTORY)
            elif current_state != self.RESTING:
                append_state(self.RESTING)
            elif any(cell_states[neighbor.index] == self.EXCITED for neighbor in cell.neighbors):
                append_state(self.EXCITED)
            else:
                append_state(self.RESTING)
        return next_states
