import os
import unittest

from tests.e2e.playwright_suite_support import (
    DEFAULT_PLAYWRIGHT_SERVER_SUBSET_COUNT,
    build_server_playwright_subset,
)


def _resolve_subset_index() -> int:
    return int(os.environ.get("PLAYWRIGHT_SUBSET_INDEX", "0"))


def _resolve_subset_count() -> int:
    return int(
        os.environ.get(
            "PLAYWRIGHT_SUBSET_COUNT",
            str(DEFAULT_PLAYWRIGHT_SERVER_SUBSET_COUNT),
        )
    )


def load_tests(
    loader: unittest.TestLoader,
    tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    del loader, tests, pattern
    return build_server_playwright_subset(_resolve_subset_index(), _resolve_subset_count())


if __name__ == "__main__":
    unittest.main()
