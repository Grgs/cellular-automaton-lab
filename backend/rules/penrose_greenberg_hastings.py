from __future__ import annotations

from backend.rules.base import AutomatonRule, CellStateDefinition
from backend.simulation.rule_context import RuleContext


class PenroseGreenbergHastingsRule(AutomatonRule):
    RESTING = 0
    EXCITED = 1
    TRAILING = 2
    REFRACTORY = 3

    name = "penrose-greenberg-hastings"
    display_name = "Excitable: Penrose Greenberg-Hastings"
    description = "A 4-state excitable-wave rule on Penrose P3 rhombs with edge-adjacent activation."
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
