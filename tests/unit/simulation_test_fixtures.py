from typing import Sequence

from backend.rules.base import AutomatonRule
from backend.simulation.rule_context import RuleContext


BLINKER_GRID = [
    [0, 1, 0],
    [0, 1, 0],
    [0, 1, 0],
]

BLINKER_PADDED_GRID = [
    [0, 1, 0, 0, 0],
    [0, 1, 0, 0, 0],
    [0, 1, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
]


class NeighborTrackingRule(AutomatonRule):
    name = "neighbor-tracking"
    display_name = "Neighbor Tracking"
    description = "Captures neighbor state payloads for tests."

    def __init__(self) -> None:
        self.calls: list[list[int]] = []

    def next_state(self, ctx: RuleContext) -> int:
        self.calls.append(list(ctx.neighbor_states()))
        return 1 if ctx.count_live_neighbors() else 0


class LiveNeighborTrackingRule(AutomatonRule):
    name = "live-neighbor-tracking"
    display_name = "Live Neighbor Tracking"
    description = "Captures non-zero neighbor counts for tests."

    def __init__(self) -> None:
        self.calls: list[int] = []

    def next_state(self, ctx: RuleContext) -> int:
        self.calls.append(ctx.count_live_neighbors())
        return 0
