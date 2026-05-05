"""Run backend unit and/or API tests under pytest-cov and emit a report.

Mirrors the CI workflow locally so contributors can reproduce the same
backend coverage numbers without pushing a branch. Coverage configuration
lives in `.coveragerc`; this tool only orchestrates pytest-cov suite runs and
the coverage combine/report lifecycle needed when multiple suites are selected.

Examples:

    py -3 tools/run_coverage.py
    py -3 tools/run_coverage.py --suite unit
    py -3 tools/run_coverage.py --suite api --no-combine
    py -3 tools/run_coverage.py --fail-under 80
    py -3 tools/run_coverage.py --xml output/coverage/coverage.xml
    py -3 tools/run_coverage.py --html output/coverage/html
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

ROOT_DIR: Final[Path] = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class SuiteSpec:
    name: str
    data_file: str
    discover_path: str


SUITES: Final[dict[str, SuiteSpec]] = {
    "unit": SuiteSpec(name="unit", data_file=".coverage.unit", discover_path="tests/unit"),
    "api": SuiteSpec(name="api", data_file=".coverage.api", discover_path="tests/api"),
}


def _run(cmd: list[str]) -> int:
    completed = subprocess.run(cmd, cwd=ROOT_DIR, check=False)
    return completed.returncode


def _run_with_coverage_file(cmd: list[str], data_file: str) -> int:
    env = os.environ.copy()
    env["COVERAGE_FILE"] = data_file
    completed = subprocess.run(cmd, cwd=ROOT_DIR, check=False, env=env)
    return completed.returncode


def _coverage(*args: str) -> list[str]:
    return [sys.executable, "-m", "coverage", *args]


def _pytest_cov(suite: SuiteSpec) -> list[str]:
    return [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-s",
        suite.discover_path,
        "--cov=backend",
        "--cov=tools",
        "--cov-config=.coveragerc",
        "--cov-report=",
    ]


def _run_suite(suite: SuiteSpec) -> int:
    print(f"\n=== Running pytest-cov for {suite.name} suite ===", flush=True)
    return _run_with_coverage_file(_pytest_cov(suite), suite.data_file)


def _report(data_file: str, fail_under: float | None) -> int:
    args: list[str] = ["report", "-m", f"--data-file={data_file}"]
    if fail_under is not None:
        args.append(f"--fail-under={fail_under:g}")
    return _run(_coverage(*args))


def _combine(data_files: list[str], output: str) -> int:
    target = ROOT_DIR / output
    if target.exists():
        target.unlink()
    return _run(_coverage("combine", "--keep", f"--data-file={output}", *data_files))


def _emit_xml(data_file: str, output: Path) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    return _run(_coverage("xml", f"--data-file={data_file}", "-o", str(output)))


def _emit_html(data_file: str, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    return _run(_coverage("html", f"--data-file={data_file}", "-d", str(output)))


def _coverage_modules_available() -> bool:
    try:
        import coverage  # noqa: F401
        import pytest  # noqa: F401
        import pytest_cov  # noqa: F401
    except ImportError:
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--suite",
        choices=("all", "unit", "api"),
        default="all",
        help="which test suite to run under coverage (default: all)",
    )
    parser.add_argument(
        "--no-combine",
        action="store_true",
        help="skip the combined report when running both suites",
    )
    parser.add_argument(
        "--fail-under",
        type=float,
        default=None,
        help="fail the run when overall line coverage drops below this percentage",
    )
    parser.add_argument(
        "--xml",
        type=Path,
        default=None,
        help="write a Cobertura XML report to this path",
    )
    parser.add_argument(
        "--html",
        type=Path,
        default=None,
        help="write an HTML report into this directory",
    )
    parser.add_argument(
        "--combined-data-file",
        default=".coverage",
        help="path for the combined data file when running both suites (default: .coverage)",
    )
    args = parser.parse_args(argv)

    if not _coverage_modules_available():
        print(
            "pytest, pytest-cov, or coverage is not installed; "
            "install requirements-dev.txt before running this tool.",
            file=sys.stderr,
        )
        return 2

    suites_to_run: list[SuiteSpec] = []
    if args.suite in ("all", "unit"):
        suites_to_run.append(SUITES["unit"])
    if args.suite in ("all", "api"):
        suites_to_run.append(SUITES["api"])

    for suite in suites_to_run:
        rc = _run_suite(suite)
        if rc != 0:
            return rc

    has_multiple_suites = len(suites_to_run) > 1
    has_combined = has_multiple_suites and not args.no_combine
    report_data_file = args.combined_data_file if has_combined else suites_to_run[0].data_file

    if has_combined:
        print("\n=== Combining coverage data ===", flush=True)
        rc = _combine([s.data_file for s in suites_to_run], args.combined_data_file)
        if rc != 0:
            return rc

    if has_multiple_suites and args.no_combine:
        final_rc = 0
        for suite in suites_to_run:
            print(f"\n=== Coverage report ({suite.data_file}) ===", flush=True)
            rc = _report(suite.data_file, args.fail_under)
            if rc != 0 and args.fail_under is None:
                return rc
            final_rc = max(final_rc, rc)
        return final_rc

    print(f"\n=== Coverage report ({report_data_file}) ===", flush=True)
    rc = _report(report_data_file, args.fail_under)
    if rc != 0 and args.fail_under is None:
        return rc
    final_rc = rc

    if args.xml is not None:
        if (xml_rc := _emit_xml(report_data_file, args.xml)) != 0:
            return xml_rc
    if args.html is not None:
        if (html_rc := _emit_html(report_data_file, args.html)) != 0:
            return html_rc

    return final_rc


# Re-exported for tests; keeps the module surface minimal.
def available_suite_names() -> tuple[str, ...]:
    return tuple(SUITES.keys())


if __name__ == "__main__":
    raise SystemExit(main())
