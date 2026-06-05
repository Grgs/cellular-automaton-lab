"""Run one seed under one rule across many topologies and collect metrics.

This is the reusable core a CLI or a future "compare mode" UI calls. It owns the
full sweep: build each topology at a sane default size, map the seed onto it
through a traversal, step the shared rule, and summarise the trajectory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.rules import RuleRegistry
from backend.rules.base import AutomatonRule
from backend.simulation.engine import SimulationEngine
from backend.simulation.rule_context_frames import topology_frame_for
from backend.simulation.seeding.metrics import (
    classify,
    first_extinction_step,
    hamming,
    population,
)
from backend.simulation.seeding.traversal import (
    DEFAULT_TRAVERSAL,
    TRAVERSALS,
    normalize_bits,
    paint_bits,
)
from backend.simulation.topology import empty_board
from backend.simulation.topology_catalog import (
    SUPPORTED_GEOMETRIES,
    default_patch_depth_for_tiling_family,
    geometry_uses_patch_depth,
    get_topology_variant_for_geometry,
    minimum_grid_dimension_for_geometry,
    topology_spec_payload,
)

# Default sweep parameters. Kept modest so a full 46-tiling sweep finishes fast.
DEFAULT_RULE = "conway"
DEFAULT_STEPS = 50
DEFAULT_GRID_SIZE = 16

# A comparison is flagged degenerate when more than this fraction of viable
# tilings go extinct in fewer than EARLY_EXTINCTION_STEPS generations.
_EARLY_EXTINCTION_STEPS = 10
_DEGENERATE_FRACTION = 0.5


@dataclass
class TopologyComparisonResult:
    """Outcome of one (seed, rule) run on a single topology."""

    geometry: str
    tiling_family: str
    family: str
    cell_count: int
    seed_bits: int
    seed_cells: int
    population: list[int]
    change_rate: list[float]
    classification: str
    period: int | None
    steps_run: int
    extinction_step: int | None
    note: str | None = None
    # Populated only when compare_seed(..., include_states=True). These let a
    # caller reconstruct the begin/end board (e.g. an "open in board" link).
    topology_spec: dict[str, Any] | None = None
    initial_cells_by_id: dict[str, int] | None = None
    final_cells_by_id: dict[str, int] | None = None

    @property
    def initial_population(self) -> int:
        return self.population[0] if self.population else 0

    @property
    def final_population(self) -> int:
        return self.population[-1] if self.population else 0

    @property
    def normalized_population(self) -> float:
        if self.initial_population == 0:
            return 0.0
        return self.final_population / self.initial_population

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "geometry": self.geometry,
            "tiling_family": self.tiling_family,
            "family": self.family,
            "cell_count": self.cell_count,
            "seed_bits": self.seed_bits,
            "seed_cells": self.seed_cells,
            "initial_population": self.initial_population,
            "final_population": self.final_population,
            "normalized_population": self.normalized_population,
            "classification": self.classification,
            "period": self.period,
            "steps_run": self.steps_run,
            "extinction_step": self.extinction_step,
            "note": self.note,
            "population": self.population,
            "change_rate": self.change_rate,
        }
        if self.topology_spec is not None:
            payload["topology_spec"] = self.topology_spec
        if self.initial_cells_by_id is not None:
            payload["initial_cells_by_id"] = self.initial_cells_by_id
        if self.final_cells_by_id is not None:
            payload["final_cells_by_id"] = self.final_cells_by_id
        return payload


@dataclass
class SeedComparison:
    """Aggregate of one seed swept across a set of topologies."""

    rule_name: str
    seed: str
    seed_bits: int
    traversal: str
    steps: int
    grid_size: int
    results: list[TopologyComparisonResult] = field(default_factory=list)

    @property
    def degenerate(self) -> bool:
        viable = [result for result in self.results if result.note != "error"]
        if not viable:
            return False
        early = sum(
            1
            for result in viable
            if result.extinction_step is not None
            and result.extinction_step < _EARLY_EXTINCTION_STEPS
        )
        return early > _DEGENERATE_FRACTION * len(viable)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "seed": self.seed,
            "seed_bits": self.seed_bits,
            "traversal": self.traversal,
            "steps": self.steps,
            "grid_size": self.grid_size,
            "degenerate": self.degenerate,
            "results": [result.to_dict() for result in self.results],
        }


def board_size_for(geometry: str, grid_size: int) -> tuple[int, int, int | None]:
    """Resolve (width, height, patch_depth) for a topology's default sizing.

    Shared so the topology-preview endpoint can build a tiling at the exact size
    a sweep uses, which keeps a live seed preview consistent with the run.
    """
    variant = get_topology_variant_for_geometry(geometry)
    if geometry_uses_patch_depth(geometry):
        patch_depth = default_patch_depth_for_tiling_family(variant.tiling_family)
    else:
        patch_depth = None
    dimension = max(grid_size, minimum_grid_dimension_for_geometry(geometry))
    return dimension, dimension, patch_depth


def _run_single(
    geometry: str,
    *,
    rule: AutomatonRule,
    bits: str,
    traversal: str,
    steps: int,
    grid_size: int,
    live_state: int,
    include_states: bool,
) -> TopologyComparisonResult:
    variant = get_topology_variant_for_geometry(geometry)
    width, height, patch_depth = board_size_for(geometry, grid_size)
    board = empty_board(geometry, width, height, patch_depth)
    frame = topology_frame_for(board.topology)

    order = TRAVERSALS[traversal](frame)
    note: str | None = None
    if len(bits) > frame.cell_count:
        note = "seed-truncated"
    cells_by_id = paint_bits(order, bits, live=live_state)
    for cell_id, state in cells_by_id.items():
        board.set_state_for(cell_id, state)

    engine = SimulationEngine()
    populations = [population(board.cell_states)]
    change_rates: list[float] = []
    seen: dict[tuple[int, ...], int] = {tuple(board.cell_states): 0}
    period: int | None = None
    steps_run = 0
    current = board
    final_board = board
    divisor = max(1, frame.cell_count)

    for step in range(1, steps + 1):
        nxt = engine.step_board(current, rule)
        steps_run = step
        final_board = nxt
        populations.append(population(nxt.cell_states))
        change_rates.append(hamming(current.cell_states, nxt.cell_states) / divisor)
        key = tuple(nxt.cell_states)
        if key in seen:
            period = step - seen[key]
            break
        seen[key] = step
        current = nxt

    result = TopologyComparisonResult(
        geometry=geometry,
        tiling_family=variant.tiling_family,
        family=variant.family,
        cell_count=frame.cell_count,
        seed_bits=len(bits),
        seed_cells=len(cells_by_id),
        population=populations,
        change_rate=change_rates,
        classification=classify(populations, period),
        period=period,
        steps_run=steps_run,
        extinction_step=first_extinction_step(populations),
        note=note,
    )
    if include_states:
        result.topology_spec = dict(
            topology_spec_payload(geometry, width=width, height=height, patch_depth=patch_depth)
        )
        result.initial_cells_by_id = dict(cells_by_id)
        result.final_cells_by_id = final_board.states_by_id(omit_zero=True)
    return result


def compare_seed(
    *,
    seed: str,
    rule_name: str = DEFAULT_RULE,
    geometries: tuple[str, ...] | None = None,
    traversal: str = DEFAULT_TRAVERSAL,
    steps: int = DEFAULT_STEPS,
    grid_size: int = DEFAULT_GRID_SIZE,
    live_state: int = 1,
    include_states: bool = False,
) -> SeedComparison:
    """Sweep one seed under one rule across ``geometries`` (all tilings by default).

    The same rule is applied to every topology; the seed's live-cell count is
    held constant across topologies by the traversal mapping. A topology that
    fails to build is recorded with ``note="error"`` rather than aborting the
    sweep.
    """
    if traversal not in TRAVERSALS:
        raise ValueError(
            f"Unknown traversal {traversal!r}. Available: {', '.join(sorted(TRAVERSALS))}."
        )
    bits = normalize_bits(seed)
    rule = RuleRegistry().get(rule_name)
    target_geometries = geometries if geometries is not None else SUPPORTED_GEOMETRIES
    unknown = [geometry for geometry in target_geometries if geometry not in SUPPORTED_GEOMETRIES]
    if unknown:
        raise ValueError(f"Unknown geometry key(s): {', '.join(unknown)}.")

    comparison = SeedComparison(
        rule_name=rule.name,
        seed=seed,
        seed_bits=len(bits),
        traversal=traversal,
        steps=steps,
        grid_size=grid_size,
    )
    for geometry in target_geometries:
        try:
            result = _run_single(
                geometry,
                rule=rule,
                bits=bits,
                traversal=traversal,
                steps=steps,
                grid_size=grid_size,
                live_state=live_state,
                include_states=include_states,
            )
        except Exception as error:  # noqa: BLE001 - one bad tiling must not abort the sweep
            variant = get_topology_variant_for_geometry(geometry)  # geometry validated above
            result = TopologyComparisonResult(
                geometry=geometry,
                tiling_family=variant.tiling_family,
                family=variant.family,
                cell_count=0,
                seed_bits=len(bits),
                seed_cells=0,
                population=[],
                change_rate=[],
                classification="error",
                period=None,
                steps_run=0,
                extinction_step=None,
                note=f"error: {error}",
            )
        comparison.results.append(result)
    return comparison
