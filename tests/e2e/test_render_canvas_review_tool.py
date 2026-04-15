from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

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
