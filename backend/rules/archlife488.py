from __future__ import annotations

from backend.rules.base import AutomatonRule
from backend.rules.life_like import KindLifeRule


class ArchLife488Rule(KindLifeRule, AutomatonRule):
    name = "archlife488"
    display_name = "Mixed Life: Square-Octagon (4.8.8)"
    description = "Square-octagon Life rule with B3/S23 octagons and B2/S23 squares."
    kind_thresholds = {
        "square": (frozenset({2}), frozenset({2, 3})),
        "octagon": (frozenset({3}), frozenset({2, 3})),
    }
    default_kind = "octagon"
