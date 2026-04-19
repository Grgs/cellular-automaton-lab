from __future__ import annotations

from dataclasses import asdict
import tempfile
import unittest
from pathlib import Path

from backend.simulation.reference_verification.observation import observe_topology
from tools.render_review.geometry_cleanup_workbench import (
    build_cleanup_structural_summary,
    default_shield_cleanup_scales,
    expand_cleanup_candidates,
    parse_cli_args,
    resolve_cleanup_workbench_request,
)


class GeometryCleanupWorkbenchToolTests(unittest.TestCase):
    def test_resolve_request_defaults_to_shield_trace_cleanup_scale(self) -> None:
        with tempfile.TemporaryDirectory(prefix="geometry-cleanup-workbench-") as tmpdir:
            request = resolve_cleanup_workbench_request(
                parse_cli_args(
                    [
                        "--family",
                        "shield",
                        "--patch-depth",
                        "3",
                        "--artifact-dir",
                        str(Path(tmpdir) / "artifacts"),
                    ]
                )
            )
            self.assertEqual(request.strategy, "trace-cleanup-scale")
            self.assertEqual(request.values, default_shield_cleanup_scales())
            self.assertFalse(request.browser_review)

    def test_resolve_request_rejects_non_shield_family(self) -> None:
        with tempfile.TemporaryDirectory(prefix="geometry-cleanup-workbench-pinwheel-") as tmpdir:
            with self.assertRaises(SystemExit):
                resolve_cleanup_workbench_request(
                    parse_cli_args(
                        [
                            "--family",
                            "pinwheel",
                            "--patch-depth",
                            "3",
                            "--artifact-dir",
                            str(Path(tmpdir) / "artifacts"),
                        ]
                    )
                )

    def test_resolve_request_includes_baseline_scale_when_values_are_provided(self) -> None:
        with tempfile.TemporaryDirectory(prefix="geometry-cleanup-workbench-values-") as tmpdir:
            request = resolve_cleanup_workbench_request(
                parse_cli_args(
                    [
                        "--family",
                        "shield",
                        "--patch-depth",
                        "3",
                        "--values",
                        "0.941,0.961",
                        "--artifact-dir",
                        str(Path(tmpdir) / "artifacts"),
                    ]
                )
            )
            self.assertEqual(request.values, (0.941, 0.961, 1.0))

    def test_expand_candidates_builds_deterministic_scale_names(self) -> None:
        with tempfile.TemporaryDirectory(prefix="geometry-cleanup-workbench-candidates-") as tmpdir:
            request = resolve_cleanup_workbench_request(
                parse_cli_args(
                    [
                        "--family",
                        "shield",
                        "--patch-depth",
                        "3",
                        "--values",
                        "0.941,0.951",
                        "--artifact-dir",
                        str(Path(tmpdir) / "artifacts"),
                    ]
                )
            )
            candidates = expand_cleanup_candidates(request)
            self.assertEqual(candidates[0].name, "001-scale-0.941000")
            self.assertEqual(candidates[1].name, "002-scale-0.951000")
            self.assertEqual(candidates[2].name, "003-scale-1.000000")
            self.assertFalse(candidates[0].is_baseline)
            self.assertFalse(candidates[1].is_baseline)
            self.assertTrue(candidates[2].is_baseline)

    def test_build_cleanup_structural_summary_reports_bounds_drift_and_warnings(self) -> None:
        with tempfile.TemporaryDirectory(prefix="geometry-cleanup-workbench-summary-") as tmpdir:
            request = resolve_cleanup_workbench_request(
                parse_cli_args(
                    [
                        "--family",
                        "shield",
                        "--patch-depth",
                        "3",
                        "--values",
                        "0.941,0.951,0.961",
                        "--artifact-dir",
                        str(Path(tmpdir) / "artifacts"),
                    ]
                )
            )
            candidates = expand_cleanup_candidates(request)
            baseline_candidate = next(
                candidate for candidate in candidates if candidate.is_baseline
            )
            baseline_summary = observe_topology(
                geometry=request.family,
                sample_mode="cleanup_workbench_baseline",
                depth=request.patch_depth,
                topology=baseline_candidate.topology,
            )
            summary = build_cleanup_structural_summary(
                candidate=next(
                    candidate for candidate in candidates if candidate.parameter_value == 0.961
                ),
                request=request,
                baseline_summary=asdict(baseline_summary),
                browser_review_summary=None,
            )

            bounds_drift = summary["cleanupDiagnostics"]["boundsDrift"]
            self.assertEqual(bounds_drift["widthRatio"], 1.0)
            self.assertEqual(summary["cleanupDiagnostics"]["visualComparison"]["gutterScore"], None)
            self.assertTrue(summary["cleanupDiagnostics"]["warnings"])
