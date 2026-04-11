from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAYWRIGHT_SUBSET_COUNT = 6


def run_command(command: list[str], *, env: dict[str, str] | None = None) -> None:
    merged_env = None if env is None else {**os.environ, **env}
    start = time.perf_counter()
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=merged_env,
        check=False,
    )
    elapsed = time.perf_counter() - start
    print(f"{elapsed:7.2f}s  {' '.join(command)}")
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def run_frontend_unit_tests() -> None:
    run_command(["npm", "run", "test:frontend"])
    run_command([sys.executable, "-m", "unittest", "-q", "tests.e2e.test_playwright_suite_integrity"])


def run_playwright_subsets(subset_count: int) -> None:
    run_command(["npm", "run", "build:frontend"])
    for subset_index in range(subset_count):
        run_command(
            ["node", "./tools/run-playwright.mjs", "--suite", "subset"],
            env={
                "PLAYWRIGHT_SUBSET_INDEX": str(subset_index),
                "PLAYWRIGHT_SUBSET_COUNT": str(subset_count),
            },
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run frontend Vitest checks and chunked Playwright suites.")
    parser.add_argument(
        "--frontend-only",
        action="store_true",
        help="Run only Vitest frontend tests and the Playwright suite integrity guard.",
    )
    parser.add_argument(
        "--playwright-only",
        action="store_true",
        help="Run only the chunked Playwright browser suites.",
    )
    parser.add_argument(
        "--subset-count",
        type=int,
        default=DEFAULT_PLAYWRIGHT_SUBSET_COUNT,
        help="Number of Playwright chunks to split the browser suite into.",
    )
    args = parser.parse_args()

    if args.frontend_only and args.playwright_only:
        parser.error("--frontend-only and --playwright-only cannot be used together")
    if args.subset_count <= 0:
        parser.error("--subset-count must be positive")

    if not args.playwright_only:
        run_frontend_unit_tests()

    if not args.frontend_only:
        run_playwright_subsets(args.subset_count)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
