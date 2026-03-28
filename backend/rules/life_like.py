from __future__ import annotations

from backend.rules.base import AutomatonRule, CellStateDefinition
from backend.simulation.rule_context import RuleContext


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


class KindLifeRule(AutomatonRule):
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
