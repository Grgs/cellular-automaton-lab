from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.e2e.support_runtime_host import (
    build_runtime_provenance_report,
    compute_source_fingerprint,
    ensure_current_standalone_build,
    load_standalone_build_manifest,
    standalone_build_status,
)


class RuntimeHostProvenanceTests(unittest.TestCase):
    def tearDown(self) -> None:
        ensure_current_standalone_build.cache_clear()

    def test_compute_source_fingerprint_is_stable_for_unchanged_inputs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="runtime-host-provenance-") as tmpdir:
            root = Path(tmpdir)
            (root / "frontend").mkdir()
            (root / "frontend" / "app-runtime.ts").write_text(
                "console.log('a');\n", encoding="utf-8"
            )
            (root / "tools").mkdir()
            (root / "tools" / "build-standalone.mjs").write_text("export {};\n", encoding="utf-8")
            (root / "package.json").write_text("{}\n", encoding="utf-8")
            fingerprint_a, source_files_a = compute_source_fingerprint(root)
            fingerprint_b, source_files_b = compute_source_fingerprint(root)
            self.assertEqual(fingerprint_a, fingerprint_b)
            self.assertEqual(source_files_a, source_files_b)
            self.assertIn("frontend/app-runtime.ts", source_files_a)

    def test_load_standalone_build_manifest_summarizes_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="runtime-host-build-manifest-") as tmpdir:
            output_dir = Path(tmpdir)
            manifest_path = output_dir / "build-manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "builtAt": "2026-04-16T00:00:00Z",
                        "gitHead": "abc123",
                        "gitDirty": False,
                        "sourceFingerprint": "fingerprint",
                        "sourceFiles": ["frontend/app-runtime.ts", "package.json"],
                    }
                ),
                encoding="utf-8",
            )
            summary = load_standalone_build_manifest(output_dir)
            assert summary is not None
            self.assertEqual(summary["manifestPath"], str(manifest_path))
            self.assertEqual(summary["sourceFileCount"], 2)

    def test_standalone_build_status_reports_current_build(self) -> None:
        with tempfile.TemporaryDirectory(prefix="runtime-host-build-status-") as tmpdir:
            root = Path(tmpdir)
            (root / "frontend").mkdir()
            (root / "frontend" / "app-runtime.ts").write_text(
                "console.log('a');\n", encoding="utf-8"
            )
            (root / "tools").mkdir()
            (root / "tools" / "build-standalone.mjs").write_text("export {};\n", encoding="utf-8")
            (root / "package.json").write_text("{}\n", encoding="utf-8")
            (root / "package-lock.json").write_text("{}\n", encoding="utf-8")
            output_dir = root / "output" / "standalone"
            output_dir.mkdir(parents=True)
            for relative_path in (
                "index.html",
                "standalone-bootstrap.json",
                "standalone-python-bundle.json",
            ):
                (output_dir / relative_path).write_text("{}\n", encoding="utf-8")
            fingerprint, source_files = compute_source_fingerprint(root)
            (output_dir / "build-manifest.json").write_text(
                json.dumps(
                    {
                        "builtAt": "2026-04-19T00:00:00Z",
                        "gitHead": None,
                        "gitDirty": False,
                        "sourceFingerprint": fingerprint,
                        "sourceFiles": list(source_files),
                    }
                ),
                encoding="utf-8",
            )

            status = standalone_build_status(root)
            self.assertTrue(status["buildCurrent"])
            self.assertEqual(status["reason"], "standalone build outputs are current")
            self.assertFalse(status["missingOutputs"])

    def test_standalone_build_status_reports_missing_outputs_before_manifest_checks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="runtime-host-build-status-missing-") as tmpdir:
            root = Path(tmpdir)
            (root / "frontend").mkdir()
            (root / "frontend" / "app-runtime.ts").write_text(
                "console.log('a');\n", encoding="utf-8"
            )
            (root / "tools").mkdir()
            (root / "tools" / "build-standalone.mjs").write_text("export {};\n", encoding="utf-8")
            (root / "package.json").write_text("{}\n", encoding="utf-8")
            output_dir = root / "output" / "standalone"
            output_dir.mkdir(parents=True)

            status = standalone_build_status(root)
            self.assertFalse(status["buildCurrent"])
            self.assertEqual(status["reason"], "required outputs are missing")
            self.assertIn("index.html", status["missingOutputs"])

    def test_build_runtime_provenance_report_warns_on_missing_manifest(self) -> None:
        report = build_runtime_provenance_report(
            host_kind="standalone",
            current_repo={
                "gitHead": "current-head",
                "gitDirty": False,
                "sourceFingerprint": "fingerprint-a",
                "sourceFileCount": 4,
            },
            standalone_build=None,
        )
        self.assertIn("Standalone build manifest is missing.", report["warnings"])

    def test_build_runtime_provenance_report_warns_on_git_head_and_fingerprint_mismatch(
        self,
    ) -> None:
        report = build_runtime_provenance_report(
            host_kind="standalone",
            current_repo={
                "gitHead": "current-head",
                "gitDirty": False,
                "sourceFingerprint": "fingerprint-a",
                "sourceFileCount": 4,
            },
            standalone_build={
                "manifestPath": "/tmp/build-manifest.json",
                "builtAt": "2026-04-16T00:00:00Z",
                "gitHead": "old-head",
                "gitDirty": False,
                "sourceFingerprint": "fingerprint-b",
                "sourceFileCount": 4,
            },
        )
        self.assertFalse(report["comparison"]["gitHeadMatches"])
        self.assertFalse(report["comparison"]["fingerprintMatches"])
        self.assertTrue(
            any("does not match current checkout HEAD" in warning for warning in report["warnings"])
        )
        self.assertIn(
            "Standalone build source fingerprint does not match the current checkout.",
            report["warnings"],
        )

    def test_build_runtime_provenance_report_warns_on_dirty_standalone_build(self) -> None:
        report = build_runtime_provenance_report(
            host_kind="standalone",
            current_repo={
                "gitHead": "current-head",
                "gitDirty": False,
                "sourceFingerprint": "fingerprint-a",
                "sourceFileCount": 4,
            },
            standalone_build={
                "manifestPath": "/tmp/build-manifest.json",
                "builtAt": "2026-04-16T00:00:00Z",
                "gitHead": "current-head",
                "gitDirty": True,
                "sourceFingerprint": "fingerprint-a",
                "sourceFileCount": 4,
            },
        )
        self.assertIn("Standalone bundle was built from a dirty checkout.", report["warnings"])

    def test_ensure_current_standalone_build_skips_rebuild_when_current(self) -> None:
        with patch("tests.e2e.support_runtime_host.standalone_build_status") as status:
            status.return_value = {"buildCurrent": True}
            with patch("tests.e2e.support_runtime_host.subprocess.run") as run:
                ensure_current_standalone_build("/tmp/repo")
        run.assert_not_called()

    def test_ensure_current_standalone_build_rebuilds_when_stale(self) -> None:
        stale_status = {
            "buildCurrent": False,
            "reason": "source fingerprint differs from current checkout",
            "runtimeProvenance": {"warnings": []},
        }
        current_status = {
            "buildCurrent": True,
            "reason": "standalone build outputs are current",
            "runtimeProvenance": {"warnings": []},
        }
        with patch(
            "tests.e2e.support_runtime_host.standalone_build_status",
            side_effect=[stale_status, current_status],
        ) as status:
            with patch(
                "tests.e2e.support_runtime_host._resolve_npm_executable", return_value="npm"
            ):
                with patch(
                    "tests.e2e.support_runtime_host.subprocess.run",
                    return_value=subprocess.CompletedProcess(
                        ["npm", "run", "build:frontend:standalone"],
                        0,
                        stdout="ok",
                        stderr="",
                    ),
                ) as run:
                    ensure_current_standalone_build("/tmp/repo")
        self.assertEqual(status.call_count, 2)
        run.assert_called_once_with(
            ["npm", "run", "build:frontend:standalone"],
            cwd=Path("/tmp/repo"),
            check=False,
            capture_output=True,
            text=True,
        )

    def test_ensure_current_standalone_build_surfaces_build_failure(self) -> None:
        stale_status = {
            "buildCurrent": False,
            "reason": "required outputs are missing",
            "runtimeProvenance": {"warnings": []},
        }
        with patch(
            "tests.e2e.support_runtime_host.standalone_build_status",
            return_value=stale_status,
        ):
            with patch(
                "tests.e2e.support_runtime_host._resolve_npm_executable", return_value="npm"
            ):
                with patch(
                    "tests.e2e.support_runtime_host.subprocess.run",
                    return_value=subprocess.CompletedProcess(
                        ["npm", "run", "build:frontend:standalone"],
                        1,
                        stdout="stdout text",
                        stderr="stderr text",
                    ),
                ):
                    with self.assertRaises(RuntimeError) as context:
                        ensure_current_standalone_build("/tmp/repo")
        self.assertIn("Standalone build refresh failed", str(context.exception))
        self.assertIn("stdout text", str(context.exception))
        self.assertIn("stderr text", str(context.exception))

    def test_ensure_current_standalone_build_fails_when_bundle_remains_stale(self) -> None:
        stale_status = {
            "buildCurrent": False,
            "reason": "source fingerprint differs from current checkout",
            "runtimeProvenance": {
                "warnings": [
                    "Standalone build source fingerprint does not match the current checkout."
                ]
            },
        }
        with patch(
            "tests.e2e.support_runtime_host.standalone_build_status",
            side_effect=[stale_status, stale_status],
        ):
            with patch(
                "tests.e2e.support_runtime_host._resolve_npm_executable", return_value="npm"
            ):
                with patch(
                    "tests.e2e.support_runtime_host.subprocess.run",
                    return_value=subprocess.CompletedProcess(
                        ["npm", "run", "build:frontend:standalone"],
                        0,
                        stdout="ok",
                        stderr="",
                    ),
                ):
                    with self.assertRaises(RuntimeError) as context:
                        ensure_current_standalone_build("/tmp/repo")
        self.assertIn("bundle is still not current", str(context.exception))
        self.assertIn(
            "source fingerprint differs from current checkout",
            str(context.exception),
        )
