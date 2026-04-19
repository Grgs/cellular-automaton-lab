from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
STYLE_TARGETS = (
    "backend/bootstrap_data.py",
    "backend/payload_contracts.py",
    "backend/payload_types.py",
    "tests/api/test_api_bootstrap.py",
    "tests/e2e/test_render_canvas_review_tool.py",
    "tests/e2e/test_run_browser_check_tool.py",
    "tests/e2e/test_run_family_sample_workbench_tool.py",
    "tests/e2e/test_run_geometry_cleanup_workbench_tool.py",
    "tests/e2e/test_run_render_review_sweep_tool.py",
    "tests/unit/test_aperiodic_family_contracts.py",
    "tests/unit/test_render_canvas_review_tool.py",
    "tests/unit/test_run_browser_check_tool.py",
    "tests/unit/test_run_family_sample_workbench_tool.py",
    "tests/unit/test_run_geometry_cleanup_workbench_tool.py",
    "tests/unit/test_run_render_review_sweep_tool.py",
    "tools/render_canvas_review.py",
    "tools/render_review",
    "tools/run_browser_check.py",
    "tools/run_family_sample_workbench.py",
    "tools/run_geometry_cleanup_workbench.py",
    "tools/run_render_review_sweep.py",
    "tools/run_python_style.py",
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
