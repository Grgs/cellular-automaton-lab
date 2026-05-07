from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.e2e.support_runtime_host import ensure_current_standalone_build
from tools.run_geometry_cleanup_workbench import main


ROOT_DIR = Path(__file__).resolve().parents[2]


class GeometryCleanupWorkbenchToolIntegrationTests(unittest.TestCase):
    def test_structural_cleanup_workbench_reports_compatibility_no_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="geometry-cleanup-workbench-tool-") as tmpdir:
            artifact_dir = Path(tmpdir) / "workbench"
            exit_code = main(
                [
                    "--family",
                    "shield",
                    "--patch-depth",
                    "3",
                    "--values",
                    "0.941,0.961",
                    "--artifact-dir",
                    str(artifact_dir),
                ]
            )

            self.assertEqual(exit_code, 0)
            manifest = json.loads(
                (artifact_dir / "workbench-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["family"], "shield")
            self.assertEqual(manifest["strategy"], "trace-cleanup-scale")
            self.assertEqual(len(manifest["candidates"]), 3)

            first_summary = json.loads(
                Path(manifest["candidates"][0]["candidateSummary"]).read_text(encoding="utf-8")
            )
            last_summary = json.loads(
                Path(manifest["candidates"][-1]["candidateSummary"]).read_text(encoding="utf-8")
            )
            self.assertEqual(first_summary["cleanupDiagnostics"]["boundsDrift"]["widthRatio"], 1.0)
            self.assertEqual(last_summary["cleanupDiagnostics"]["boundsDrift"]["widthRatio"], 1.0)
            self.assertIn("maxOverlapArea", first_summary["cleanupDiagnostics"])


class GeometryCleanupWorkbenchBrowserIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        ensure_current_standalone_build(str(ROOT_DIR))

    def test_browser_review_renders_injected_cleanup_candidate_topology(self) -> None:
        with tempfile.TemporaryDirectory(prefix="geometry-cleanup-workbench-browser-") as tmpdir:
            artifact_dir = Path(tmpdir) / "workbench"
            exit_code = main(
                [
                    "--family",
                    "shield",
                    "--patch-depth",
                    "3",
                    "--values",
                    "0.941",
                    "--browser-review",
                    "--host",
                    "standalone",
                    "--theme",
                    "dark",
                    "--artifact-dir",
                    str(artifact_dir),
                ]
            )

            self.assertEqual(exit_code, 0)
            manifest = json.loads(
                (artifact_dir / "workbench-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(manifest["candidates"]), 2)
            candidate_record = manifest["candidates"][0]
            candidate_summary = json.loads(
                Path(candidate_record["candidateSummary"]).read_text(encoding="utf-8")
            )
            render_review = candidate_summary["renderReview"]
            self.assertEqual(
                render_review["consistency"]["reviewTarget"]["mode"], "injected_topology"
            )
            self.assertEqual(
                render_review["consistency"]["browserState"]["topologyCellCount"],
                candidate_summary["total_cells"],
            )
            self.assertTrue(Path(render_review["summaryPath"]).exists())
            self.assertTrue(Path(render_review["pngPath"]).exists())
            self.assertIn("profileExpectations", render_review)
            self.assertEqual(render_review["profileExpectations"]["profile"], "shield-depth-3")
            self.assertIsNotNone(
                candidate_summary["cleanupDiagnostics"]["visualComparison"]["gutterScore"]
            )
