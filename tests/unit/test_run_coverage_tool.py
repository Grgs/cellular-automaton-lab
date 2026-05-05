import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

try:
    from tools.run_coverage import SUITES, available_suite_names, main
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.run_coverage import SUITES, available_suite_names, main


class SuiteCatalogTests(unittest.TestCase):
    def test_available_suite_names_match_internal_dictionary(self) -> None:
        self.assertEqual(set(available_suite_names()), set(SUITES.keys()))

    def test_unit_and_api_suites_are_registered(self) -> None:
        self.assertIn("unit", SUITES)
        self.assertIn("api", SUITES)

    def test_suites_use_distinct_data_files(self) -> None:
        files = {spec.data_file for spec in SUITES.values()}
        self.assertEqual(len(files), len(SUITES))

    def test_suites_target_expected_test_directories(self) -> None:
        self.assertEqual(SUITES["unit"].discover_path, "tests/unit")
        self.assertEqual(SUITES["api"].discover_path, "tests/api")


class MainOrchestrationTests(unittest.TestCase):
    def _silence_stdout(self) -> io.StringIO:
        return io.StringIO()

    def test_module_missing_returns_two(self) -> None:
        buffer = self._silence_stdout()
        err_buffer = io.StringIO()
        with (
            mock.patch("tools.run_coverage._coverage_modules_available", return_value=False),
            redirect_stdout(buffer),
            redirect_stderr(err_buffer),
        ):
            self.assertEqual(main(["--suite", "unit"]), 2)
        self.assertIn("pytest, pytest-cov, or coverage is not installed", err_buffer.getvalue())

    def test_unit_only_skips_combine_and_xml_html(self) -> None:
        buffer = self._silence_stdout()
        with (
            mock.patch("tools.run_coverage._coverage_modules_available", return_value=True),
            mock.patch("tools.run_coverage._run_suite", return_value=0) as run_suite,
            mock.patch("tools.run_coverage._combine") as combine,
            mock.patch("tools.run_coverage._report", return_value=0) as report,
            mock.patch("tools.run_coverage._emit_xml") as emit_xml,
            mock.patch("tools.run_coverage._emit_html") as emit_html,
            redirect_stdout(buffer),
        ):
            rc = main(["--suite", "unit"])
        self.assertEqual(rc, 0)
        self.assertEqual(run_suite.call_count, 1)
        self.assertEqual(run_suite.call_args.args[0].name, "unit")
        report.assert_called_once_with(".coverage.unit", None)
        combine.assert_not_called()
        emit_xml.assert_not_called()
        emit_html.assert_not_called()

    def test_default_runs_both_suites_then_combines_and_reports(self) -> None:
        buffer = self._silence_stdout()
        with (
            mock.patch("tools.run_coverage._coverage_modules_available", return_value=True),
            mock.patch("tools.run_coverage._run_suite", return_value=0) as run_suite,
            mock.patch("tools.run_coverage._combine", return_value=0) as combine,
            mock.patch("tools.run_coverage._report", return_value=0) as report,
            redirect_stdout(buffer),
        ):
            rc = main([])
        self.assertEqual(rc, 0)
        self.assertEqual(run_suite.call_count, 2)
        suite_names = [call.args[0].name for call in run_suite.call_args_list]
        self.assertEqual(suite_names, ["unit", "api"])
        combine.assert_called_once_with([".coverage.unit", ".coverage.api"], ".coverage")
        report.assert_called_once_with(".coverage", None)

    def test_no_combine_skips_combined_report_when_running_both_suites(self) -> None:
        buffer = self._silence_stdout()
        with (
            mock.patch("tools.run_coverage._coverage_modules_available", return_value=True),
            mock.patch("tools.run_coverage._run_suite", return_value=0),
            mock.patch("tools.run_coverage._combine") as combine,
            mock.patch("tools.run_coverage._report", return_value=0) as report,
            redirect_stdout(buffer),
        ):
            rc = main(["--no-combine"])
        self.assertEqual(rc, 0)
        combine.assert_not_called()
        self.assertEqual(
            [call.args[0] for call in report.call_args_list], [".coverage.unit", ".coverage.api"]
        )

    def test_fail_under_threshold_propagates_to_report(self) -> None:
        buffer = self._silence_stdout()
        with (
            mock.patch("tools.run_coverage._coverage_modules_available", return_value=True),
            mock.patch("tools.run_coverage._run_suite", return_value=0),
            mock.patch("tools.run_coverage._combine", return_value=0),
            mock.patch("tools.run_coverage._report", return_value=0) as report,
            redirect_stdout(buffer),
        ):
            main(["--fail-under", "85"])
        report.assert_called_once_with(".coverage", 85.0)

    def test_run_suite_failure_short_circuits(self) -> None:
        buffer = self._silence_stdout()
        with (
            mock.patch("tools.run_coverage._coverage_modules_available", return_value=True),
            mock.patch("tools.run_coverage._run_suite", return_value=4) as run_suite,
            mock.patch("tools.run_coverage._combine") as combine,
            mock.patch("tools.run_coverage._report") as report,
            redirect_stdout(buffer),
        ):
            rc = main([])
        self.assertEqual(rc, 4)
        # Only the first suite is attempted; the runner stops on failure.
        self.assertEqual(run_suite.call_count, 1)
        combine.assert_not_called()
        report.assert_not_called()

    def test_xml_and_html_emit_after_report(self) -> None:
        buffer = self._silence_stdout()
        with (
            mock.patch("tools.run_coverage._coverage_modules_available", return_value=True),
            mock.patch("tools.run_coverage._run_suite", return_value=0),
            mock.patch("tools.run_coverage._combine", return_value=0),
            mock.patch("tools.run_coverage._report", return_value=0),
            mock.patch("tools.run_coverage._emit_xml", return_value=0) as emit_xml,
            mock.patch("tools.run_coverage._emit_html", return_value=0) as emit_html,
            redirect_stdout(buffer),
        ):
            rc = main(
                [
                    "--xml",
                    "output/coverage/coverage.xml",
                    "--html",
                    "output/coverage/html",
                ]
            )
        self.assertEqual(rc, 0)
        emit_xml.assert_called_once()
        emit_html.assert_called_once()
        self.assertEqual(emit_xml.call_args.args[0], ".coverage")
        self.assertEqual(emit_html.call_args.args[0], ".coverage")


if __name__ == "__main__":
    unittest.main()
