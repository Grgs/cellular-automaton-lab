"""Parse and run a compare request from an untrusted JSON payload.

Shared by the Flask route and the standalone browser runtime so both surfaces
validate and bound the request identically. Validation failures raise
``ValueError`` for the host layer to turn into a 4xx response.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from backend.simulation.seeding.comparison import (
    DEFAULT_FILMSTRIP_FRAMES,
    DEFAULT_FILMSTRIP_GRID_SIZE,
    DEFAULT_GRID_SIZE,
    DEFAULT_RULE,
    DEFAULT_STEPS,
    MAX_FILMSTRIP_FRAMES,
    MAX_FILMSTRIP_TILINGS,
    compare_seed,
    run_seed_filmstrip,
)
from backend.simulation.seeding.shapes import NAMED_PATTERNS
from backend.simulation.seeding.traversal import DEFAULT_TRAVERSAL, TRAVERSALS

# Guard rails so a single request cannot ask for an unboundedly large sweep.
_MAX_STEPS = 500
_MAX_GRID_SIZE = 64
_MAX_SEED_LENGTH = 4096


@dataclass(frozen=True)
class CompareRequest:
    seed: str
    rule_name: str
    traversal: str
    steps: int
    grid_size: int
    geometries: tuple[str, ...] | None
    include_states: bool
    pattern: str | None


def _bounded_int(value: Any, *, default: int, low: int, high: int, name: str) -> int:
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"'{name}' must be an integer.") from error
    if parsed < low or parsed > high:
        raise ValueError(f"'{name}' must be between {low} and {high}.")
    return parsed


def parse_compare_request(payload: Mapping[str, Any]) -> CompareRequest:
    pattern_value = payload.get("pattern")
    pattern = pattern_value if isinstance(pattern_value, str) and pattern_value else None
    if pattern is not None and pattern not in NAMED_PATTERNS:
        raise ValueError(
            f"Unknown pattern {pattern!r}. Available: {', '.join(sorted(NAMED_PATTERNS))}."
        )

    seed_value = payload.get("seed")
    if pattern is None:
        # Bit-string mode requires a seed; in pattern mode the seed is ignored.
        if not isinstance(seed_value, str) or not seed_value.strip():
            raise ValueError("'seed' must be a non-empty string.")
        seed = seed_value
    else:
        seed = seed_value if isinstance(seed_value, str) else ""
    if len(seed) > _MAX_SEED_LENGTH:
        raise ValueError(f"'seed' must be at most {_MAX_SEED_LENGTH} characters.")

    rule_value = payload.get("rule")
    rule_name = rule_value if isinstance(rule_value, str) and rule_value else DEFAULT_RULE

    traversal_value = payload.get("traversal")
    traversal = (
        traversal_value
        if isinstance(traversal_value, str) and traversal_value
        else DEFAULT_TRAVERSAL
    )
    if traversal not in TRAVERSALS:
        raise ValueError(
            f"Unknown traversal {traversal!r}. Available: {', '.join(sorted(TRAVERSALS))}."
        )

    steps = _bounded_int(
        payload.get("steps"), default=DEFAULT_STEPS, low=1, high=_MAX_STEPS, name="steps"
    )
    grid_size = _bounded_int(
        payload.get("grid_size"),
        default=DEFAULT_GRID_SIZE,
        low=2,
        high=_MAX_GRID_SIZE,
        name="grid_size",
    )

    geometries_value = payload.get("geometries")
    geometries: tuple[str, ...] | None = None
    if geometries_value is not None:
        if not isinstance(geometries_value, (list, tuple)):
            raise ValueError("'geometries' must be a list of geometry keys.")
        collected = tuple(item for item in geometries_value if isinstance(item, str) and item)
        if not collected:
            raise ValueError("'geometries' must contain at least one geometry key.")
        geometries = collected

    return CompareRequest(
        seed=seed,
        rule_name=rule_name,
        traversal=traversal,
        steps=steps,
        grid_size=grid_size,
        geometries=geometries,
        include_states=bool(payload.get("include_states", False)),
        pattern=pattern,
    )


def run_compare_request(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate ``payload``, run the sweep, and return the serialised comparison."""
    request = parse_compare_request(payload)
    comparison = compare_seed(
        seed=request.seed,
        rule_name=request.rule_name,
        geometries=request.geometries,
        traversal=request.traversal,
        steps=request.steps,
        grid_size=request.grid_size,
        include_states=request.include_states,
        pattern=request.pattern,
    )
    return comparison.to_dict()


@dataclass(frozen=True)
class FilmstripRequest:
    seed: str
    rule_name: str
    traversal: str
    frame_count: int
    grid_size: int
    geometries: tuple[str, ...]
    pattern: str | None


def parse_filmstrip_request(payload: Mapping[str, Any]) -> FilmstripRequest:
    base = parse_compare_request(payload)

    # The live filmstrip runs an explicit, small set of tilings side by side,
    # so geometries are required (not an optional "all tilings" sweep) and
    # capped to keep per-frame compute and payload bounded.
    if base.geometries is None:
        raise ValueError("'geometries' must list the tilings to run side by side.")
    if len(base.geometries) > MAX_FILMSTRIP_TILINGS:
        raise ValueError(
            f"'geometries' must list at most {MAX_FILMSTRIP_TILINGS} tilings for side-by-side play."
        )

    frame_count = _bounded_int(
        payload.get("frames"),
        default=DEFAULT_FILMSTRIP_FRAMES,
        low=1,
        high=MAX_FILMSTRIP_FRAMES,
        name="frames",
    )
    grid_size = _bounded_int(
        payload.get("grid_size"),
        default=DEFAULT_FILMSTRIP_GRID_SIZE,
        low=2,
        high=_MAX_GRID_SIZE,
        name="grid_size",
    )

    return FilmstripRequest(
        seed=base.seed,
        rule_name=base.rule_name,
        traversal=base.traversal,
        frame_count=frame_count,
        grid_size=grid_size,
        geometries=base.geometries,
        pattern=base.pattern,
    )


def run_filmstrip_request(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate ``payload``, run the synchronized filmstrip, and serialise it."""
    request = parse_filmstrip_request(payload)
    filmstrip = run_seed_filmstrip(
        seed=request.seed,
        rule_name=request.rule_name,
        geometries=request.geometries,
        traversal=request.traversal,
        frame_count=request.frame_count,
        grid_size=request.grid_size,
        pattern=request.pattern,
    )
    return filmstrip.to_dict()
