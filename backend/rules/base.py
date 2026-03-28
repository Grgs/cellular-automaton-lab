from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.simulation.rule_context import RuleContext


@dataclass(frozen=True)
class CellStateDefinition:
    value: int
    label: str
    color: str
    paintable: bool = True

    def to_dict(self) -> dict[str, int | str | bool]:
        return {
            "value": self.value,
            "label": self.label,
            "color": self.color,
            "paintable": self.paintable,
        }


RULE_PROTOCOL_UNIVERSAL_V1 = "universal-v1"


class AutomatonRule(ABC):
    """Base contract for pluggable automaton rule modules."""

    name: str = "base"
    display_name: str = "Base Rule"
    description: str = "Abstract base rule."
    rule_protocol: str = RULE_PROTOCOL_UNIVERSAL_V1
    supports_all_topologies: bool = True
    states: tuple[CellStateDefinition, ...] = (
        CellStateDefinition(0, "Dead", "#f8f1e5"),
        CellStateDefinition(1, "Live", "#1f2430"),
    )
    default_paint_state: int = 1
    randomize_weights: dict[int, float] | None = None

    @property
    def supports_randomize(self) -> bool:
        return bool(self.randomize_weights)

    def state_definitions(self) -> tuple[CellStateDefinition, ...]:
        return tuple(self.states)

    def state_values(self) -> set[int]:
        return {state.value for state in self.state_definitions()}

    def is_valid_state(self, state: int) -> bool:
        return state in self.state_values()

    @abstractmethod
    def next_state(self, ctx: RuleContext) -> int:
        """Return the next state for a cell using the universal rule context."""
