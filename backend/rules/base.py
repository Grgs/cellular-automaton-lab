from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from backend.payload_types import CellStatePayload

if TYPE_CHECKING:
    from backend.simulation.rule_context import RuleContext


@dataclass(frozen=True)
class CellStateDefinition:
    value: int
    label: str
    color: str
    paintable: bool = True

    def to_dict(self) -> CellStatePayload:
        return {
            "value": self.value,
            "label": self.label,
            "color": self.color,
            "paintable": self.paintable,
        }


RULE_PROTOCOL_UNIVERSAL_V1 = "universal-v1"


class RuleTopologyCompatibilityError(ValueError):
    """Raised when a rule is applied to a tiling family it does not support."""


class AutomatonRule(ABC):
    """Base contract for pluggable automaton rule modules."""

    name: str = "base"
    display_name: str = "Base Rule"
    description: str = "Abstract base rule."
    rule_protocol: str = RULE_PROTOCOL_UNIVERSAL_V1
    # Tiling families this rule is designed for, or ``None`` for a rule that
    # works on any topology. Universal Life-like and multistate rules stay
    # ``None`` so the same rule can be compared across many neighborhoods --
    # the app's core purpose. Only kind-specific rules (which look up
    # per-cell-kind thresholds and silently misbehave elsewhere) restrict
    # themselves to the families whose cell kinds they actually handle.
    compatible_tiling_families: tuple[str, ...] | None = None
    states: tuple[CellStateDefinition, ...] = (
        CellStateDefinition(0, "Dead", "#f8f1e5"),
        CellStateDefinition(1, "Live", "#1f2430"),
    )
    default_paint_state: int = 1
    randomize_weights: dict[int, float] | None = None

    @property
    def supports_randomize(self) -> bool:
        return bool(self.randomize_weights)

    @property
    def supports_all_topologies(self) -> bool:
        return self.compatible_tiling_families is None

    def supports_tiling_family(self, tiling_family: str) -> bool:
        return (
            self.compatible_tiling_families is None
            or tiling_family in self.compatible_tiling_families
        )

    def state_definitions(self) -> tuple[CellStateDefinition, ...]:
        return tuple(self.states)

    def state_values(self) -> set[int]:
        return {state.value for state in self.state_definitions()}

    def is_valid_state(self, state: int) -> bool:
        return state in self.state_values()

    @abstractmethod
    def next_state(self, ctx: RuleContext) -> int:
        """Return the next state for a cell using the universal rule context."""
