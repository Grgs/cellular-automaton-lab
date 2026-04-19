from collections import Counter
import unittest

from backend.simulation.topology_catalog import (
    PENROSE_GEOMETRY,
    default_patch_depth_for_tiling_family,
)

from tests.e2e.playwright_suite_support import (
    DEFAULT_PLAYWRIGHT_SUBSET_COUNT,
    PLAYWRIGHT_FEATURE_NAMES,
    build_playwright_suite,
    build_server_playwright_suite,
    iter_public_playwright_suite_names,
    iter_playwright_feature_test_names,
    playwright_suite_manifest_payload,
    iter_server_playwright_test_names,
    iter_server_playwright_subset_test_names,
    iter_standalone_runtime_test_names,
    iter_playwright_subset_test_names,
    iter_playwright_test_names,
)
from tests.e2e.support_browser import parse_grid_summary_text


def _iter_suite_test_names(suite: unittest.TestSuite) -> list[str]:
    names: list[str] = []
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            names.extend(_iter_suite_test_names(item))
            continue
        names.append(item.id().rsplit(".", 2)[-2] + "." + item._testMethodName)
    return names


class PlaywrightSuiteIntegrityTests(unittest.TestCase):
    def test_public_suite_manifest_declares_every_runner_entrypoint(self) -> None:
        manifest = playwright_suite_manifest_payload()
        suite_names = [entry["name"] for entry in manifest]

        self.assertEqual(suite_names, iter_public_playwright_suite_names())
        self.assertEqual(
            suite_names,
            [
                "all",
                "server",
                "standalone",
                "subset",
                *PLAYWRIGHT_FEATURE_NAMES,
            ],
        )

    def test_standalone_build_flags_match_suite_scope(self) -> None:
        manifest = {
            entry["name"]: entry
            for entry in playwright_suite_manifest_payload()
        }

        self.assertTrue(manifest["all"]["requires_standalone_build"])
        self.assertTrue(manifest["standalone"]["requires_standalone_build"])
        self.assertTrue(manifest["standalone_runtime"]["requires_standalone_build"])
        self.assertFalse(manifest["server"]["requires_standalone_build"])
        self.assertFalse(manifest["subset"]["requires_standalone_build"])
        self.assertFalse(manifest["rules_and_picker"]["requires_standalone_build"])
        self.assertFalse(manifest["topology_and_persistence"]["requires_standalone_build"])

    def test_default_playwright_loader_covers_every_master_browser_test(self) -> None:
        expected = iter_playwright_test_names()
        self.assertEqual(iter_playwright_test_names(), expected)
        self.assertEqual(sorted(_iter_suite_test_names(build_playwright_suite())), expected)

    def test_server_playwright_loader_covers_every_server_browser_test(self) -> None:
        expected = iter_server_playwright_test_names()
        self.assertEqual(sorted(_iter_suite_test_names(build_server_playwright_suite())), expected)

    def test_chunked_playwright_subsets_cover_every_server_browser_test_once(self) -> None:
        expected = iter_server_playwright_test_names()
        chunked_names: list[str] = []
        for subset_index in range(DEFAULT_PLAYWRIGHT_SUBSET_COUNT):
            subset_names = iter_server_playwright_subset_test_names(
                subset_index,
                DEFAULT_PLAYWRIGHT_SUBSET_COUNT,
            )
            self.assertTrue(subset_names)
            chunked_names.extend(subset_names)

        self.assertEqual(sorted(chunked_names), expected)
        self.assertEqual(Counter(chunked_names), Counter(expected))

    def test_server_shards_plus_standalone_suite_cover_every_master_browser_test_once(self) -> None:
        expected = iter_playwright_test_names()
        combined = list(iter_standalone_runtime_test_names())
        for subset_index in range(DEFAULT_PLAYWRIGHT_SUBSET_COUNT):
            combined.extend(iter_playwright_subset_test_names(
                subset_index,
                DEFAULT_PLAYWRIGHT_SUBSET_COUNT,
            ))

        self.assertEqual(sorted(combined), expected)
        self.assertEqual(Counter(combined), Counter(expected))

    def test_feature_playwright_suites_cover_every_master_browser_test_once(self) -> None:
        expected = iter_playwright_test_names()
        feature_names: list[str] = []
        for feature_name in PLAYWRIGHT_FEATURE_NAMES:
            names = iter_playwright_feature_test_names(feature_name)
            self.assertTrue(names)
            feature_names.extend(names)

        self.assertEqual(sorted(feature_names), expected)
        self.assertEqual(Counter(feature_names), Counter(expected))

    def test_grid_summary_parser_supports_regular_and_aperiodic_labels(self) -> None:
        regular = parse_grid_summary_text("36 x 25")
        expected_patch_depth = default_patch_depth_for_tiling_family(PENROSE_GEOMETRY)
        aperiodic = parse_grid_summary_text(f"Depth {expected_patch_depth} • 271 tiles")

        self.assertEqual(regular.kind, "regular")
        self.assertEqual(regular.width, 36)
        self.assertEqual(regular.height, 25)
        self.assertIsNone(regular.patch_depth)

        self.assertEqual(aperiodic.kind, "aperiodic")
        self.assertIsNone(aperiodic.width)
        self.assertIsNone(aperiodic.height)
        self.assertEqual(aperiodic.patch_depth, expected_patch_depth)


if __name__ == "__main__":
    unittest.main()
