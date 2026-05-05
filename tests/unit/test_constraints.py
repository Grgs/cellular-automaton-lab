import sys
import unittest
from pathlib import Path

try:
    from backend.rules.constraints import normalize_rule_dimensions, rule_requires_square_dimensions
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.rules.constraints import normalize_rule_dimensions, rule_requires_square_dimensions


class RuleConstraintTests(unittest.TestCase):
    def test_rule_requires_square_dimensions_returns_false_for_all_rules(self) -> None:
        whirlpool_like = type("RuleLike", (), {"name": "whirlpool"})()
        non_square_like = type("RuleLike", (), {"name": "conway"})()

        self.assertFalse(rule_requires_square_dimensions("whirlpool"))
        self.assertFalse(rule_requires_square_dimensions("hexwhirlpool"))
        self.assertFalse(rule_requires_square_dimensions("conway"))
        self.assertFalse(rule_requires_square_dimensions(whirlpool_like))
        self.assertFalse(rule_requires_square_dimensions(non_square_like))

    def test_normalize_rule_dimensions_preserves_requested_dimensions(self) -> None:
        self.assertEqual(normalize_rule_dimensions("conway", 9, 5), (9, 5))
        self.assertEqual(normalize_rule_dimensions("whirlpool", None, None), (None, None))
        self.assertEqual(normalize_rule_dimensions("whirlpool", None, 7), (None, 7))
        self.assertEqual(normalize_rule_dimensions("hexwhirlpool", 5, None), (5, None))
        self.assertEqual(normalize_rule_dimensions("whirlpool", 7, 5), (7, 5))
        self.assertEqual(normalize_rule_dimensions("whirlpool", 4, 9), (4, 9))
        self.assertEqual(normalize_rule_dimensions(type("RuleLike", (), {"name": "wireworld"})(), 7, None), (7, None))


if __name__ == "__main__":
    unittest.main()
