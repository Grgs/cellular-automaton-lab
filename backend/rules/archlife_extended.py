from __future__ import annotations

from backend.rules.base import AutomatonRule
from backend.rules.life_like import KindLifeRule


class ArchLife31212Rule(KindLifeRule, AutomatonRule):
    name = "archlife-3-12-12"
    display_name = "Mixed Life: Truncated Hexagonal (3.12.12)"
    description = "Truncated hexagonal Life rule with B2/S23 triangles and B34/S23 dodecagons."
    kind_thresholds = {
        "triangle": (frozenset({2}), frozenset({2, 3})),
        "dodecagon": (frozenset({3, 4}), frozenset({2, 3})),
    }
    default_kind = "dodecagon"


class ArchLife3464Rule(KindLifeRule, AutomatonRule):
    name = "archlife-3-4-6-4"
    display_name = "Mixed Life: Rhombitrihexagonal (3.4.6.4)"
    description = "Rhombitrihexagonal Life rule with B2/S23 triangles and squares, and B3/S23 hexagons."
    kind_thresholds = {
        "triangle": (frozenset({2}), frozenset({2, 3})),
        "square": (frozenset({2}), frozenset({2, 3})),
        "hexagon": (frozenset({3}), frozenset({2, 3})),
    }
    default_kind = "hexagon"


class ArchLife4612Rule(KindLifeRule, AutomatonRule):
    name = "archlife-4-6-12"
    display_name = "Mixed Life: Truncated Trihexagonal (4.6.12)"
    description = "Truncated trihexagonal Life rule with B2/S23 squares, B3/S23 hexagons, and B34/S23 dodecagons."
    kind_thresholds = {
        "square": (frozenset({2}), frozenset({2, 3})),
        "hexagon": (frozenset({3}), frozenset({2, 3})),
        "dodecagon": (frozenset({3, 4}), frozenset({2, 3})),
    }
    default_kind = "dodecagon"


class ArchLife33434Rule(KindLifeRule, AutomatonRule):
    name = "archlife-3-3-4-3-4"
    display_name = "Mixed Life: Snub Square (3.3.4.3.4)"
    description = "Snub square Life rule with B2/S23 triangles and B3/S23 squares."
    kind_thresholds = {
        "triangle": (frozenset({2}), frozenset({2, 3})),
        "square": (frozenset({3}), frozenset({2, 3})),
    }
    default_kind = "square"


class ArchLife33344Rule(KindLifeRule, AutomatonRule):
    name = "archlife-3-3-3-4-4"
    display_name = "Mixed Life: Elongated Triangular (3.3.3.4.4)"
    description = "Elongated triangular Life rule with B2/S23 triangles and B23/S23 squares."
    kind_thresholds = {
        "triangle": (frozenset({2}), frozenset({2, 3})),
        "square": (frozenset({2, 3}), frozenset({2, 3})),
    }
    default_kind = "square"


class ArchLife33336Rule(KindLifeRule, AutomatonRule):
    name = "archlife-3-3-3-3-6"
    display_name = "Mixed Life: Snub Trihexagonal (3.3.3.3.6)"
    description = "Snub trihexagonal Life rule with B2/S23 triangles and B234/S23 hexagons."
    kind_thresholds = {
        "triangle": (frozenset({2}), frozenset({2, 3})),
        "hexagon": (frozenset({2, 3, 4}), frozenset({2, 3})),
    }
    default_kind = "hexagon"
