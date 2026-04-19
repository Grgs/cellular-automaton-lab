from __future__ import annotations

import unittest

from tests.e2e.browser_support.palette_regression import infer_palette_selector_fields


class PaletteRegressionSupportTests(unittest.TestCase):
    def test_infer_selector_fields_prefers_kind_and_chirality_when_present(self) -> None:
        cells = [
            {"kind": "triangle", "chirality_token": "left", "orientation_token": "0"},
            {"kind": "triangle", "chirality_token": "right", "orientation_token": "30"},
            {"kind": "square", "chirality_token": "left", "orientation_token": "60"},
        ]

        self.assertEqual(infer_palette_selector_fields(cells), ("kind", "chirality_token"))

    def test_infer_selector_fields_uses_orientation_when_it_is_the_only_variant_axis(self) -> None:
        cells = [
            {"kind": "chair", "orientation_token": "0"},
            {"kind": "chair", "orientation_token": "1"},
            {"kind": "chair", "orientation_token": "2"},
        ]

        self.assertEqual(infer_palette_selector_fields(cells), ("orientation_token",))

    def test_infer_selector_fields_returns_empty_tuple_for_single_variant_fixtures(self) -> None:
        cells = [
            {"kind": "spectre"},
            {"kind": "spectre"},
        ]

        self.assertEqual(infer_palette_selector_fields(cells), ())


if __name__ == "__main__":
    unittest.main()
