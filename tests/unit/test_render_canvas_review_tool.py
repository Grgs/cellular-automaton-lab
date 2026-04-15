from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.render_canvas_review import (
    parse_cli_args,
    resolve_montage_path,
    resolve_output_paths,
    resolve_render_review_request,
)


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

    def test_parse_cli_args_rejects_montage_without_reference(self) -> None:
        with self.assertRaises(SystemExit):
            parse_cli_args(["--family", "chair", "--montage-out", "/tmp/out.png"])

    def test_resolve_render_review_request_accepts_profile_without_family(self) -> None:
        args = parse_cli_args(["--profile", "pinwheel-depth-3"])
        request = resolve_render_review_request(args)
        self.assertEqual(request.family, "pinwheel")
        self.assertEqual(request.patch_depth, 3)
        self.assertEqual(request.viewport_width, 1200)
        self.assertEqual(request.viewport_height, 900)
        self.assertEqual(request.theme, "light")

    def test_resolve_render_review_request_prefers_explicit_cli_over_profile(self) -> None:
        args = parse_cli_args(
            [
                "--profile",
                "pinwheel-depth-3",
                "--family",
                "shield",
                "--patch-depth",
                "2",
                "--viewport-width",
                "1440",
                "--theme",
                "dark",
            ]
        )
        request = resolve_render_review_request(args)
        self.assertEqual(request.family, "shield")
        self.assertEqual(request.patch_depth, 2)
        self.assertEqual(request.viewport_width, 1440)
        self.assertEqual(request.theme, "dark")

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

    def test_resolve_montage_path_defaults_next_to_png_output(self) -> None:
        montage_path = resolve_montage_path(
            png_path=Path("/tmp/pinwheel-depth-3.png"),
            reference=Path("/tmp/reference.png"),
            montage_out=None,
        )
        self.assertEqual(montage_path, Path("/tmp/pinwheel-depth-3-montage.png"))

    def test_resolve_render_review_request_validates_reference_path(self) -> None:
        with self.assertRaises(SystemExit):
            args = parse_cli_args(["--family", "chair", "--reference", "/tmp/does-not-exist.png"])
            resolve_render_review_request(args)

    def test_resolve_render_review_request_preserves_reference_when_present(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-review-reference-") as tmpdir:
            reference_path = Path(tmpdir) / "reference.png"
            reference_path.write_bytes(b"png")
            args = parse_cli_args(
                ["--family", "chair", "--reference", str(reference_path)]
            )
            request = resolve_render_review_request(args)
            self.assertEqual(request.reference, reference_path)
