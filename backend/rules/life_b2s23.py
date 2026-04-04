from __future__ import annotations

from backend.rules.life_like import BinaryLifeRule


class LifeB2S23Rule(BinaryLifeRule):
    name = "life-b2-s23"
    display_name = "Life: B2/S23"
    description = "Binary Life-like rule with births on 2 neighbors and survival on 2 or 3."
    births = frozenset({2})
    survives = frozenset({2, 3})
