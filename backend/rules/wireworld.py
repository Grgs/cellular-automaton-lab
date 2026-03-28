from backend.rules.base import AutomatonRule, CellStateDefinition
from backend.simulation.rule_context import RuleContext


class WireWorldRule(AutomatonRule):
    name = "wireworld"
    display_name = "Circuit: WireWorld"
    description = "Electron heads and tails travel through conductors to form digital circuits."
    states = (
        CellStateDefinition(0, "Empty", "#f8f1e5"),
        CellStateDefinition(1, "Electron Head", "#2f80ed"),
        CellStateDefinition(2, "Electron Tail", "#d64e4e"),
        CellStateDefinition(3, "Conductor", "#d88c32"),
    )
    default_paint_state = 3
    randomize_weights = None

    def next_state(self, ctx: RuleContext) -> int:
        if ctx.current_state == 0:
            return 0
        if ctx.current_state == 1:
            return 2
        if ctx.current_state == 2:
            return 3
        if ctx.current_state == 3:
            head_neighbors = ctx.count_neighbors(1)
            return 1 if head_neighbors in (1, 2) else 3
        return 0
