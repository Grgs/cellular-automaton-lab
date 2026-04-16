from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.run_render_review_sweep import (
    build_case_review_request,
    expand_sweep_cases,
    parse_cli_args,
    resolve_sweep_request,
    sweep_case_dir_name,
)


class RenderReviewSweepToolTests(unittest.TestCase):
    def test_resolve_sweep_request_defaults_from_profile(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-review-sweep-") as tmpdir:
            args = parse_cli_args(
                [
                    "--profile",
                    "pinwheel-depth-3",
                    "--artifact-dir",
                    str(Path(tmpdir) / "artifacts"),
                ]
            )
            request = resolve_sweep_request(args)
            self.assertEqual(request.profile.name, "pinwheel-depth-3")
            self.assertEqual(request.hosts, ("standalone",))
            self.assertEqual(request.themes, ("light",))
            self.assertEqual(request.patch_depths, (3,))
            self.assertIsNone(request.cell_sizes)

    def test_resolve_sweep_request_rejects_cell_sizes_for_patch_depth_profile(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-review-sweep-invalid-") as tmpdir:
            with self.assertRaises(SystemExit):
                request = parse_cli_args(
                    [
                        "--profile",
                        "pinwheel-depth-3",
                        "--cell-sizes",
                        "8,12",
                        "--artifact-dir",
                        str(Path(tmpdir) / "artifacts"),
                    ]
                )
                resolve_sweep_request(request)

    def test_sweep_case_dir_name_is_deterministic(self) -> None:
        self.assertEqual(
            sweep_case_dir_name(
                index=2,
                host="server",
                theme="dark",
                patch_depth=4,
                cell_size=None,
            ),
            "002-host-server-theme-dark-depth-4",
        )
        self.assertEqual(
            sweep_case_dir_name(
                index=5,
                host="standalone",
                theme="light",
                patch_depth=None,
                cell_size=12,
            ),
            "005-host-standalone-theme-light-size-12",
        )

    def test_expand_sweep_cases_preserves_host_theme_size_order(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-review-sweep-order-") as tmpdir:
            request = resolve_sweep_request(
                parse_cli_args(
                    [
                        "--profile",
                        "pinwheel-depth-3",
                        "--hosts",
                        "standalone,server",
                        "--themes",
                        "light,dark",
                        "--patch-depths",
                        "3,4",
                        "--artifact-dir",
                        str(Path(tmpdir) / "artifacts"),
                    ]
                )
            )
            cases = expand_sweep_cases(request)
            self.assertEqual(cases[0].name, "001-host-standalone-theme-light-depth-3")
            self.assertEqual(cases[1].name, "002-host-standalone-theme-light-depth-4")
            self.assertEqual(cases[2].name, "003-host-standalone-theme-dark-depth-3")
            self.assertEqual(cases[-1].name, "008-host-server-theme-dark-depth-4")

    def test_build_case_review_request_uses_case_artifact_dir(self) -> None:
        with tempfile.TemporaryDirectory(prefix="render-review-sweep-request-") as tmpdir:
            request = resolve_sweep_request(
                parse_cli_args(
                    [
                        "--profile",
                        "shield-depth-3",
                        "--artifact-dir",
                        str(Path(tmpdir) / "artifacts"),
                    ]
                )
            )
            case = expand_sweep_cases(request)[0]
            review_request = build_case_review_request(request, case)
            self.assertEqual(review_request.out, case.artifact_dir / "shield-depth-3.png")
            self.assertEqual(review_request.summary_out, case.artifact_dir / "shield-depth-3.json")
            self.assertEqual(review_request.theme, "light")
