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
from backend.simulation.rule_context_frames import TopologyFrame, topology_frame_for
from backend.simulation.seeding.metrics import (
    classify,
    first_extinction_step,
    hamming,
    population,
)
from backend.simulation.seeding.shapes import NAMED_PATTERNS, place_pattern
from backend.simulation.seeding.traversal import (
    DEFAULT_TRAVERSAL,
    TRAVERSALS,
    normalize_bits,
    paint_bits,
)
from backend.simulation.topology import SimulationBoard, empty_board
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

# Live side-by-side defaults. The filmstrip captures every generation's board
# state for a handful of tilings, so it is deliberately small: a few tilings, a
# bounded frame count, and a modest grid keep the payload and compute in check.
DEFAULT_FILMSTRIP_FRAMES = 60
MAX_FILMSTRIP_FRAMES = 240
DEFAULT_FILMSTRIP_GRID_SIZE = 12
MAX_FILMSTRIP_TILINGS = 6

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


@dataclass(frozen=True)
class _SeededBoard:
    """A built, seeded board plus the seeding metadata both callers need."""

    board: SimulationBoard
    frame: TopologyFrame
    cells_by_id: dict[str, int]
    note: str | None
    seed_size: int
    width: int
    height: int
    patch_depth: int | None


def _build_seeded_board(
    geometry: str,
    *,
    bits: str,
    traversal: str,
    grid_size: int,
    live_state: int,
    pattern: str | None,
) -> _SeededBoard:
    """Build a topology board and paint the seed onto it.

    Shared by the metrics sweep (``_run_single``) and the live filmstrip
    (``run_seed_filmstrip``) so both seed every topology identically.
    """
    width, height, patch_depth = board_size_for(geometry, grid_size)
    board = empty_board(geometry, width, height, patch_depth)
    frame = topology_frame_for(board.topology)

    note: str | None = None
    if pattern is not None:
        # Policy A: place a recognisable shape geometrically (nearest cell).
        seed_size = len(NAMED_PATTERNS[pattern])
        cells_by_id = {
            cell_id: live_state for cell_id in place_pattern(frame, NAMED_PATTERNS[pattern])
        }
    else:
        order = TRAVERSALS[traversal](frame)
        if len(bits) > frame.cell_count:
            note = "seed-truncated"
        seed_size = len(bits)
        cells_by_id = paint_bits(order, bits, live=live_state)
    for cell_id, state in cells_by_id.items():
        board.set_state_for(cell_id, state)
    return _SeededBoard(
        board=board,
        frame=frame,
        cells_by_id=cells_by_id,
        note=note,
        seed_size=seed_size,
        width=width,
        height=height,
        patch_depth=patch_depth,
    )


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
    pattern: str | None,
) -> TopologyComparisonResult:
    variant = get_topology_variant_for_geometry(geometry)
    seeded = _build_seeded_board(
        geometry,
        bits=bits,
        traversal=traversal,
        grid_size=grid_size,
        live_state=live_state,
        pattern=pattern,
    )
    board = seeded.board
    frame = seeded.frame
    cells_by_id = seeded.cells_by_id
    note = seeded.note
    seed_size = seeded.seed_size
    width, height, patch_depth = seeded.width, seeded.height, seeded.patch_depth

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
        seed_bits=seed_size,
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
    pattern: str | None = None,
) -> SeedComparison:
    """Sweep one seed under one rule across ``geometries`` (all tilings by default).

    The same rule is applied to every topology. By default the seed is a bit
    string mapped onto each tiling by the ``traversal`` (preserving live-cell
    count). When ``pattern`` names a shape, that recognisable shape is placed
    geometrically on each tiling instead (Policy A), preserving its 2-D form. A
    topology that fails to build is recorded with ``note="error"`` rather than
    aborting the sweep.
    """
    if traversal not in TRAVERSALS:
        raise ValueError(
            f"Unknown traversal {traversal!r}. Available: {', '.join(sorted(TRAVERSALS))}."
        )
    if pattern is not None and pattern not in NAMED_PATTERNS:
        raise ValueError(
            f"Unknown pattern {pattern!r}. Available: {', '.join(sorted(NAMED_PATTERNS))}."
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
                pattern=pattern,
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


@dataclass
class TopologyFilmstrip:
    """Per-generation board states for one tiling, for live side-by-side play.

    ``topology`` is the full geometry payload (cells/vertices) sent once so the
    client can render the board; ``frames`` is one sparse live-cell map per
    generation (``frames[0]`` is the seed), all tilings sharing the same frame
    count so a single client clock keeps them synchronised.
    """

    geometry: str
    label: str
    tiling_family: str
    family: str
    cell_count: int
    topology: dict[str, Any]
    topology_spec: dict[str, Any]
    frames: list[dict[str, int]]
    extinction_step: int | None
    period: int | None
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "geometry": self.geometry,
            "label": self.label,
            "tiling_family": self.tiling_family,
            "family": self.family,
            "cell_count": self.cell_count,
            "topology": self.topology,
            "topology_spec": self.topology_spec,
            "frames": self.frames,
            "extinction_step": self.extinction_step,
            "period": self.period,
            "note": self.note,
        }


@dataclass
class SeedFilmstrip:
    """A synchronized live run of one seed and rule across a few tilings."""

    rule_name: str
    seed: str
    traversal: str
    frame_count: int
    grid_size: int
    tilings: list[TopologyFilmstrip] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "seed": self.seed,
            "traversal": self.traversal,
            "frame_count": self.frame_count,
            "grid_size": self.grid_size,
            "tilings": [tiling.to_dict() for tiling in self.tilings],
        }


def _run_single_filmstrip(
    geometry: str,
    *,
    rule: AutomatonRule,
    bits: str,
    traversal: str,
    frame_count: int,
    grid_size: int,
    live_state: int,
    pattern: str | None,
) -> TopologyFilmstrip:
    variant = get_topology_variant_for_geometry(geometry)
    seeded = _build_seeded_board(
        geometry,
        bits=bits,
        traversal=traversal,
        grid_size=grid_size,
        live_state=live_state,
        pattern=pattern,
    )
    board = seeded.board

    engine = SimulationEngine()
    frames: list[dict[str, int]] = [board.states_by_id(omit_zero=True)]
    seen: dict[tuple[int, ...], int] = {tuple(board.cell_states): 0}
    period: int | None = None
    extinction_step: int | None = None
    current = board
    # Every tiling captures the same number of frames so the client can advance
    # them on one shared clock. A board that reaches a fixed point, cycle, or
    # extinction simply repeats; those frames are cheap (sparse, often empty).
    for step in range(1, frame_count):
        nxt = engine.step_board(current, rule)
        frames.append(nxt.states_by_id(omit_zero=True))
        if extinction_step is None and population(nxt.cell_states) == 0:
            extinction_step = step
        if period is None:
            key = tuple(nxt.cell_states)
            if key in seen:
                period = step - seen[key]
            else:
                seen[key] = step
        current = nxt

    return TopologyFilmstrip(
        geometry=geometry,
        label=variant.label,
        tiling_family=variant.tiling_family,
        family=variant.family,
        cell_count=seeded.frame.cell_count,
        topology=dict(board.topology.to_dict()),
        topology_spec=dict(
            topology_spec_payload(
                geometry,
                width=seeded.width,
                height=seeded.height,
                patch_depth=seeded.patch_depth,
            )
        ),
        frames=frames,
        extinction_step=extinction_step,
        period=period,
        note=seeded.note,
    )


def run_seed_filmstrip(
    *,
    seed: str,
    rule_name: str = DEFAULT_RULE,
    geometries: tuple[str, ...],
    traversal: str = DEFAULT_TRAVERSAL,
    frame_count: int = DEFAULT_FILMSTRIP_FRAMES,
    grid_size: int = DEFAULT_FILMSTRIP_GRID_SIZE,
    live_state: int = 1,
    pattern: str | None = None,
) -> SeedFilmstrip:
    """Run one seed under one rule across a few tilings, capturing every frame.

    Unlike ``compare_seed`` (which sweeps all tilings for aggregate metrics),
    this keeps the full per-generation board state for a small, explicit set of
    tilings so they can be played back synchronously side by side. A tiling that
    fails to build is recorded with ``note="error"`` and empty frames rather
    than aborting the run.
    """
    if traversal not in TRAVERSALS:
        raise ValueError(
            f"Unknown traversal {traversal!r}. Available: {', '.join(sorted(TRAVERSALS))}."
        )
    if pattern is not None and pattern not in NAMED_PATTERNS:
        raise ValueError(
            f"Unknown pattern {pattern!r}. Available: {', '.join(sorted(NAMED_PATTERNS))}."
        )
    if not geometries:
        raise ValueError("At least one geometry is required for a filmstrip.")
    if len(geometries) > MAX_FILMSTRIP_TILINGS:
        raise ValueError(f"At most {MAX_FILMSTRIP_TILINGS} tilings can run side by side.")
    unknown = [geometry for geometry in geometries if geometry not in SUPPORTED_GEOMETRIES]
    if unknown:
        raise ValueError(f"Unknown geometry key(s): {', '.join(unknown)}.")
    resolved_frame_count = max(1, min(int(frame_count), MAX_FILMSTRIP_FRAMES))

    bits = normalize_bits(seed)
    rule = RuleRegistry().get(rule_name)
    filmstrip = SeedFilmstrip(
        rule_name=rule.name,
        seed=seed,
        traversal=traversal,
        frame_count=resolved_frame_count,
        grid_size=grid_size,
    )
    for geometry in geometries:
        try:
            tiling = _run_single_filmstrip(
                geometry,
                rule=rule,
                bits=bits,
                traversal=traversal,
                frame_count=resolved_frame_count,
                grid_size=grid_size,
                live_state=live_state,
                pattern=pattern,
            )
        except Exception as error:  # noqa: BLE001 - one bad tiling must not abort the run
            variant = get_topology_variant_for_geometry(geometry)  # geometry validated above
            tiling = TopologyFilmstrip(
                geometry=geometry,
                label=variant.label,
                tiling_family=variant.tiling_family,
                family=variant.family,
                cell_count=0,
                topology={},
                topology_spec={},
                frames=[],
                extinction_step=None,
                period=None,
                note=f"error: {error}",
            )
        filmstrip.tilings.append(tiling)
    return filmstrip
