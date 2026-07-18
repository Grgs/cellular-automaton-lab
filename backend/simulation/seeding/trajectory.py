"""Shared, single-pass trajectory measurements for comparison consumers."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass

from backend.rules.base import AutomatonRule
from backend.simulation.engine import SimulationEngine
from backend.simulation.topology import SimulationBoard
from backend.simulation.topology_types import LatticeTopology


@dataclass(frozen=True)
class TrajectoryFrame:
    """One generation plus cumulative extinction and exact cycle information."""

    generation: int
    board: SimulationBoard
    population: int
    changed_cells: int
    extinction_step: int | None
    cycle_start: int | None
    period: int | None
    sparse_states: dict[str, int] | None = None
    delta: dict[str, int] | None = None


@dataclass(frozen=True)
class _FrameMeasurement:
    state_key: tuple[int, ...]
    population: int
    changed_cells: int
    sparse_states: dict[str, int] | None
    delta: dict[str, int] | None


def _measure_frame(
    topology: LatticeTopology,
    previous: Sequence[int] | None,
    current: Sequence[int],
    *,
    include_sparse: bool,
    include_delta: bool,
) -> _FrameMeasurement:
    """Fuse cycle-key, population, Hamming, sparse-state, and delta collection."""
    if previous is not None and len(previous) != len(current):
        raise ValueError("Trajectory state vectors must have the same length.")

    state_key: list[int] = []
    sparse_states: dict[str, int] | None = {} if include_sparse else None
    delta: dict[str, int] | None = {} if include_delta else None
    population = 0
    changed_cells = 0
    for index, raw_state in enumerate(current):
        state = int(raw_state)
        state_key.append(state)
        if state != 0:
            population += 1
            if sparse_states is not None:
                sparse_states[topology.cells[index].id] = state
        if previous is not None and previous[index] != state:
            changed_cells += 1
            if delta is not None:
                # State zero is explicit so consumers can remove a live cell.
                delta[topology.cells[index].id] = state
    return _FrameMeasurement(
        state_key=tuple(state_key),
        population=population,
        changed_cells=changed_cells,
        sparse_states=sparse_states,
        delta=delta,
    )


def iter_trajectory(
    board: SimulationBoard,
    rule: AutomatonRule,
    *,
    max_steps: int,
    include_sparse: bool = False,
    include_deltas: bool = False,
    stop_on_cycle: bool = False,
) -> Iterator[TrajectoryFrame]:
    """Yield generation zero and up to ``max_steps`` measured transitions.

    Exact state tuples are the cycle keys, so cycle detection remains safe in
    the presence of hash collisions. Metrics and requested sparse data are
    collected in one Python traversal of each generation's state vector.
    """
    if max_steps < 0:
        raise ValueError("max_steps must be non-negative.")

    engine = SimulationEngine()
    seen: dict[tuple[int, ...], int] = {}
    current = board
    previous_states: Sequence[int] | None = None
    extinction_step: int | None = None
    cycle_start: int | None = None
    period: int | None = None

    for generation in range(max_steps + 1):
        if generation > 0:
            current = engine.step_board(current, rule)
        measurement = _measure_frame(
            current.topology,
            previous_states,
            current.cell_states,
            include_sparse=include_sparse,
            include_delta=include_deltas,
        )
        if extinction_step is None and measurement.population == 0:
            extinction_step = generation
        if period is None:
            repeated_at = seen.get(measurement.state_key)
            if repeated_at is None:
                seen[measurement.state_key] = generation
            else:
                cycle_start = repeated_at
                period = generation - repeated_at

        yield TrajectoryFrame(
            generation=generation,
            board=current,
            population=measurement.population,
            changed_cells=measurement.changed_cells,
            extinction_step=extinction_step,
            cycle_start=cycle_start,
            period=period,
            sparse_states=measurement.sparse_states,
            delta=measurement.delta,
        )
        if stop_on_cycle and period is not None:
            return
        # Reuse the immutable exact-cycle key as the previous vector. Besides
        # avoiding another copy, it keeps previous-side delta accounting stable.
        previous_states = measurement.state_key


__all__ = ["TrajectoryFrame", "iter_trajectory"]
