from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from PIL import Image

from tools.render_canvas_review import (
    build_visual_metrics,
    build_overlap_hotspots_summary,
    build_reference_montage,
    build_consistency_report,
    compute_orientation_diversity,
    compute_radial_symmetry_score,
    condense_overlap_hotspots,
    condense_transform_report,
    condense_visual_metrics,
    main,
    parse_grid_size_text,
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

    def test_main_lists_available_profiles_without_requiring_family(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["--list-profiles"])
        self.assertEqual(exit_code, 0)
        rendered = stdout.getvalue()
        self.assertIn("pinwheel-depth-3: family=pinwheel, depth=3", rendered)
        self.assertIn(
            "dodecagonal-square-triangle-depth-3: family=dodecagonal-square-triangle, depth=3",
            rendered,
        )

    def test_resolve_render_review_request_accepts_profile_without_family(self) -> None:
        args = parse_cli_args(["--profile", "pinwheel-depth-3"])
        request = resolve_render_review_request(args)
        self.assertEqual(request.family, "pinwheel")
        self.assertEqual(request.patch_depth, 3)
        self.assertEqual(request.viewport_width, 1200)
        self.assertEqual(request.viewport_height, 900)
        self.assertEqual(request.theme, "light")
        self.assertFalse(request.literature_review)

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

    def test_parse_cli_args_rejects_literature_review_without_profile(self) -> None:
        args = parse_cli_args(["--family", "chair", "--literature-review"])
        with self.assertRaises(SystemExit):
            resolve_render_review_request(args)

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

    def test_resolve_render_review_request_uses_profile_owned_cached_reference_for_literature_review(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-review-cache-") as tmpdir:
            cache_dir = Path(tmpdir)
            cached_reference = cache_dir / "pinwheel-reference.png"
            cached_reference.write_bytes(b"png")
            args = parse_cli_args(
                [
                    "--profile",
                    "pinwheel-depth-3",
                    "--literature-review",
                    "--reference-cache-dir",
                    str(cache_dir),
                ]
            )
            request = resolve_render_review_request(args)
            self.assertTrue(request.literature_review)
            self.assertEqual(request.reference, cached_reference)
            self.assertEqual(request.literature_reference.reference_status, "cached")
            self.assertEqual(request.literature_reference.cache_path, cached_reference)
            self.assertIn("https://annals.math.princeton.edu/1994/139-3/p05", request.literature_reference.source_urls)

    def test_explicit_reference_overrides_literature_cache(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-review-explicit-reference-") as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir(parents=True)
            explicit_reference = Path(tmpdir) / "explicit.png"
            explicit_reference.write_bytes(b"png")
            (cache_dir / "pinwheel-reference.png").write_bytes(b"png")
            args = parse_cli_args(
                [
                    "--profile",
                    "pinwheel-depth-3",
                    "--literature-review",
                    "--reference-cache-dir",
                    str(cache_dir),
                    "--reference",
                    str(explicit_reference),
                ]
            )
            request = resolve_render_review_request(args)
            self.assertEqual(request.reference, explicit_reference)
            self.assertEqual(request.literature_reference.reference_status, "explicit")

    def test_missing_literature_cache_emits_warning_without_failing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-review-missing-cache-") as tmpdir:
            cache_dir = Path(tmpdir)
            args = parse_cli_args(
                [
                    "--profile",
                    "shield-depth-3",
                    "--literature-review",
                    "--reference-cache-dir",
                    str(cache_dir),
                ]
            )
            request = resolve_render_review_request(args)
            self.assertIsNone(request.reference)
            self.assertEqual(request.literature_reference.reference_status, "missing")
            self.assertTrue(request.literature_reference.warnings)

    def test_build_reference_montage_normalizes_images_with_contain_panels(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-review-montage-") as tmpdir:
            tmpdir_path = Path(tmpdir)
            rendered_path = tmpdir_path / "rendered.png"
            reference_path = tmpdir_path / "reference.png"
            montage_path = tmpdir_path / "montage.png"
            Image.new("RGBA", (200, 100), (255, 0, 0, 255)).save(rendered_path)
            Image.new("RGBA", (50, 200), (0, 0, 255, 255)).save(reference_path)
            comparison = build_reference_montage(rendered_path, reference_path, montage_path)
            self.assertEqual(comparison["normalizationMode"], "contain")
            self.assertEqual(comparison["panelWidth"], 200)
            self.assertEqual(comparison["panelHeight"], 200)
            self.assertEqual(comparison["outputImageFittedWidth"], 200)
            self.assertEqual(comparison["outputImageFittedHeight"], 100)
            self.assertEqual(comparison["referenceImageFittedWidth"], 50)
            self.assertEqual(comparison["referenceImageFittedHeight"], 200)
            self.assertTrue(montage_path.exists())

    def test_condense_transform_report_extracts_bounds_and_sample_ids(self) -> None:
        condensed = condense_transform_report(
            {
                "adapterGeometry": "shield",
                "adapterFamily": "mixed",
                "topologyBounds": {"minX": -1, "maxX": 8, "minY": -1, "maxY": 1, "width": 9, "height": 2},
                "renderMetrics": {"cssWidth": 300, "cssHeight": 140, "canvasWidth": 300, "canvasHeight": 140},
                "sampleCells": {
                    "lexicographicFirst": {"cellId": "shield:a"},
                    "centerNearest": {"cellId": "shield:b"},
                    "boundaryFurthest": {"cellId": "shield:c"},
                },
            }
        )
        self.assertEqual(condensed["adapterGeometry"], "shield")
        self.assertEqual(condensed["sampleCellIds"]["centerNearest"], "shield:b")
        self.assertEqual(condensed["renderedBounds"]["width"], 300)

    def test_build_overlap_hotspots_summary_marks_large_shield_overlap_blocking(self) -> None:
        request = resolve_render_review_request(parse_cli_args(["--profile", "shield-depth-3"]))
        summary = build_overlap_hotspots_summary(
            family=request.family,
            profile=request.profile,
            overlap_hotspots={
                "representativeCellCount": 443,
                "sampledOverlapCount": 200,
                "maxSampledArea": 213254.65271002054,
                "topOverlapPairs": [],
                "topKindPairs": [],
                "transformSampleHits": ["shield:ref:1378", "shield:ref:1400"],
            },
        )
        assert summary is not None
        self.assertEqual(summary["status"], "blocking")
        self.assertEqual(summary["policyMode"], "image-derived-relaxed")
        self.assertTrue(summary["warnings"])

    def test_condense_overlap_hotspots_extracts_review_fields(self) -> None:
        condensed = condense_overlap_hotspots(
            {
                "status": "expected-to-reduce",
                "policyMode": "image-derived-relaxed",
                "representativeCellCount": 443,
                "sampledOverlapCount": 12,
                "maxSampledArea": 4.25,
                "transformSampleHits": ["shield:ref:1378"],
                "topKindPairs": [{"kindPair": "shield-square / shield-triangle", "count": 8}],
            }
        )
        self.assertEqual(condensed["status"], "expected-to-reduce")
        self.assertEqual(condensed["sampledOverlapCount"], 12)
        self.assertEqual(condensed["transformSampleHits"], ["shield:ref:1378"])

    def test_compute_orientation_diversity_normalizes_entropy(self) -> None:
        diversity = compute_orientation_diversity({"0": 4, "120": 4, "240": 4})
        self.assertEqual(diversity["uniqueOrientationTokens"], 3)
        self.assertAlmostEqual(float(diversity["normalizedEntropy"]), 1.0)

    def test_compute_radial_symmetry_score_clamps_uniform_distribution(self) -> None:
        self.assertEqual(compute_radial_symmetry_score([2] * 12), 1.0)
        self.assertIsNone(compute_radial_symmetry_score(None))

    def test_build_visual_metrics_combines_raster_and_geometry_signals(self) -> None:
        visual_metrics = build_visual_metrics(
            visual_summary={
                "visibleAspectRatio": 1.2,
                "edgeDensity": 0.4,
                "boundaryDominance": 0.35,
                "gutterScore": 0.02,
            },
            transform_report={
                "metricInputs": {
                    "renderedTopologyCenter": {"x": 50, "y": 50},
                    "renderedCellCount": 12,
                    "orientationTokenCounts": {"0": 4, "120": 4, "240": 4},
                    "angularSectorCounts": [1] * 12,
                }
            },
        )
        self.assertEqual(visual_metrics["visibleAspectRatio"], 1.2)
        self.assertEqual(visual_metrics["orientationDiversity"]["uniqueOrientationTokens"], 3)
        self.assertEqual(visual_metrics["angularSectorOccupancy"]["sectorCount"], 12)
        self.assertEqual(visual_metrics["angularSectorOccupancy"]["counts"], [1] * 12)
        self.assertEqual(visual_metrics["radialSymmetryScore"], 1.0)
        self.assertEqual(visual_metrics["warnings"], [])

    def test_build_visual_metrics_emits_warnings_for_unavailable_metrics(self) -> None:
        visual_metrics = build_visual_metrics(
            visual_summary={
                "visibleAspectRatio": None,
                "edgeDensity": None,
                "boundaryDominance": None,
                "gutterScore": None,
            },
            transform_report=None,
        )
        self.assertIsNone(visual_metrics["radialSymmetryScore"])
        self.assertIsNone(visual_metrics["orientationDiversity"]["normalizedEntropy"])
        self.assertTrue(visual_metrics["warnings"])

    def test_condense_visual_metrics_preserves_review_fields(self) -> None:
        condensed = condense_visual_metrics(
            {
                "visibleAspectRatio": 1.2,
                "edgeDensity": 0.4,
                "boundaryDominance": 0.35,
                "gutterScore": 0.02,
                "orientationDiversity": {"uniqueOrientationTokens": 3, "normalizedEntropy": 1.0},
                "angularSectorOccupancy": {
                    "sectorCount": 12,
                    "counts": [1] * 12,
                    "normalizedCounts": [1 / 12] * 12,
                },
                "radialSymmetryScore": 1.0,
                "warnings": ["example warning"],
            }
        )
        self.assertEqual(condensed["visibleAspectRatio"], 1.2)
        self.assertEqual(condensed["radialSymmetryScore"], 1.0)
        self.assertEqual(condensed["warnings"], ["example warning"])

    def test_parse_grid_size_text_parses_patch_depth_summary(self) -> None:
        parsed = parse_grid_size_text("Depth 3 • 600 tiles")
        self.assertEqual(parsed, {"mode": "patch_depth", "depth": 3, "tileCount": 600})

    def test_parse_grid_size_text_parses_grid_dimensions_summary(self) -> None:
        parsed = parse_grid_size_text("12 x 10")
        self.assertEqual(parsed, {"mode": "grid_dimensions", "width": 12, "height": 10})

    def test_build_consistency_report_warns_on_backend_browser_dom_mismatch(self) -> None:
        request = resolve_render_review_request(parse_cli_args(["--family", "pinwheel", "--patch-depth", "3"]))
        report = build_consistency_report(
            request=request,
            host_kind="server",
            actual_patch_depth=3,
            actual_cell_size=None,
            grid_size_text="Depth 3 • 600 tiles",
            generation_text="Generation 0",
            backend_topology={
                "tilingFamily": "pinwheel",
                "patchDepth": 3,
                "width": 2,
                "height": 1,
                "topologyCellCount": 250,
                "topologyRevision": "backend-rev",
            },
            browser_topology={
                "tilingFamily": "pinwheel",
                "patchDepth": 3,
                "topologyCellCount": 250,
                "width": 2,
                "height": 1,
                "topologyRevision": "browser-rev",
            },
        )
        self.assertEqual(report["parsedGridSummary"], {"mode": "patch_depth", "depth": 3, "tileCount": 600})
        self.assertIn(
            "Grid summary tile count 600 does not match browser topology cell count 250.",
            report["warnings"],
        )
        self.assertIn(
            "Grid summary tile count 600 does not match backend topology cell count 250.",
            report["warnings"],
        )
