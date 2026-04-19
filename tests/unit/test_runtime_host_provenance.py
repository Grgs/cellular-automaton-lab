from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.e2e.support_runtime_host import (
    build_runtime_provenance_report,
    compute_source_fingerprint,
    load_standalone_build_manifest,
)


class RuntimeHostProvenanceTests(unittest.TestCase):
    def test_compute_source_fingerprint_is_stable_for_unchanged_inputs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="runtime-host-provenance-") as tmpdir:
            root = Path(tmpdir)
            (root / "frontend").mkdir()
            (root / "frontend" / "app-runtime.ts").write_text("console.log('a');\n", encoding="utf-8")
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
            self.assertEqual(summary["manifestPath"], str(manifest_path))
            self.assertEqual(summary["sourceFileCount"], 2)

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

    def test_build_runtime_provenance_report_warns_on_git_head_and_fingerprint_mismatch(self) -> None:
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
