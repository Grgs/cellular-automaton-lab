from backend.rules.life_like import BinaryLifeRule


class ConwayLifeRule(BinaryLifeRule):
    name = "conway"
    display_name = "Life: Conway (B3/S23)"
    description = "Classic Game of Life with births on 3 neighbors and survival on 2 or 3."
    births = frozenset({3})
    survives = frozenset({2, 3})
