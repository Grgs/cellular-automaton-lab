from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.run_render_review_sweep import main


ROOT_DIR = Path(__file__).resolve().parents[2]
STANDALONE_OUTPUT_DIR = ROOT_DIR / "output" / "standalone"
STANDALONE_REQUIRED_OUTPUTS = (
    "index.html",
    "standalone-bootstrap.json",
    "standalone-python-bundle.json",
)


def _standalone_outputs_ready() -> bool:
    return all((STANDALONE_OUTPUT_DIR / relative_path).exists() for relative_path in STANDALONE_REQUIRED_OUTPUTS)


@unittest.skipUnless(
    _standalone_outputs_ready(),
    "standalone outputs are required; run `npm run build:frontend:standalone`",
)
class RenderReviewSweepToolIntegrationTests(unittest.TestCase):
    def test_tool_runs_two_case_host_sweep(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-review-sweep-tool-") as tmpdir:
            artifact_dir = Path(tmpdir) / "sweep"
            exit_code = main(
                [
                    "--profile",
                    "shield-depth-3",
                    "--hosts",
                    "standalone,server",
                    "--artifact-dir",
                    str(artifact_dir),
                ]
            )

            self.assertEqual(exit_code, 0)
            manifest_path = artifact_dir / "sweep-manifest.json"
            self.assertTrue(manifest_path.exists())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["profile"], "shield-depth-3")
            self.assertEqual(manifest["exitStatus"], "success")
            self.assertEqual(len(manifest["cases"]), 2)

            first_case = manifest["cases"][0]
            second_case = manifest["cases"][1]
            self.assertEqual(first_case["host"], "standalone")
            self.assertEqual(second_case["host"], "server")

            for case in manifest["cases"]:
                case_dir = Path(case["artifactDir"])
                self.assertTrue(case_dir.exists())
                self.assertTrue(Path(case["runManifest"]).exists())
                self.assertTrue(Path(case["renderPng"]).exists())
                self.assertTrue(Path(case["renderSummary"]).exists())
                self.assertIn("gridSizeText", case["metrics"])
                self.assertIn("coverageWidthRatio", case["metrics"])
                self.assertIn("coverageHeightRatio", case["metrics"])
                self.assertIn("browserTopologyCellCount", case["metrics"])
                self.assertIn("backendTopologyCellCount", case["metrics"])
                self.assertIn("runtimeProvenance", case)
                self.assertIn("provenanceWarnings", case)
                self.assertIn("transformSummary", case)
                self.assertIn("overlapHotspots", case)

    def test_tool_records_literature_review_status_for_cached_reference(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-review-sweep-literature-tool-") as tmpdir:
            artifact_dir = Path(tmpdir) / "sweep"
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir(parents=True)
            Image.new("RGBA", (80, 120), (255, 255, 255, 255)).save(cache_dir / "pinwheel-reference.png")

            exit_code = main(
                [
                    "--profile",
                    "pinwheel-depth-3",
                    "--hosts",
                    "standalone,server",
                    "--literature-review",
                    "--reference-cache-dir",
                    str(cache_dir),
                    "--artifact-dir",
                    str(artifact_dir),
                ]
            )

            self.assertEqual(exit_code, 0)
            manifest = json.loads((artifact_dir / "sweep-manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["requestedMatrix"]["literatureReview"])
            self.assertEqual(manifest["requestedMatrix"]["referenceCacheDir"], str(cache_dir))
            self.assertEqual(len(manifest["cases"]), 2)
            for case in manifest["cases"]:
                self.assertEqual(case["literatureReview"]["referenceImageStatus"], "cached")
                self.assertEqual(case["literatureReview"]["referenceCachePath"], str(cache_dir / "pinwheel-reference.png"))
                self.assertTrue(Path(case["renderMontage"]).exists())
                self.assertIn("runtimeProvenance", case)
                self.assertIn("overlapHotspots", case)
