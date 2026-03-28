from __future__ import annotations

import importlib
import inspect
import pkgutil

from backend.payload_types import RuleDefinitionPayload
from backend.rules.base import AutomatonRule
from backend.simulation.models import RuleSnapshot
from backend.simulation.topology_catalog import (
    GEOMETRY_DEFAULT_RULES,
    SQUARE_GEOMETRY,
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
        rules: dict[str, AutomatonRule] = {}

        for module_info in pkgutil.iter_modules(__path__):
            if module_info.name == "base":
                continue

            module = importlib.import_module(f"{__name__}.{module_info.name}")
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ != module.__name__:
                    continue
                if not issubclass(obj, AutomatonRule) or obj is AutomatonRule:
                    continue

                rule = obj()
                if rule.name == AutomatonRule.name:
                    continue
                rules[rule.name] = rule

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
