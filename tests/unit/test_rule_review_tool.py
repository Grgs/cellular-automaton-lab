from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from tools import rule_review


class RuleReviewToolTests(unittest.TestCase):
    def test_review_writes_frames_montage_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            exit_code = rule_review.main(
                [
                    "--rule",
                    "conway",
                    "--geometry",
                    "square",
                    "--width",
                    "12",
                    "--height",
                    "12",
                    "--pattern",
                    "blinker",
                    "--generations",
                    "0,1,2",
                    "--output-dir",
                    str(output_dir),
                    "--prefix",
                    "blinker-review",
                ]
            )

            self.assertEqual(exit_code, 0)
            summary_path = output_dir / "blinker-review-summary.json"
            montage_path = output_dir / "blinker-review-montage.png"
            self.assertTrue(summary_path.exists())
            self.assertTrue(montage_path.exists())

            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertEqual(summary["rule"], "conway")
            self.assertEqual(summary["geometry"], "square")
            self.assertEqual(summary["generations"], [0, 1, 2])
            self.assertEqual(len(summary["frames"]), 3)
            for frame in summary["frames"]:
                frame_path = output_dir / frame["image"]
                self.assertTrue(frame_path.exists())
                self.assertGreater(frame["live_cells"], 0)

            with Image.open(montage_path) as image:
                self.assertGreater(image.width, 0)
                self.assertGreater(image.height, 0)

    def test_whirlpool_preset_rejects_non_whirlpool_rule(self) -> None:
        parser = rule_review.build_parser()
        args = parser.parse_args(
            [
                "--rule",
                "conway",
                "--preset",
                "anchored-source-vortex",
            ]
        )
        with self.assertRaisesRegex(ValueError, "Whirlpool"):
            rule_review.run_review(args)

    def test_whirlpool_preset_stays_inside_rectangular_board(self) -> None:
        cells = rule_review._build_whirlpool_preset(
            "anchored-source-vortex",
            80,
            50,
            geometry="square",
        )

        self.assertGreater(min(cell.y for cell in cells), 0)
        self.assertLess(max(cell.y for cell in cells), 49)

    def test_hex_whirlpool_preset_renders(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            exit_code = rule_review.main(
                [
                    "--rule",
                    "hexwhirlpool",
                    "--geometry",
                    "hex",
                    "--width",
                    "18",
                    "--height",
                    "14",
                    "--preset",
                    "centered-rotor",
                    "--generations",
                    "0,1",
                    "--output-dir",
                    str(output_dir),
                    "--prefix",
                    "hex-whirlpool-review",
                ]
            )

            self.assertEqual(exit_code, 0)
            summary = json.loads(
                (output_dir / "hex-whirlpool-review-summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(summary["rule"], "whirlpool")
            self.assertEqual(summary["geometry"], "hex")
            self.assertEqual(len(summary["frames"]), 2)


if __name__ == "__main__":
    unittest.main()
