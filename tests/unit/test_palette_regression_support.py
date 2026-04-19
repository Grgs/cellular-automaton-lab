from __future__ import annotations

import unittest

from tests.e2e.browser_support.palette_regression import (
    iter_palette_fixture_cases,
    load_palette_manifest,
    palette_manifest_path,
)


class PaletteRegressionSupportTests(unittest.TestCase):
    def test_manifest_declares_palette_families_with_browser_coverage(self) -> None:
        manifest = load_palette_manifest()

        self.assertEqual(
            palette_manifest_path().name,
            "family-dead-palette-manifest.json",
        )
        self.assertEqual(
            [family["geometry"] for family in manifest["families"] if "browserAliasCoverage" in family],
            [
                "tuebingen-triangle",
                "robinson-triangles",
                "hat-monotile",
                "chair",
                "dodecagonal-square-triangle",
                "pinwheel",
                "shield",
            ],
        )

    def test_iter_palette_fixture_cases_uses_manifest_selector_fields(self) -> None:
        cases = {case["family"]: case for case in iter_palette_fixture_cases()}

        self.assertEqual(cases["chair"]["selector_fields"], ("orientation_token",))
        self.assertEqual(cases["shield"]["selector_fields"], ("kind",))
        self.assertEqual(cases["pinwheel"]["selector_fields"], ("chirality_token",))
        self.assertTrue(cases["shield"]["fixture_path"].endswith("shield-depth-3.json"))


if __name__ == "__main__":
    unittest.main()
