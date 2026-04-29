from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from tools.render_review.diff_review import (
    build_case_metadata_lines,
    build_diff_review_html,
    build_diff_review_image,
    collect_diff_review_cases,
    load_sweep_manifest,
    parse_cli_args,
    resolve_diff_review_request,
    run_render_review_diff,
)


class RenderReviewDiffToolTests(unittest.TestCase):
    def test_documented_thin_entrypoints_support_direct_help(self) -> None:
        root = Path(__file__).resolve().parents[2]
        for tool_path in (
            "tools/render_canvas_review.py",
            "tools/run_browser_check.py",
            "tools/run_render_review_sweep.py",
            "tools/run_render_review_diff.py",
            "tools/run_family_sample_workbench.py",
            "tools/run_geometry_cleanup_workbench.py",
        ):
            with self.subTest(tool_path=tool_path):
                result = subprocess.run(
                    [sys.executable, tool_path, "--help"],
                    cwd=root,
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def _write_fake_sweep_manifest(self, root: Path) -> Path:
        first_png = root / "case-1.png"
        first_montage = root / "case-1-montage.png"
        second_png = root / "case-2.png"
        Image.new("RGBA", (120, 80), (255, 0, 0, 255)).save(first_png)
        Image.new("RGBA", (180, 80), (255, 128, 0, 255)).save(first_montage)
        Image.new("RGBA", (80, 120), (0, 0, 255, 255)).save(second_png)
        first_summary = root / "case-1.json"
        second_summary = root / "case-2.json"
        first_summary.write_text("{}", encoding="utf-8")
        second_summary.write_text("{}", encoding="utf-8")
        manifest_path = root / "sweep-manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "profile": "pinwheel-depth-3",
                    "cases": [
                        {
                            "index": 1,
                            "name": "001-host-standalone-theme-light-depth-3",
                            "host": "standalone",
                            "theme": "light",
                            "patchDepth": 3,
                            "renderPng": str(first_png),
                            "renderMontage": str(first_montage),
                            "renderSummary": str(first_summary),
                            "metrics": {
                                "gridSizeText": "Depth 3 • 250 tiles",
                                "browserTopologyCellCount": 250,
                                "backendTopologyCellCount": 250,
                                "renderCellSize": 16.25,
                            },
                            "visualMetrics": {
                                "radialSymmetryScore": 0.75,
                                "visibleAspectRatio": 1.2,
                            },
                            "consistencyWarnings": [],
                            "provenanceWarnings": [],
                        },
                        {
                            "index": 2,
                            "name": "002-host-server-theme-dark-depth-4",
                            "host": "server",
                            "theme": "dark",
                            "patchDepth": 4,
                            "renderPng": str(second_png),
                            "renderSummary": str(second_summary),
                            "metrics": {
                                "gridSizeText": "Depth 4 • 1250 tiles",
                                "browserTopologyCellCount": 1250,
                                "backendTopologyCellCount": 1250,
                            },
                            "consistencyWarnings": ["example warning"],
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        return manifest_path

    def test_resolve_diff_review_request_accepts_existing_sweep_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-review-diff-request-") as tmpdir:
            manifest_path = Path(tmpdir) / "sweep-manifest.json"
            manifest_path.write_text('{"cases": []}', encoding="utf-8")
            request = resolve_diff_review_request(
                parse_cli_args(
                    [
                        "--sweep-manifest",
                        str(manifest_path),
                        "--columns",
                        "2",
                        "--allow-stale-standalone",
                    ]
                )
            )
            self.assertEqual(request.sweep_manifest, manifest_path)
            self.assertEqual(request.columns, 2)
            self.assertTrue(request.allow_stale_standalone)

    def test_resolve_diff_review_request_requires_manifest_or_profile(self) -> None:
        with self.assertRaises(SystemExit):
            resolve_diff_review_request(parse_cli_args([]))

    def test_collect_diff_review_cases_prefers_montage_image_when_present(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-review-diff-cases-") as tmpdir:
            root = Path(tmpdir)
            manifest_path = self._write_fake_sweep_manifest(root)
            manifest = load_sweep_manifest(manifest_path)
            cases = collect_diff_review_cases(manifest, manifest_path=manifest_path)
            self.assertEqual(len(cases), 2)
            self.assertEqual(cases[0].image_path, root / "case-1-montage.png")
            self.assertEqual(cases[1].image_path, root / "case-2.png")
            self.assertIn("cells browser=250 backend=250", build_case_metadata_lines(cases[0]))

    def test_build_diff_review_outputs_html_and_png_sheet(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-review-diff-output-") as tmpdir:
            root = Path(tmpdir)
            manifest_path = self._write_fake_sweep_manifest(root)
            manifest = load_sweep_manifest(manifest_path)
            cases = collect_diff_review_cases(manifest, manifest_path=manifest_path)
            html_path = build_diff_review_html(
                cases=cases,
                sweep_manifest_path=manifest_path,
                output_path=root / "review-diff.html",
                title="Example Diff",
            )
            image_path = build_diff_review_image(
                cases=cases,
                output_path=root / "review-diff.png",
                title="Example Diff",
                columns=2,
                card_image_width=200,
                card_image_height=120,
            )
            self.assertIn("Example Diff", html_path.read_text(encoding="utf-8"))
            self.assertTrue(image_path.exists())
            with Image.open(image_path) as generated:
                self.assertEqual(generated.width, 466)

    def test_run_render_review_diff_from_existing_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-review-diff-run-") as tmpdir:
            root = Path(tmpdir)
            manifest_path = self._write_fake_sweep_manifest(root)
            request = resolve_diff_review_request(
                parse_cli_args(
                    [
                        "--sweep-manifest",
                        str(manifest_path),
                        "--out-html",
                        str(root / "custom.html"),
                        "--out-image",
                        str(root / "custom.png"),
                    ]
                )
            )
            result = run_render_review_diff(request)
            self.assertEqual(result.case_count, 2)
            self.assertEqual(result.html_path, root / "custom.html")
            self.assertTrue(result.image_path.exists())

    def test_existing_manifest_can_write_default_outputs_to_artifact_dir(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-review-diff-artifact-dir-") as tmpdir:
            root = Path(tmpdir)
            manifest_path = self._write_fake_sweep_manifest(root)
            artifact_dir = root / "diff"
            request = resolve_diff_review_request(
                parse_cli_args(
                    [
                        "--sweep-manifest",
                        str(manifest_path),
                        "--artifact-dir",
                        str(artifact_dir),
                    ]
                )
            )
            result = run_render_review_diff(request)
            self.assertEqual(result.html_path, artifact_dir / "review-diff.html")
            self.assertEqual(result.image_path, artifact_dir / "review-diff.png")

    def test_repo_relative_manifest_paths_resolve_to_sheet_relative_links(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-review-diff-relative-paths-") as tmpdir:
            root = Path(tmpdir)
            sweep_dir = root / "output" / "sweep"
            case_dir = sweep_dir / "case"
            case_dir.mkdir(parents=True)
            Image.new("RGBA", (80, 60), (0, 255, 0, 255)).save(case_dir / "case.png")
            (case_dir / "case.json").write_text("{}", encoding="utf-8")
            manifest_path = sweep_dir / "sweep-manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "profile": "pinwheel-depth-3",
                        "cases": [
                            {
                                "index": 1,
                                "name": "case",
                                "renderPng": "output/sweep/case/case.png",
                                "renderSummary": "output/sweep/case/case.json",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with patch("tools.render_review.diff_review.ROOT_DIR", root):
                result = run_render_review_diff(
                    resolve_diff_review_request(
                        parse_cli_args(["--sweep-manifest", str(manifest_path)])
                    )
                )
            html = result.html_path.read_text(encoding="utf-8")
            self.assertIn('src="case/case.png"', html)
            self.assertIn('href="case/case.json"', html)
