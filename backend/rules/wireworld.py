from backend.rules.base import AutomatonRule, CellStateDefinition
from backend.simulation.rule_context import RuleContext
from backend.simulation.rule_context_frames import TopologyFrame
from backend.simulation.rule_frame_capabilities import ADJACENCY_FRAME_CAPABILITIES


class WireWorldRule(AutomatonRule):
    frame_capabilities = ADJACENCY_FRAME_CAPABILITIES
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

    def next_states(self, frame: TopologyFrame, cell_states: list[int]) -> list[int]:
        next_states: list[int] = []
        append_state = next_states.append
        for index, cell in enumerate(frame.cells):
            current_state = cell_states[index]
            if current_state == 0:
                append_state(0)
            elif current_state == 1:
                append_state(2)
            elif current_state == 2:
                append_state(3)
            elif current_state == 3:
                head_neighbors = sum(
                    cell_states[neighbor.index] == 1 for neighbor in cell.neighbors
                )
                append_state(1 if head_neighbors in (1, 2) else 3)
            else:
                append_state(0)
        return next_states
