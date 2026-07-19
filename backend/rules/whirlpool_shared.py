from __future__ import annotations

from backend.rules.base import AutomatonRule, CellStateDefinition
from backend.simulation.rule_context import RuleContext
from backend.simulation.rule_context_frames import RuleFrame


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

    def has_outer_guided_relay(self, ctx: RuleContext, counts: dict[str, int]) -> bool:
        if self.zone_for_radius(ctx.radial_ratio) != "outer":
            return False
        wake = self.wake_counts(ctx)
        guided_clockwise_pressure = counts["clockwise"] + min(1, wake["clockwise"])
        guided_swirl_margin = self.swirl_margin(counts) + self.wake_score(ctx)
        tangential_relay = (
            wake["clockwise"] >= 1
            and wake["resistance"] == 0
            and counts["counterclockwise"] == 0
            and counts["outward"] == 0
        )
        return (
            (wake["support"] >= 2 or tangential_relay)
            and wake["resistance"] == 0
            and guided_clockwise_pressure >= 1
            and guided_swirl_margin >= 1
            and counts["outward"] <= 1
        )

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
        outer_tangential_relay = (
            zone == "outer"
            and wake["clockwise"] >= 1
            and wake["resistance"] == 0
            and counterclockwise_excited == 0
            and outward_excited == 0
        )

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
                (guided_inward_pressure >= 2 or strong_trailing_wake or outer_tangential_relay)
                and guided_swirl_margin >= 1
                and (guided_clockwise_pressure >= 1 or total_excited >= 3 or strong_trailing_wake)
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
                if self.has_outer_guided_relay(ctx, counts):
                    return self.EXCITED
            return self.RESTING
        if ctx.current_state != self.RESTING:
            return self.RESTING
        if self.has_incoming_source_pulse(ctx):
            return self.EXCITED
        if self.eye_has_excited_support(ctx, counts):
            return self.EXCITED
        return self.EXCITED if self.should_excite_resting(ctx, counts) else self.RESTING

    def next_states(self, frame: RuleFrame, cell_states: list[int]) -> list[int]:
        cell_count = frame.cell_count
        excited_outward = [0] * cell_count
        excited_inward = [0] * cell_count
        excited_clockwise = [0] * cell_count
        excited_counterclockwise = [0] * cell_count
        excited_total = [0] * cell_count
        trailing_inward = [0] * cell_count
        trailing_clockwise = [0] * cell_count
        refractory_outward = [0] * cell_count
        refractory_counterclockwise = [0] * cell_count

        for index, cell in enumerate(frame.cells):
            outward = inward = clockwise = counterclockwise = total = 0
            wake_inward = wake_clockwise = resistance_outward = resistance_counter = 0
            for neighbor in cell.neighbors:
                state = cell_states[neighbor.index]
                if state == self.EXCITED:
                    total += 1
                    if neighbor.radial == "outward":
                        outward += 1
                    elif neighbor.radial == "inward":
                        inward += 1
                    if neighbor.turn == "clockwise":
                        clockwise += 1
                    elif neighbor.turn == "counterclockwise":
                        counterclockwise += 1
                elif state == self.TRAILING:
                    wake_inward += neighbor.radial == "inward"
                    wake_clockwise += neighbor.turn == "clockwise"
                elif state == self.REFRACTORY:
                    resistance_outward += neighbor.radial == "outward"
                    resistance_counter += neighbor.turn == "counterclockwise"
            excited_outward[index] = outward
            excited_inward[index] = inward
            excited_clockwise[index] = clockwise
            excited_counterclockwise[index] = counterclockwise
            excited_total[index] = total
            trailing_inward[index] = wake_inward
            trailing_clockwise[index] = wake_clockwise
            refractory_outward[index] = resistance_outward
            refractory_counterclockwise[index] = resistance_counter

        incoming_source_pulse = [False] * frame.cell_count
        for source_index, source_state in enumerate(cell_states):
            if source_state != self.SOURCE:
                continue
            best: tuple[tuple[float, float, float, float, int], int] | None = None
            for neighbor in frame.cells[source_index].neighbors:
                target_index = neighbor.index
                if cell_states[target_index] != self.RESTING:
                    continue
                tier_index = self.source_selection_tier(neighbor.radial, neighbor.turn)
                if tier_index is None:
                    continue
                wake_score = (trailing_clockwise[target_index] + trailing_inward[target_index]) - (
                    refractory_counterclockwise[target_index] + refractory_outward[target_index]
                )
                radial_score = max(0.0, -neighbor.radial_delta)
                turn_score = (
                    max(0.0, -neighbor.angle_delta) if neighbor.turn == "clockwise" else 0.0
                )
                candidate = (
                    (
                        float(tier_index),
                        -float(wake_score),
                        -radial_score,
                        -turn_score,
                        neighbor.clockwise_index,
                    ),
                    target_index,
                )
                if best is None or candidate[0] < best[0]:
                    best = candidate
            if best is not None:
                incoming_source_pulse[best[1]] = True

        next_states: list[int] = []
        append_state = next_states.append
        for index, cell in enumerate(frame.cells):
            state = cell_states[index]
            if state == self.SOURCE:
                append_state(self.SOURCE)
                continue
            if state == self.EXCITED:
                append_state(self.TRAILING)
                continue
            if state == self.TRAILING:
                append_state(self.REFRACTORY)
                continue
            zone = self.zone_for_radius(cell.radial_ratio)
            if state == self.REFRACTORY:
                if (cell.shell_rank == 0 and excited_total[index] >= 1) or (
                    zone == "outer"
                    and (
                        (
                            excited_inward[index] >= 1
                            and (excited_clockwise[index] >= 1 or excited_total[index] >= 2)
                        )
                        or self._outer_guided_relay_from_counts(
                            excited_outward[index],
                            excited_clockwise[index],
                            excited_counterclockwise[index],
                            trailing_inward[index],
                            trailing_clockwise[index],
                            refractory_outward[index],
                            refractory_counterclockwise[index],
                        )
                    )
                ):
                    append_state(self.EXCITED)
                else:
                    append_state(self.RESTING)
                continue
            if state != self.RESTING:
                append_state(self.RESTING)
                continue
            if incoming_source_pulse[index] or (cell.shell_rank == 0 and excited_total[index] >= 1):
                append_state(self.EXCITED)
                continue
            append_state(
                self.EXCITED
                if self._should_excite_from_counts(
                    zone,
                    excited_outward[index],
                    excited_inward[index],
                    excited_clockwise[index],
                    excited_counterclockwise[index],
                    excited_total[index],
                    trailing_inward[index],
                    trailing_clockwise[index],
                    refractory_outward[index],
                    refractory_counterclockwise[index],
                )
                else self.RESTING
            )
        return next_states

    def _outer_guided_relay_from_counts(
        self,
        outward: int,
        clockwise: int,
        counterclockwise: int,
        wake_inward: int,
        wake_clockwise: int,
        resistance_outward: int,
        resistance_counterclockwise: int,
    ) -> bool:
        support = wake_clockwise + wake_inward
        resistance = resistance_counterclockwise + resistance_outward
        guided_clockwise = clockwise + min(1, wake_clockwise)
        guided_swirl = clockwise - counterclockwise + support - resistance
        tangential = (
            wake_clockwise >= 1 and resistance == 0 and counterclockwise == 0 and outward == 0
        )
        return (
            (support >= 2 or tangential)
            and resistance == 0
            and guided_clockwise >= 1
            and guided_swirl >= 1
            and outward <= 1
        )

    def _should_excite_from_counts(
        self,
        zone: str,
        outward: int,
        inward: int,
        clockwise: int,
        counterclockwise: int,
        total: int,
        wake_inward: int,
        wake_clockwise: int,
        resistance_outward: int,
        resistance_counterclockwise: int,
    ) -> bool:
        support = wake_clockwise + wake_inward
        resistance = resistance_counterclockwise + resistance_outward
        guided_inward = inward + min(1, wake_inward)
        guided_clockwise = clockwise + min(1, wake_clockwise)
        guided_swirl = clockwise - counterclockwise + support - resistance
        strong_wake = support >= 2
        if zone == "eye":
            return total >= 1
        if zone == "inner":
            return inward >= 1 and (guided_clockwise >= 1 or total >= 2) and guided_swirl >= 0
        if zone == "shear":
            score = (
                (2 * guided_inward)
                + (3 * guided_clockwise)
                + support
                - (2 * counterclockwise)
                - (3 * resistance)
            )
            return (
                score >= 5
                and guided_inward >= 1
                and guided_clockwise >= 1
                and (total >= 1 or strong_wake)
            )
        if zone == "outer":
            tangential = (
                wake_clockwise >= 1 and resistance == 0 and counterclockwise == 0 and outward == 0
            )
            return (
                (guided_inward >= 2 or strong_wake or tangential)
                and guided_swirl >= 1
                and (guided_clockwise >= 1 or total >= 3 or strong_wake)
                and outward <= 1
            )
        return guided_inward >= 2 and guided_clockwise >= 1 and guided_swirl >= 1
