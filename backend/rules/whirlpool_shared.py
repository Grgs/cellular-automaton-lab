from __future__ import annotations

from backend.rules.base import AutomatonRule, CellStateDefinition
from backend.simulation.rule_context import RuleContext


class WhirlpoolRuleBase(AutomatonRule):
    RESTING = 0
    EXCITED = 1
    TRAILING = 2
    REFRACTORY = 3
    SOURCE = 4

    EYE_CORE_MAX_RADIUS = 0.10
    INNER_RELAY_MAX_RADIUS = 0.26
    SHEAR_RING_MAX_RADIUS = 0.56
    OUTER_RING_MAX_RADIUS = 0.86

    SOURCE_SELECTION_TIERS = (
        ("outward", "clockwise"),
        ("outward", None),
        (None, "clockwise"),
        (None, None),
    )
    states = (
        CellStateDefinition(RESTING, "Resting", "#f8f1e5"),
        CellStateDefinition(EXCITED, "Excited", "#2f80ed"),
        CellStateDefinition(TRAILING, "Trailing", "#4ecdc4"),
        CellStateDefinition(REFRACTORY, "Refractory", "#243042"),
        CellStateDefinition(SOURCE, "Source", "#f2994a"),
    )
    default_paint_state = EXCITED
    randomize_weights = None

    def zone_for_radius(self, radius: float) -> str:
        if radius <= self.EYE_CORE_MAX_RADIUS:
            return "eye"
        if radius <= self.INNER_RELAY_MAX_RADIUS:
            return "inner"
        if radius <= self.SHEAR_RING_MAX_RADIUS:
            return "shear"
        if radius <= self.OUTER_RING_MAX_RADIUS:
            return "outer"
        return "rim"

    def eye_has_excited_support(self, ctx: RuleContext, counts: dict[str, int]) -> bool:
        return ctx.in_shell(0) and counts["total"] >= 1

    def source_emission_target_id(self, ctx: RuleContext, source_id: str) -> str | None:
        candidates: list[tuple[tuple[float, float, float, float, int], str]] = []
        source = ctx.frame.cell_for(source_id)
        for neighbor in source.neighbors:
            target = ctx.frame.cells[neighbor.index]
            if ctx.state_for(target.id) != self.RESTING:
                continue
            tier_index = self.source_selection_tier(neighbor.radial, neighbor.turn)
            if tier_index is None:
                continue
            wake_score = self.wake_score(ctx, cell_id=target.id)
            radial_score = max(0.0, -neighbor.radial_delta)
            turn_score = max(0.0, -neighbor.angle_delta) if neighbor.turn == "clockwise" else 0.0
            candidates.append(
                (
                    (
                        float(tier_index),
                        -float(wake_score),
                        -radial_score,
                        -turn_score,
                        neighbor.clockwise_index,
                    ),
                    target.id,
                )
            )
        if not candidates:
            return None
        return min(candidates, key=lambda candidate: candidate[0])[1]

    def has_incoming_source_pulse(self, ctx: RuleContext) -> bool:
        if ctx.current_state != self.RESTING:
            return False
        for source_id in ctx.neighbor_ids_with(self.SOURCE):
            if self.source_emission_target_id(ctx, source_id) == ctx.cell_id:
                return True
        return False

    def swirl_margin(self, counts: dict[str, int]) -> int:
        return counts["clockwise"] - counts["counterclockwise"]

    def source_selection_tier(self, radial: str, turn: str) -> int | None:
        for index, (tier_radial, tier_turn) in enumerate(self.SOURCE_SELECTION_TIERS):
            if (tier_radial is None or radial == tier_radial) and (
                tier_turn is None or turn == tier_turn
            ):
                return index
        return None

    def wake_counts(self, ctx: RuleContext, *, cell_id: str | None = None) -> dict[str, int]:
        trailing = ctx.directional_counts(self.TRAILING, cell_id=cell_id)
        refractory = ctx.directional_counts(self.REFRACTORY, cell_id=cell_id)
        return {
            "support": trailing["clockwise"] + trailing["inward"],
            "resistance": refractory["counterclockwise"] + refractory["outward"],
            "clockwise": trailing["clockwise"],
            "inward": trailing["inward"],
            "counterclockwise": refractory["counterclockwise"],
            "outward": refractory["outward"],
        }

    def wake_score(self, ctx: RuleContext, *, cell_id: str | None = None) -> int:
        wake = self.wake_counts(ctx, cell_id=cell_id)
        return wake["support"] - wake["resistance"]

    def should_excite_resting(self, ctx: RuleContext, counts: dict[str, int]) -> bool:
        zone = self.zone_for_radius(ctx.radial_ratio)
        outward_excited = counts["outward"]
        inward_excited = counts["inward"]
        clockwise_excited = counts["clockwise"]
        counterclockwise_excited = counts["counterclockwise"]
        total_excited = counts["total"]
        swirl_margin = self.swirl_margin(counts)
        wake = self.wake_counts(ctx)
        wake_score = wake["support"] - wake["resistance"]
        guided_inward_pressure = inward_excited + min(1, wake["inward"])
        guided_clockwise_pressure = clockwise_excited + min(1, wake["clockwise"])
        guided_swirl_margin = swirl_margin + wake_score
        strong_trailing_wake = wake["support"] >= 2

        if zone == "eye":
            return total_excited >= 1

        if zone == "inner":
            return (
                inward_excited >= 1
                and (guided_clockwise_pressure >= 1 or total_excited >= 2)
                and guided_swirl_margin >= 0
            )

        if zone == "shear":
            score = (
                (2 * guided_inward_pressure)
                + (3 * guided_clockwise_pressure)
                + wake["support"]
                - (2 * counterclockwise_excited)
                - (3 * wake["resistance"])
            )
            return (
                score >= 5
                and guided_inward_pressure >= 1
                and guided_clockwise_pressure >= 1
                and (total_excited >= 1 or strong_trailing_wake)
            )

        if zone == "outer":
            return (
                guided_inward_pressure >= 2
                and guided_swirl_margin >= 1
                and (guided_clockwise_pressure >= 1 or total_excited >= 3)
                and outward_excited <= 1
            )

        return (
            guided_inward_pressure >= 2
            and guided_clockwise_pressure >= 1
            and guided_swirl_margin >= 1
        )

    def next_state(self, ctx: RuleContext) -> int:
        counts = ctx.directional_counts(self.EXCITED)

        if ctx.current_state == self.SOURCE:
            return self.SOURCE
        if ctx.current_state == self.EXCITED:
            return self.TRAILING
        if ctx.current_state == self.TRAILING:
            return self.REFRACTORY
        if ctx.current_state == self.REFRACTORY:
            if self.eye_has_excited_support(ctx, counts):
                return self.EXCITED
            if self.zone_for_radius(ctx.radial_ratio) == "outer":
                if counts["inward"] >= 1 and (counts["clockwise"] >= 1 or counts["total"] >= 2):
                    return self.EXCITED
            return self.RESTING
        if ctx.current_state != self.RESTING:
            return self.RESTING
        if self.has_incoming_source_pulse(ctx):
            return self.EXCITED
        if self.eye_has_excited_support(ctx, counts):
            return self.EXCITED
        return self.EXCITED if self.should_excite_resting(ctx, counts) else self.RESTING
