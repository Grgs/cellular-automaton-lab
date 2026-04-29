from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.render_review.browser_check import (
    build_run_manifest,
    require_current_standalone_build,
    ensure_render_review_outputs,
    resolve_default_artifact_dir,
    resolve_host_kind,
    build_parser,
)
from tools.render_review.review import parse_cli_args as parse_render_canvas_review_cli_args


class RunBrowserCheckToolTests(unittest.TestCase):
    def test_resolve_host_kind_defaults_auto_to_standalone(self) -> None:
        self.assertEqual(resolve_host_kind("auto"), "standalone")
        self.assertEqual(resolve_host_kind("server"), "server")

    def test_resolve_default_artifact_dir_uses_explicit_directory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="browser-check-artifacts-") as tmpdir:
            artifact_dir = resolve_default_artifact_dir(
                artifact_dir=Path(tmpdir),
                host_kind="standalone",
                mode_name="render-review",
            )
            self.assertEqual(artifact_dir, Path(tmpdir))

    def test_resolve_default_artifact_dir_creates_timestamped_default(self) -> None:
        with tempfile.TemporaryDirectory(prefix="browser-check-root-") as tmpdir:
            with patch("tools.render_review.browser_check.DEFAULT_BROWSER_CHECK_DIR", Path(tmpdir)):
                artifact_dir = resolve_default_artifact_dir(
                    artifact_dir=None,
                    host_kind="server",
                    mode_name="unittest",
                )
                self.assertTrue(artifact_dir.exists())
                self.assertIn("server", artifact_dir.name)
                self.assertIn("unittest", artifact_dir.name)

    def test_build_run_manifest_includes_expected_keys(self) -> None:
        manifest = build_run_manifest(
            host_kind="standalone",
            mode_name="render-review",
            artifact_dir=Path("/tmp/browser-check"),
        )
        self.assertEqual(manifest["hostKind"], "standalone")
        self.assertEqual(manifest["mode"], "render-review")
        self.assertEqual(manifest["artifactDir"], "/tmp/browser-check")
        self.assertIn("startedAt", manifest)

    def test_ensure_render_review_outputs_defaults_into_artifact_dir(self) -> None:
        with tempfile.TemporaryDirectory(prefix="browser-check-render-review-") as tmpdir:
            artifact_dir = Path(tmpdir)
            args = parse_render_canvas_review_cli_args(["--profile", "pinwheel-depth-3"])
            resolved = ensure_render_review_outputs(args, artifact_dir=artifact_dir)
            self.assertEqual(resolved.out, artifact_dir / "pinwheel-depth-3.png")
            self.assertEqual(resolved.summary_out, artifact_dir / "pinwheel-depth-3.json")

    def test_ensure_render_review_outputs_preserves_explicit_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="browser-check-render-review-explicit-") as tmpdir:
            artifact_dir = Path(tmpdir)
            args = parse_render_canvas_review_cli_args(
                [
                    "--profile",
                    "pinwheel-depth-3",
                    "--out",
                    str(artifact_dir / "custom.png"),
                    "--summary-out",
                    str(artifact_dir / "custom.json"),
                ]
            )
            resolved = ensure_render_review_outputs(args, artifact_dir=artifact_dir)
            self.assertEqual(resolved.out, artifact_dir / "custom.png")
            self.assertEqual(resolved.summary_out, artifact_dir / "custom.json")

    def test_ensure_render_review_outputs_adds_montage_for_literature_review(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="browser-check-render-review-literature-"
        ) as tmpdir:
            artifact_dir = Path(tmpdir)
            args = parse_render_canvas_review_cli_args(
                [
                    "--profile",
                    "pinwheel-depth-3",
                    "--literature-review",
                ]
            )
            resolved = ensure_render_review_outputs(args, artifact_dir=artifact_dir)
            self.assertEqual(resolved.out, artifact_dir / "pinwheel-depth-3.png")
            self.assertEqual(resolved.summary_out, artifact_dir / "pinwheel-depth-3.json")
            self.assertEqual(resolved.montage_out, artifact_dir / "pinwheel-depth-3-montage.png")

    def test_parser_accepts_success_artifacts_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--success-artifacts", "--unittest", "tests.example"])
        self.assertTrue(args.success_artifacts)

    def test_parser_accepts_allow_stale_standalone_flag(self) -> None:
        parser = build_parser()
        args, remaining = parser.parse_known_args(
            ["--allow-stale-standalone", "--render-review", "--profile", "pinwheel-depth-3"]
        )
        self.assertTrue(args.allow_stale_standalone)
        self.assertEqual(remaining, ["--profile", "pinwheel-depth-3"])

    def test_require_current_standalone_build_fails_with_actionable_message(self) -> None:
        with patch("tools.render_review.browser_check.standalone_build_status") as status:
            status.return_value = {
                "buildCurrent": False,
                "reason": "source fingerprint differs from current checkout",
                "recommendedBuildCommand": "npm run build:frontend:standalone",
                "runtimeProvenance": {
                    "warnings": [
                        "Standalone build source fingerprint does not match the current checkout."
                    ],
                },
            }
            with self.assertRaisesRegex(RuntimeError, "npm run build:frontend:standalone"):
                require_current_standalone_build(host_kind="standalone")

    def test_require_current_standalone_build_can_be_bypassed(self) -> None:
        with patch("tools.render_review.browser_check.standalone_build_status") as status:
            require_current_standalone_build(host_kind="standalone", allow_stale=True)
            status.assert_not_called()
