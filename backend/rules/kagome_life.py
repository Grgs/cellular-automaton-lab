from __future__ import annotations

from backend.rules.base import AutomatonRule
from backend.rules.life_like import KindLifeRule


class KagomeLifeRule(KindLifeRule, AutomatonRule):
    name = "kagome-life"
    display_name = "Mixed Life: Kagome (3.6.3.6)"
    description = "Mixed-tile Life rule with B3/S23 hexagons and B2/S23 triangles."
    kind_thresholds = {
        "triangle": (frozenset({2}), frozenset({2, 3})),
        "hexagon": (frozenset({2, 3, 4}), frozenset({2, 3})),
    }
    kind_aliases = {
        "triangle-up": "triangle",
        "triangle-down": "triangle",
    }
    default_kind = "hexagon"
