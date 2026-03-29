from collections import Counter
import unittest


from tests.e2e.playwright_suite_support import (
    DEFAULT_PLAYWRIGHT_SUBSET_COUNT,
    PLAYWRIGHT_FEATURE_NAMES,
    build_playwright_suite,
    iter_playwright_feature_test_names,
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
    def test_default_playwright_loader_covers_every_master_browser_test(self) -> None:
        expected = iter_playwright_test_names()
        self.assertEqual(iter_playwright_test_names(), expected)
        self.assertEqual(sorted(_iter_suite_test_names(build_playwright_suite())), expected)

    def test_chunked_playwright_subsets_cover_every_master_browser_test_once(self) -> None:
        expected = iter_playwright_test_names()
        chunked_names: list[str] = []
        for subset_index in range(DEFAULT_PLAYWRIGHT_SUBSET_COUNT):
            subset_names = iter_playwright_subset_test_names(
                subset_index,
                DEFAULT_PLAYWRIGHT_SUBSET_COUNT,
            )
            self.assertTrue(subset_names)
            chunked_names.extend(subset_names)

        self.assertEqual(sorted(chunked_names), expected)
        self.assertEqual(Counter(chunked_names), Counter(expected))

    def test_feature_playwright_suites_cover_every_master_browser_test_once(self) -> None:
        expected = iter_playwright_test_names()
        feature_names: list[str] = []
        for feature_name in PLAYWRIGHT_FEATURE_NAMES:
            names = iter_playwright_feature_test_names(feature_name)
            self.assertTrue(names)
            feature_names.extend(names)

        self.assertEqual(sorted(feature_names), expected)
        self.assertEqual(Counter(feature_names), Counter(expected))

    def test_grid_summary_parser_supports_regular_and_penrose_labels(self) -> None:
        regular = parse_grid_summary_text("36 x 25")
        penrose = parse_grid_summary_text("Depth 4 • 271 tiles")

        self.assertEqual(regular.kind, "regular")
        self.assertEqual(regular.width, 36)
        self.assertEqual(regular.height, 25)
        self.assertIsNone(regular.patch_depth)

        self.assertEqual(penrose.kind, "penrose")
        self.assertIsNone(penrose.width)
        self.assertIsNone(penrose.height)
        self.assertEqual(penrose.patch_depth, 4)


if __name__ == "__main__":
    unittest.main()
