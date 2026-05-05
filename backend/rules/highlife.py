from backend.rules.life_like import BinaryLifeRule


class HighLifeRule(BinaryLifeRule):
    name = "highlife"
    display_name = "Life: HighLife (B36/S23)"
    description = (
        "HighLife keeps Conway survival and adds the 6-neighbor birth that enables replicators."
    )
    births = frozenset({3, 6})
    survives = frozenset({2, 3})
