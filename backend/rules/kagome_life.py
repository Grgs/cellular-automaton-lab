from __future__ import annotations

from backend.rules.base import AutomatonRule
from backend.rules.life_like import KindLifeRule


class KagomeLifeRule(KindLifeRule, AutomatonRule):
    name = "kagome-life"
    display_name = "Mixed Life: Triangle-Hexagon (B2/B234)"
    description = (
        "Triangle-hexagon Life rule with B2/S23 triangles and B234/S23 hexagons; "
        "used by Kagome and snub trihexagonal tilings."
    )
    compatible_tiling_families = ("trihexagonal-3-6-3-6", "archimedean-3-3-3-3-6")
    kind_thresholds = {
        "triangle": (frozenset({2}), frozenset({2, 3})),
        "hexagon": (frozenset({2, 3, 4}), frozenset({2, 3})),
    }
    kind_aliases = {
        "triangle-up": "triangle",
        "triangle-down": "triangle",
    }
    default_kind = "hexagon"
