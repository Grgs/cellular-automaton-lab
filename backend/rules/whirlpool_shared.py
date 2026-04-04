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
        return ctx.select_neighbor_id(
            self.RESTING,
            tiers=self.SOURCE_SELECTION_TIERS,
            cell_id=source_id,
        )

    def has_incoming_source_pulse(self, ctx: RuleContext) -> bool:
        if ctx.current_state != self.RESTING:
            return False
        for source_id in ctx.neighbor_ids_with(self.SOURCE):
            if self.source_emission_target_id(ctx, source_id) == ctx.cell_id:
                return True
        return False

    def swirl_margin(self, counts: dict[str, int]) -> int:
        return counts["clockwise"] - counts["counterclockwise"]

    def should_excite_resting(self, ctx: RuleContext, counts: dict[str, int]) -> bool:
        zone = self.zone_for_radius(ctx.radial_ratio)
        outward_excited = counts["outward"]
        inward_excited = counts["inward"]
        clockwise_excited = counts["clockwise"]
        counterclockwise_excited = counts["counterclockwise"]
        total_excited = counts["total"]
        swirl_margin = self.swirl_margin(counts)

        if zone == "eye":
            return total_excited >= 1

        if zone == "inner":
            return (
                inward_excited >= 1
                and (clockwise_excited >= 1 or total_excited >= 2)
                and swirl_margin >= 0
            )

        if zone == "shear":
            score = (2 * inward_excited) + (3 * clockwise_excited) - (2 * counterclockwise_excited)
            return score >= 4 and inward_excited >= 1 and clockwise_excited >= 1

        if zone == "outer":
            return (
                inward_excited >= 2
                and swirl_margin >= 1
                and (clockwise_excited >= 1 or total_excited >= 3)
                and outward_excited <= 1
            )

        return inward_excited >= 2 and clockwise_excited >= 1 and swirl_margin >= 1

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
