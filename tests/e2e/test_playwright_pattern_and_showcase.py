import unittest

from tests.e2e.playwright_suite_support import (
    build_playwright_feature_suite,
    should_skip_playwright_under_discovery,
)


def load_tests(
    loader: unittest.TestLoader,
    tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    del loader, tests
    if should_skip_playwright_under_discovery(pattern):
        return unittest.TestSuite()
    return build_playwright_feature_suite("pattern_and_showcase")


if __name__ == "__main__":
    unittest.TextTestRunner().run(build_playwright_feature_suite("pattern_and_showcase"))
