from backend.rules.life_like import BinaryLifeRule


class HexLifeRule(BinaryLifeRule):
    name = "hexlife"
    display_name = "Life: Hex (B2/S34)"
    description = "Hexagonal Life with births on 2 neighbors and survival on 3 or 4."
    births = frozenset({2})
    survives = frozenset({3, 4})
