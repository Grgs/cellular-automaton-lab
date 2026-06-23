from __future__ import annotations

import unittest

from tools.render_review.browser_support.palette_regression import (
    iter_palette_fixture_cases,
    load_palette_manifest,
    palette_manifest_path,
)


class PaletteRegressionSupportTests(unittest.TestCase):
    def test_manifest_path_is_the_dead_palette_manifest(self) -> None:
        self.assertEqual(
            palette_manifest_path().name,
            "family-dead-palette-manifest.json",
        )

    def test_every_browser_coverage_entry_is_well_formed(self) -> None:
        # The manifest is the single source of truth for which families get a
        # browser-visible palette-alias gate. Rather than pinning the membership
        # list (which forced a manual, order-sensitive edit every time a family
        # gained coverage), validate the shape of each entry so adding a family
        # needs no edit here. The Playwright suite derives one alias test per
        # entry, so each one must name a real fixture and at least one selector
        # field.
        manifest = load_palette_manifest()
        repo_root = palette_manifest_path().parents[2]

        covered = [family for family in manifest["families"] if "browserAliasCoverage" in family]
        self.assertTrue(covered, "expected at least one family with browserAliasCoverage")

        for family in covered:
            geometry = family.get("geometry")
            coverage = family["browserAliasCoverage"]
            with self.subTest(geometry=geometry):
                self.assertIsInstance(geometry, str)

                fixture_path = coverage.get("fixturePath")
                self.assertIsInstance(fixture_path, str)
                self.assertTrue(
                    (repo_root / fixture_path).is_file(),
                    f"{geometry}: browserAliasCoverage fixturePath does not exist: {fixture_path}",
                )

                selector_fields = coverage.get("selectorFields")
                self.assertIsInstance(selector_fields, list)
                self.assertTrue(
                    selector_fields,
                    f"{geometry}: browserAliasCoverage declares no selectorFields",
                )
                self.assertTrue(all(isinstance(field, str) for field in selector_fields))

    def test_every_coverage_entry_yields_a_fixture_case(self) -> None:
        # iter_palette_fixture_cases drives the Playwright alias suite; every
        # manifest coverage entry should turn into exactly one case (a dropped
        # case would silently lose browser coverage for that family).
        manifest = load_palette_manifest()
        covered = {
            family["geometry"]
            for family in manifest["families"]
            if "browserAliasCoverage" in family
        }
        cases = {case["family"] for case in iter_palette_fixture_cases()}
        self.assertEqual(cases, covered)

    def test_iter_palette_fixture_cases_uses_manifest_selector_fields(self) -> None:
        cases = {case["family"]: case for case in iter_palette_fixture_cases()}

        self.assertEqual(cases["chair"]["selector_fields"], ("orientation_token",))
        self.assertEqual(cases["shield"]["selector_fields"], ("kind",))
        self.assertEqual(cases["pinwheel"]["selector_fields"], ("chirality_token",))
        self.assertTrue(cases["shield"]["fixture_path"].endswith("shield-depth-3.json"))


if __name__ == "__main__":
    unittest.main()
