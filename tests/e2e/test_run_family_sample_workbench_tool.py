from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.run_family_sample_workbench import main


ROOT_DIR = Path(__file__).resolve().parents[2]
STANDALONE_OUTPUT_DIR = ROOT_DIR / "output" / "standalone"
STANDALONE_REQUIRED_OUTPUTS = (
    "index.html",
    "standalone-bootstrap.json",
    "standalone-python-bundle.json",
)


def _standalone_outputs_ready() -> bool:
    return all(
        (STANDALONE_OUTPUT_DIR / relative_path).exists()
        for relative_path in STANDALONE_REQUIRED_OUTPUTS
    )


class FamilySampleWorkbenchToolIntegrationTests(unittest.TestCase):
    def test_structural_only_shield_window_workbench_keeps_exact_output_stable(self) -> None:
        with tempfile.TemporaryDirectory(prefix="family-sample-workbench-tool-") as tmpdir:
            artifact_dir = Path(tmpdir) / "workbench"
            exit_code = main(
                [
                    "--family",
                    "shield",
                    "--patch-depth",
                    "3",
                    "--values",
                    "150,214.8816",
                    "--artifact-dir",
                    str(artifact_dir),
                ]
            )

            self.assertEqual(exit_code, 0)
            manifest = json.loads(
                (artifact_dir / "workbench-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["family"], "shield")
            self.assertEqual(manifest["strategy"], "representative-window")
            self.assertEqual(len(manifest["candidates"]), 2)

            first_summary = json.loads(
                Path(manifest["candidates"][0]["candidateSummary"]).read_text(encoding="utf-8")
            )
            second_summary = json.loads(
                Path(manifest["candidates"][1]["candidateSummary"]).read_text(encoding="utf-8")
            )
            self.assertEqual(first_summary["total_cells"], second_summary["total_cells"])
            self.assertEqual(first_summary["signature"], second_summary["signature"])
            self.assertIn("validation", first_summary)
            self.assertIn("validation", second_summary)

    def test_baseline_pinwheel_workbench_produces_single_candidate_summary(self) -> None:
        with tempfile.TemporaryDirectory(prefix="family-sample-workbench-pinwheel-") as tmpdir:
            artifact_dir = Path(tmpdir) / "workbench"
            exit_code = main(
                [
                    "--family",
                    "pinwheel",
                    "--patch-depth",
                    "3",
                    "--artifact-dir",
                    str(artifact_dir),
                ]
            )

            self.assertEqual(exit_code, 0)
            manifest = json.loads(
                (artifact_dir / "workbench-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["strategy"], "baseline")
            self.assertEqual(len(manifest["candidates"]), 1)
            summary = json.loads(
                Path(manifest["candidates"][0]["candidateSummary"]).read_text(encoding="utf-8")
            )
            self.assertGreater(summary["total_cells"], 0)


@unittest.skipUnless(
    _standalone_outputs_ready(),
    "standalone outputs are required; run `npm run build:frontend:standalone`",
)
class FamilySampleWorkbenchBrowserIntegrationTests(unittest.TestCase):
    def test_browser_review_renders_injected_candidate_topology(self) -> None:
        with tempfile.TemporaryDirectory(prefix="family-sample-workbench-browser-") as tmpdir:
            artifact_dir = Path(tmpdir) / "workbench"
            exit_code = main(
                [
                    "--family",
                    "shield",
                    "--patch-depth",
                    "3",
                    "--values",
                    "150",
                    "--browser-review",
                    "--host",
                    "standalone",
                    "--artifact-dir",
                    str(artifact_dir),
                ]
            )

            self.assertEqual(exit_code, 0)
            manifest = json.loads(
                (artifact_dir / "workbench-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(len(manifest["candidates"]), 1)
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
            self.assertTrue(render_review["settleDiagnostics"]["settled"])
