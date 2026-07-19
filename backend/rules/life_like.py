from __future__ import annotations

from backend.rules.base import AutomatonRule, CellStateDefinition
from backend.simulation.rule_context import RuleContext
from backend.simulation.rule_context_frames import RuleFrame
from backend.simulation.rule_frame_capabilities import ADJACENCY_FRAME_CAPABILITIES

BINARY_STATES = (
    CellStateDefinition(0, "Dead", "#f8f1e5"),
    CellStateDefinition(1, "Live", "#1f2430"),
)


def apply_binary_life_rule(
    current_state: int,
    live_neighbors: int,
    *,
    births: frozenset[int],
    survives: frozenset[int],
) -> int:
    if current_state == 1:
        return 1 if live_neighbors in survives else 0
    return 1 if live_neighbors in births else 0


class BinaryLifeRule(AutomatonRule):
    frame_capabilities = ADJACENCY_FRAME_CAPABILITIES
    states = BINARY_STATES
    default_paint_state = 1
    randomize_weights = {0: 0.5, 1: 0.5}

    births: frozenset[int] = frozenset()
    survives: frozenset[int] = frozenset()

    def next_state(self, ctx: RuleContext) -> int:
        return apply_binary_life_rule(
            ctx.current_state,
            ctx.count_live_neighbors(),
            births=self.births,
            survives=self.survives,
        )

    def next_states(self, frame: RuleFrame, cell_states: list[int]) -> list[int]:
        births = self.births
        survives = self.survives
        next_states: list[int] = []
        append_state = next_states.append
        for index in range(frame.cell_count):
            live_neighbors = 0
            for neighbor_index in frame.neighbor_indexes_for(index):
                live_neighbors += cell_states[neighbor_index] != 0
            thresholds = survives if cell_states[index] == 1 else births
            append_state(1 if live_neighbors in thresholds else 0)
        return next_states


class KindLifeRule(AutomatonRule):
    frame_capabilities = ADJACENCY_FRAME_CAPABILITIES
    states = BINARY_STATES
    default_paint_state = 1
    randomize_weights = {0: 0.5, 1: 0.5}

    kind_thresholds: dict[str, tuple[frozenset[int], frozenset[int]]] = {}
    kind_aliases: dict[str, str] = {}
    default_kind: str | None = None

    def resolve_kind(self, kind: str) -> str:
        normalized_kind = self.kind_aliases.get(kind, kind)
        if normalized_kind in self.kind_thresholds:
            return normalized_kind
        if self.default_kind is not None:
            return self.default_kind
        return next(iter(self.kind_thresholds))

    def next_state(self, ctx: RuleContext) -> int:
        resolved_kind = self.resolve_kind(ctx.kind)
        births, survives = self.kind_thresholds[resolved_kind]
        return apply_binary_life_rule(
            ctx.current_state,
            ctx.count_live_neighbors(),
            births=births,
            survives=survives,
        )

    def next_states(self, frame: RuleFrame, cell_states: list[int]) -> list[int]:
        thresholds_by_kind: dict[str, tuple[frozenset[int], frozenset[int]]] = {}
        next_states: list[int] = []
        append_state = next_states.append
        for index in range(frame.cell_count):
            cell_kind = frame.cell_kind_for(index)
            thresholds = thresholds_by_kind.get(cell_kind)
            if thresholds is None:
                thresholds = self.kind_thresholds[self.resolve_kind(cell_kind)]
                thresholds_by_kind[cell_kind] = thresholds
            live_neighbors = 0
            for neighbor_index in frame.neighbor_indexes_for(index):
                live_neighbors += cell_states[neighbor_index] != 0
            births, survives = thresholds
            active_thresholds = survives if cell_states[index] == 1 else births
            append_state(1 if live_neighbors in active_thresholds else 0)
        return next_states
