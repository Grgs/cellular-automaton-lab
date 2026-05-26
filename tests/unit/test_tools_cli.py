from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import provenance
from tools.cli import main as tools_main
from tools.standalone_build import compute_source_fingerprint as build_compute_source_fingerprint
from tools.tools_docs import TOOLS_DOC_PATH, render_tools_reference


ROOT = Path(__file__).resolve().parents[2]
GROUPS = (
    "build",
    "tilings",
    "fixtures",
    "bootstrap",
    "browser",
    "test",
    "security",
    "perf",
    "repo",
)
REMOVED_PUBLIC_ENTRYPOINTS = (
    "tools/build-standalone.mjs",
    "tools/run-playwright.mjs",
    "tools/run-python.mjs",
    "tools/render_canvas_review.py",
    "tools/run_browser_check.py",
    "tools/run_render_review_sweep.py",
    "tools/run_render_review_diff.py",
    "tools/run_family_sample_workbench.py",
    "tools/run_geometry_cleanup_workbench.py",
    "tools/print_playwright_suite_manifest.py",
    "tools/print_standalone_build_status.py",
    "tools/run_e2e.py",
    "tools/render_standalone_shell.py",
)
LEGACY_COMMAND_PATTERNS = (
    re.compile(
        r"\b(?:python|py(?:\s+-3)?)\s+[./\\]*tools[\\/](?!internal[\\/])[\w.-]+\.(?:py|mjs)\b"
    ),
    re.compile(r"\bnode\s+[./\\]*tools[\\/](?!internal[\\/])[\w.-]+\.mjs\b"),
)
TEXT_FILE_SUFFIXES = {
    ".json",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}


def _iter_repo_surface_files() -> list[Path]:
    files: list[Path] = []
    for relative_path in (
        "README.md",
        "CONTRIBUTING.md",
        "package.json",
        ".pre-commit-config.yaml",
    ):
        path = ROOT / relative_path
        if path.exists():
            files.append(path)
    for relative_dir in ("docs", "examples", "tests", ".github"):
        directory = ROOT / relative_dir
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix.lower() in TEXT_FILE_SUFFIXES:
                files.append(path)
    return files


class ToolsCliTests(unittest.TestCase):
    def test_root_help_lists_public_command_groups(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "tools", "--help"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for group in GROUPS:
            self.assertIn(group, result.stdout)

    def test_each_group_supports_help(self) -> None:
        for group in GROUPS:
            with self.subTest(group=group):
                result = subprocess.run(
                    [sys.executable, "-m", "tools", group, "--help"],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(group, result.stdout)

    def test_playwright_e2e_subcommand_lists_suites(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "tools", "test", "e2e", "--list-suites"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(any(entry["name"] == "server" for entry in payload))
        self.assertTrue(any(entry["name"] == "standalone" for entry in payload))

    def test_standalone_build_status_summary_command_runs(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools",
                "test",
                "standalone-build-status",
                "--format",
                "summary",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("standalone build:", result.stdout)

    def test_passthrough_help_uses_cli_label(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "tools", "tilings", "sketch", "--help"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: python -m tools tilings sketch", result.stdout)

    def test_passthrough_error_uses_cli_label(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "tools", "tilings", "sketch"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("usage: python -m tools tilings sketch", result.stderr)

    def test_perf_bench_propagates_nonzero_exit_code(self) -> None:
        with patch("tools.bench_engine.main", return_value=7):
            self.assertEqual(tools_main(["perf", "bench"]), 7)

    def test_perf_latency_propagates_nonzero_exit_code(self) -> None:
        with patch("tools.profile_tiling_latency.main", return_value=9):
            self.assertEqual(tools_main(["perf", "latency"]), 9)

    def test_git_dirty_status_distinguishes_clean_dirty_and_unavailable(self) -> None:
        with patch("tools.provenance.read_git_status_porcelain", return_value=""):
            self.assertFalse(provenance.git_dirty_status(ROOT))
        with patch("tools.provenance.read_git_status_porcelain", return_value=" M tools/cli.py"):
            self.assertTrue(provenance.git_dirty_status(ROOT))
        with patch("tools.provenance.read_git_status_porcelain", return_value=None):
            self.assertIsNone(provenance.git_dirty_status(ROOT))

    def test_shared_source_fingerprint_helper_is_the_canonical_build_implementation(self) -> None:
        self.assertIs(build_compute_source_fingerprint, provenance.compute_source_fingerprint)

    def test_tools_reference_is_generated_from_the_cli_registry(self) -> None:
        current = TOOLS_DOC_PATH.read_text(encoding="utf-8")
        expected = render_tools_reference()
        self.assertEqual(
            current,
            expected,
            "docs/TOOLS.md is out of date. Run `python -m tools repo tools-docs --write`.",
        )

    def test_repo_surfaces_do_not_reference_removed_or_legacy_tool_entrypoints(self) -> None:
        current_file = Path(__file__).resolve()
        offenders: list[str] = []
        for path in _iter_repo_surface_files():
            if path == current_file:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            normalized = text.replace("\\", "/")
            for entrypoint in REMOVED_PUBLIC_ENTRYPOINTS:
                if entrypoint in normalized:
                    offenders.append(
                        f"{path.relative_to(ROOT)} mentions removed entrypoint {entrypoint}"
                    )
            for pattern in LEGACY_COMMAND_PATTERNS:
                match = pattern.search(text)
                if match is not None:
                    offenders.append(
                        f"{path.relative_to(ROOT)} contains legacy tool invocation {match.group(0)!r}"
                    )
        self.assertFalse(
            offenders,
            "Legacy tool references remain in repo-owned surfaces:\n" + "\n".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
