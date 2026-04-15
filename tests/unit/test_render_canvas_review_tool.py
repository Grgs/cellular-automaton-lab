from __future__ import annotations

import unittest
from pathlib import Path

from tools.render_canvas_review import parse_cli_args, resolve_output_paths


class RenderCanvasReviewToolTests(unittest.TestCase):
    def test_parse_cli_args_rejects_conflicting_sizing_flags(self) -> None:
        with self.assertRaises(SystemExit):
            parse_cli_args(
                [
                    "--family",
                    "chair",
                    "--patch-depth",
                    "3",
                    "--cell-size",
                    "12",
                ]
            )

    def test_parse_cli_args_rejects_non_positive_viewport_dimensions(self) -> None:
        with self.assertRaises(SystemExit):
            parse_cli_args(["--family", "chair", "--viewport-width", "0"])

    def test_resolve_output_paths_defaults_to_render_review_directory(self) -> None:
        png_path, summary_path = resolve_output_paths(
            family="pinwheel",
            patch_depth=3,
            cell_size=None,
            out=None,
            summary_out=None,
        )
        self.assertTrue(str(png_path).endswith("output/render-review/pinwheel-depth-3.png"))
        self.assertTrue(str(summary_path).endswith("output/render-review/pinwheel-depth-3.json"))

    def test_resolve_output_paths_derives_summary_path_from_png_output(self) -> None:
        png_path, summary_path = resolve_output_paths(
            family="chair",
            patch_depth=3,
            cell_size=None,
            out=Path("/tmp/chair-review.png"),
            summary_out=None,
        )
        self.assertEqual(png_path, Path("/tmp/chair-review.png"))
        self.assertEqual(summary_path, Path("/tmp/chair-review.json"))

    def test_resolve_output_paths_derives_png_path_from_summary_output(self) -> None:
        png_path, summary_path = resolve_output_paths(
            family="hex",
            patch_depth=None,
            cell_size=12,
            out=None,
            summary_out=Path("/tmp/hex-review.json"),
        )
        self.assertEqual(png_path, Path("/tmp/hex-review.png"))
        self.assertEqual(summary_path, Path("/tmp/hex-review.json"))
