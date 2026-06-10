"""Measurement helpers that turn a stepped trajectory into comparison metrics.

These are deliberately rule-agnostic. "Live" means any non-zero cell state, so
the same metrics describe binary Life-like rules and multi-state rules
(Wireworld, Whirlpool, Greenberg-Hastings) without special-casing.
"""

from __future__ import annotations

from collections.abc import Sequence

# Classification labels emitted by :func:`classify`.
EXTINCT = "extinct"
STILL_LIFE = "still-life"
UNSETTLED = "unsettled"


def population(states: Sequence[int]) -> int:
    """Number of non-zero (live) cells."""
    return sum(1 for state in states if state)


def hamming(previous: Sequence[int], current: Sequence[int]) -> int:
    """Count of cells whose state changed between two steps."""
    return sum(1 for before, after in zip(previous, current, strict=True) if before != after)


def first_extinction_step(populations: Sequence[int]) -> int | None:
    """Index of the first step at which the population reaches zero, if any."""
    for step, value in enumerate(populations):
        if value == 0:
            return step
    return None


def classify(populations: Sequence[int], period: int | None) -> str:
    """Label the end state from the population trace and detected period.

    - empty final board -> ``extinct``
    - period 1 with survivors -> ``still-life``
    - period > 1 -> ``oscillator-p{period}``
    - no repeat within the step budget -> ``unsettled``
    """
    if not populations or populations[-1] == 0:
        return EXTINCT
    if period == 1:
        return STILL_LIFE
    if period is not None and period > 1:
        return f"oscillator-p{period}"
    return UNSETTLED
