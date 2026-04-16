from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools.render_canvas_review import main


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
class RenderCanvasReviewToolIntegrationTests(unittest.TestCase):
    def test_tool_renders_chair_png_and_summary(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-canvas-review-") as tmpdir:
            output_dir = Path(tmpdir)
            png_path = output_dir / "chair.png"
            summary_path = output_dir / "chair.json"

            exit_code = main(
                [
                    "--family",
                    "chair",
                    "--patch-depth",
                    "3",
                    "--out",
                    str(png_path),
                    "--summary-out",
                    str(summary_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(png_path.exists())
            self.assertGreater(png_path.stat().st_size, 0)
            self.assertTrue(summary_path.exists())

            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["tiling_family"], "chair")
            self.assertEqual(summary["patchDepth"], 3)
            self.assertGreater(summary["canvasPixelWidth"], 0)
            self.assertGreater(summary["canvasPixelHeight"], 0)
            self.assertGreater(summary["coverageWidthRatio"], 0)
            self.assertGreater(summary["coverageHeightRatio"], 0)
            self.assertGreater(summary["renderCellSize"], 0)
            self.assertIn("consistency", summary)
            self.assertEqual(summary["consistency"]["requested"]["tilingFamily"], "chair")
            self.assertEqual(summary["consistency"]["requested"]["patchDepth"], 3)
            self.assertIsNone(summary["consistency"]["backendTopology"])
            self.assertEqual(summary["consistency"]["browserState"]["tilingFamily"], "chair")
            self.assertEqual(summary["consistency"]["browserState"]["patchDepth"], 3)
            self.assertGreater(summary["consistency"]["browserState"]["topologyCellCount"], 0)
            self.assertIn("Backend topology facts unavailable for host mode standalone.", summary["consistency"]["warnings"])

    def test_tool_supports_profiles_literature_review_and_normalized_montages(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-canvas-review-profile-") as tmpdir:
            output_dir = Path(tmpdir)
            png_path = output_dir / "pinwheel.png"
            summary_path = output_dir / "pinwheel.json"
            cache_dir = output_dir / "cache"
            cache_dir.mkdir(parents=True)
            reference_path = cache_dir / "pinwheel-reference.png"
            montage_path = output_dir / "montage.png"
            Image.new("RGBA", (50, 100), (255, 255, 255, 255)).save(reference_path)

            exit_code = main(
                [
                    "--profile",
                    "pinwheel-depth-3",
                    "--literature-review",
                    "--reference-cache-dir",
                    str(cache_dir),
                    "--montage-out",
                    str(montage_path),
                    "--out",
                    str(png_path),
                    "--summary-out",
                    str(summary_path),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(png_path.exists())
            self.assertTrue(summary_path.exists())
            self.assertTrue(montage_path.exists())

            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["profile"], "pinwheel-depth-3")
            self.assertEqual(summary["tiling_family"], "pinwheel")
            self.assertIn("literatureReview", summary)
            self.assertIn("comparison", summary)
            self.assertIn("consistency", summary)
            self.assertEqual(summary["consistency"]["requested"]["tilingFamily"], "pinwheel")
            self.assertTrue(summary["literatureReview"]["requested"])
            self.assertEqual(summary["literatureReview"]["referenceImageStatus"], "cached")
            self.assertEqual(summary["literatureReview"]["referenceImagePath"], str(reference_path))
            self.assertEqual(summary["literatureReview"]["referenceCachePath"], str(reference_path))
            self.assertIn("https://annals.math.princeton.edu/1994/139-3/p05", summary["literatureReview"]["sourceUrls"])
            self.assertEqual(summary["comparison"]["referenceImagePath"], str(reference_path))
            self.assertEqual(summary["comparison"]["montageImagePath"], str(montage_path))
            self.assertEqual(summary["comparison"]["normalizationMode"], "contain")
