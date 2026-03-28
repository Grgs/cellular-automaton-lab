from backend.rules.life_like import BinaryLifeRule


class TriLifeRule(BinaryLifeRule):
    name = "trilife"
    display_name = "Life: Triangle (B4/S345)"
    description = "Triangular Life with births on 4 touching neighbors and survival on 3, 4, or 5."
    births = frozenset({4})
    survives = frozenset({3, 4, 5})
