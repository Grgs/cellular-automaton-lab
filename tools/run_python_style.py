from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
STYLE_TARGETS = (
    # Bootstrap and payload contracts.
    "backend/bootstrap_data.py",
    "backend/payload_contracts.py",
    "backend/payload_types.py",
    # Reference-spec and verification stack.
    "backend/simulation/literature_reference_specs.py",
    "backend/simulation/literature_reference_verification.py",
    "backend/simulation/reference_specs",
    "backend/simulation/reference_verification",
    # Verification and reference-fixture tools.
    "tools/regenerate_reference_fixtures.py",
    "tools/report_tiling_verification_strength.py",
    "tools/validate_tilings.py",
    "tools/verify_reference_tilings.py",
    # Browser diagnosis and workbench tooling.
    "tools/render_canvas_review.py",
    "tools/render_review",
    "tools/run_browser_check.py",
    "tools/run_family_sample_workbench.py",
    "tools/run_geometry_cleanup_workbench.py",
    "tools/run_render_review_diff.py",
    "tools/run_render_review_sweep.py",
    "tools/run_python_style.py",
    # Direct tests for the guarded Python slices.
    "tests/api/test_api_bootstrap.py",
    "tests/e2e/test_render_canvas_review_tool.py",
    "tests/e2e/test_run_browser_check_tool.py",
    "tests/e2e/test_run_family_sample_workbench_tool.py",
    "tests/e2e/test_run_geometry_cleanup_workbench_tool.py",
    "tests/e2e/test_run_render_review_sweep_tool.py",
    "tests/unit/test_aperiodic_family_contracts.py",
    "tests/unit/test_literature_reference_verification.py",
    "tests/unit/test_reference_fixture_regeneration.py",
    "tests/unit/test_report_tiling_verification_strength_tool.py",
    "tests/unit/test_render_canvas_review_tool.py",
    "tests/unit/test_validate_tilings_tool.py",
    "tests/unit/test_run_browser_check_tool.py",
    "tests/unit/test_run_family_sample_workbench_tool.py",
    "tests/unit/test_run_geometry_cleanup_workbench_tool.py",
    "tests/unit/test_run_render_review_diff_tool.py",
    "tests/unit/test_run_render_review_sweep_tool.py",
)

STYLE_COMMANDS = {
    "check": ["check", "--config", "ruff.toml"],
    "format-check": ["format", "--check", "--config", "ruff.toml"],
    "format": ["format", "--config", "ruff.toml"],
}


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1 or args[0] not in STYLE_COMMANDS:
        print(
            "Usage: python tools/run_python_style.py [check|format-check|format]", file=sys.stderr
        )
        return 2

    result = subprocess.run(
        [sys.executable, "-m", "ruff", *STYLE_COMMANDS[args[0]], *STYLE_TARGETS],
        cwd=ROOT_DIR,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
