from __future__ import annotations

import unittest
from unittest.mock import patch

from tools.generated_check import GeneratedCheckResult, _parse_only, run_selected_checks


class GeneratedCheckToolTests(unittest.TestCase):
    def test_parse_only_defaults_to_all_checks(self) -> None:
        self.assertEqual(
            _parse_only([]),
            (
                "tools-docs",
                "periodic-catalog",
                "bootstrap",
                "frontend-fixtures",
                "reference-fixtures",
            ),
        )

    def test_parse_only_deduplicates_selected_checks(self) -> None:
        self.assertEqual(
            _parse_only(["tools-docs", "tools-docs", "bootstrap"]),
            ("tools-docs", "bootstrap"),
        )

    def test_run_selected_checks_preserves_requested_order(self) -> None:
        with (
            patch(
                "tools.generated_check._check_bootstrap_fixture",
                return_value=GeneratedCheckResult("bootstrap", True, "ok"),
            ),
            patch(
                "tools.generated_check._check_tools_docs",
                return_value=GeneratedCheckResult("tools-docs", True, "ok"),
            ),
        ):
            results = run_selected_checks(("bootstrap", "tools-docs"))

        self.assertEqual([result.name for result in results], ["bootstrap", "tools-docs"])

    def test_run_selected_checks_reports_stale_result(self) -> None:
        with patch(
            "tools.generated_check._check_tools_docs",
            return_value=GeneratedCheckResult("tools-docs", False, "stale"),
        ):
            results = run_selected_checks(("tools-docs",))

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].ok)
        self.assertEqual(results[0].detail, "stale")


if __name__ == "__main__":
    unittest.main()
