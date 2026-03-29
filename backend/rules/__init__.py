from __future__ import annotations

from backend.payload_types import RuleDefinitionPayload
from backend.rules.archlife488 import ArchLife488Rule
from backend.rules.archlife_extended import (
    ArchLife31212Rule,
    ArchLife33336Rule,
    ArchLife33344Rule,
    ArchLife33434Rule,
    ArchLife3464Rule,
    ArchLife4612Rule,
)
from backend.rules.base import AutomatonRule
from backend.rules.conway import ConwayLifeRule
from backend.rules.highlife import HighLifeRule
from backend.rules.hexlife import HexLifeRule
from backend.rules.kagome_life import KagomeLifeRule
from backend.rules.life_b2s23 import LifeB2S23Rule
from backend.rules.penrose_greenberg_hastings import PenroseGreenbergHastingsRule
from backend.rules.trilife import TriLifeRule
from backend.rules.whirlpool import WhirlpoolRule
from backend.rules.wireworld import WireWorldRule
from backend.simulation.models import RuleSnapshot
from backend.simulation.topology_catalog import (
    GEOMETRY_DEFAULT_RULES,
    SQUARE_GEOMETRY,
)

RULE_TYPES: tuple[type[AutomatonRule], ...] = (
    ArchLife31212Rule,
    ArchLife33336Rule,
    ArchLife33344Rule,
    ArchLife33434Rule,
    ArchLife3464Rule,
    ArchLife4612Rule,
    ArchLife488Rule,
    ConwayLifeRule,
    HighLifeRule,
    HexLifeRule,
    KagomeLifeRule,
    LifeB2S23Rule,
    PenroseGreenbergHastingsRule,
    TriLifeRule,
    WhirlpoolRule,
    WireWorldRule,
)


class RuleRegistry:
    """Loads rule implementations from modules in backend.rules."""

    _ALIASES = {
        "penrose-life": "life-b2-s23",
        "penrose-vertex-life": "conway",
        "hexwhirlpool": "whirlpool",
    }

    def __init__(self) -> None:
        self._rules = self._discover_rules()
        if not self._rules:
            raise RuntimeError("No rule modules were discovered.")

    def _discover_rules(self) -> dict[str, AutomatonRule]:
        rules = {
            rule.name: rule
            for rule in (rule_type() for rule_type in RULE_TYPES)
            if rule.name != AutomatonRule.name
        }
        return dict(sorted(rules.items(), key=lambda item: item[1].display_name.lower()))

    def has(self, name: str) -> bool:
        return name in self._rules or name in self._ALIASES

    def get(self, name: str | None) -> AutomatonRule:
        if name:
            resolved_name = self._ALIASES.get(name, name)
            if resolved_name in self._rules:
                return self._rules[resolved_name]
        return self.default_for_geometry(SQUARE_GEOMETRY)

    def default_for_geometry(self, geometry: str) -> AutomatonRule:
        default_name = GEOMETRY_DEFAULT_RULES.get(geometry)
        if default_name and default_name in self._rules:
            return self._rules[default_name]

        square_default = GEOMETRY_DEFAULT_RULES.get(SQUARE_GEOMETRY)
        if square_default and square_default in self._rules:
            return self._rules[square_default]

        raise RuntimeError(f"No rule modules support geometry '{geometry}'.")

    def describe_rules(self) -> list[RuleDefinitionPayload]:
        return [
            RuleSnapshot.from_rule(rule).to_dict()
            for rule in self._rules.values()
        ]
