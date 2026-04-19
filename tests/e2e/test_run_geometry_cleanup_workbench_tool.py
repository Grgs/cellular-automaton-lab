from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.run_geometry_cleanup_workbench import main


ROOT_DIR = Path(__file__).resolve().parents[2]
STANDALONE_OUTPUT_DIR = ROOT_DIR / "output" / "standalone"
STANDALONE_REQUIRED_OUTPUTS = (
    "index.html",
    "standalone-bootstrap.json",
    "standalone-python-bundle.json",
)


def _standalone_outputs_ready() -> bool:
    return all((STANDALONE_OUTPUT_DIR / relative_path).exists() for relative_path in STANDALONE_REQUIRED_OUTPUTS)


class GeometryCleanupWorkbenchToolIntegrationTests(unittest.TestCase):
    def test_structural_cleanup_workbench_records_distinct_candidate_drift(self) -> None:
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
            manifest = json.loads((artifact_dir / "workbench-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["family"], "shield")
            self.assertEqual(manifest["strategy"], "trace-cleanup-scale")
            self.assertEqual(len(manifest["candidates"]), 3)

            first_summary = json.loads(Path(manifest["candidates"][0]["candidateSummary"]).read_text(encoding="utf-8"))
            last_summary = json.loads(Path(manifest["candidates"][-1]["candidateSummary"]).read_text(encoding="utf-8"))
            self.assertNotEqual(
                first_summary["cleanupDiagnostics"]["boundsDrift"]["widthRatio"],
                last_summary["cleanupDiagnostics"]["boundsDrift"]["widthRatio"],
            )
            self.assertIn("maxOverlapArea", first_summary["cleanupDiagnostics"])


@unittest.skipUnless(
    _standalone_outputs_ready(),
    "standalone outputs are required; run `npm run build:frontend:standalone`",
)
class GeometryCleanupWorkbenchBrowserIntegrationTests(unittest.TestCase):
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
            manifest = json.loads((artifact_dir / "workbench-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["candidates"]), 2)
            candidate_record = manifest["candidates"][0]
            candidate_summary = json.loads(Path(candidate_record["candidateSummary"]).read_text(encoding="utf-8"))
            render_review = candidate_summary["renderReview"]
            self.assertEqual(render_review["consistency"]["reviewTarget"]["mode"], "injected_topology")
            self.assertEqual(
                render_review["consistency"]["browserState"]["topologyCellCount"],
                candidate_summary["total_cells"],
            )
            self.assertTrue(Path(render_review["summaryPath"]).exists())
            self.assertTrue(Path(render_review["pngPath"]).exists())
            self.assertIsNotNone(candidate_summary["cleanupDiagnostics"]["visualComparison"]["gutterScore"])
