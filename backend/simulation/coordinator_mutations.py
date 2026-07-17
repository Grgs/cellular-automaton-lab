from __future__ import annotations

from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


class SimulationCoordinatorMutationDispatcher:
    """Runs coordinator mutations with the correct persistence behavior."""

    def __init__(
        self,
        *,
        flush_immediately: Callable[[], None],
        schedule_deferred_persist: Callable[[], None],
    ) -> None:
        self._flush_immediately = flush_immediately
        self._schedule_deferred_persist = schedule_deferred_persist

    def run_immediate(
        self,
        action: Callable[P, R],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        result = action(*args, **kwargs)
        self._flush_immediately()
        return result

    def run_deferred(
        self,
        action: Callable[P, R],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        result = action(*args, **kwargs)
        self._schedule_deferred_persist()
        return result
