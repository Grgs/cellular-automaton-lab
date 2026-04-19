from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from backend.simulation.topology import build_topology
from tools.render_review.family_sample_workbench import (
    DEFAULT_WORKBENCH_OUTPUT_DIR,
    build_structural_summary,
    candidate_dir_name,
    default_shield_window_values,
    expand_candidates,
    parse_cli_args,
    resolve_default_workbench_artifact_dir,
    resolve_workbench_request,
)


class FamilySampleWorkbenchToolTests(unittest.TestCase):
    def test_resolve_workbench_request_defaults_shield_to_representative_window(self) -> None:
        with tempfile.TemporaryDirectory(prefix="family-sample-workbench-") as tmpdir:
            request = resolve_workbench_request(
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
            self.assertEqual(request.strategy, "representative-window")
            self.assertEqual(request.host, "standalone")
            self.assertEqual(request.theme, "light")
            self.assertFalse(request.browser_review)
            self.assertEqual(request.values, default_shield_window_values(patch_depth=3))

    def test_resolve_workbench_request_defaults_non_shield_to_baseline(self) -> None:
        with tempfile.TemporaryDirectory(prefix="family-sample-workbench-baseline-") as tmpdir:
            request = resolve_workbench_request(
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
            self.assertEqual(request.strategy, "baseline")
            self.assertIsNone(request.values)

    def test_resolve_workbench_request_rejects_values_for_baseline(self) -> None:
        with tempfile.TemporaryDirectory(prefix="family-sample-workbench-invalid-") as tmpdir:
            with self.assertRaises(SystemExit):
                resolve_workbench_request(
                    parse_cli_args(
                        [
                            "--family",
                            "pinwheel",
                            "--patch-depth",
                            "3",
                            "--values",
                            "1,2",
                            "--artifact-dir",
                            str(Path(tmpdir) / "artifacts"),
                        ]
                    )
                )

    def test_resolve_workbench_request_rejects_non_patch_depth_family(self) -> None:
        with tempfile.TemporaryDirectory(prefix="family-sample-workbench-grid-") as tmpdir:
            with self.assertRaises(SystemExit):
                resolve_workbench_request(
                    parse_cli_args(
                        [
                            "--family",
                            "square",
                            "--patch-depth",
                            "3",
                            "--artifact-dir",
                            str(Path(tmpdir) / "artifacts"),
                        ]
                    )
                )

    def test_expand_candidates_builds_deterministic_shield_threshold_names(self) -> None:
        with tempfile.TemporaryDirectory(prefix="family-sample-workbench-candidates-") as tmpdir:
            request = resolve_workbench_request(
                parse_cli_args(
                    [
                        "--family",
                        "shield",
                        "--patch-depth",
                        "3",
                        "--values",
                        "193.39344,214.8816",
                        "--artifact-dir",
                        str(Path(tmpdir) / "artifacts"),
                    ]
                )
            )
            candidates = expand_candidates(request)
            self.assertEqual(candidate_dir_name(candidates[0]), "001-threshold-193.393440")
            self.assertEqual(candidate_dir_name(candidates[1]), "002-threshold-214.881600")

    def test_expand_candidates_uses_single_baseline_for_non_shield_family(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="family-sample-workbench-baseline-candidate-"
        ) as tmpdir:
            request = resolve_workbench_request(
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
            candidates = expand_candidates(request)
            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0].name, "001-baseline")

    def test_baseline_candidate_matches_shipped_topology_for_non_shield_family(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="family-sample-workbench-baseline-match-"
        ) as tmpdir:
            request = resolve_workbench_request(
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
            candidate = expand_candidates(request)[0]
            shipped = build_topology("pinwheel", 0, 0, 3)
            self.assertEqual(candidate.topology.to_dict(), shipped.to_dict())

    def test_build_structural_summary_reuses_reference_observation_shape(self) -> None:
        with tempfile.TemporaryDirectory(prefix="family-sample-workbench-summary-") as tmpdir:
            request = resolve_workbench_request(
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
            candidate = expand_candidates(request)[0]
            summary = build_structural_summary(candidate=candidate, request=request)
            self.assertEqual(summary["family"], "pinwheel")
            self.assertEqual(summary["patchDepth"], 3)
            self.assertGreater(summary["total_cells"], 0)
            self.assertIn("validation", summary)
            self.assertIn("overlapPairCount", summary["validation"])
            self.assertIn("signature", summary)

    def test_default_artifact_dir_generation_is_unique_across_repeated_calls(self) -> None:
        first = resolve_default_workbench_artifact_dir(
            artifact_dir=None,
            default_parent=DEFAULT_WORKBENCH_OUTPUT_DIR,
            name="shield-depth-3",
        )
        second = resolve_default_workbench_artifact_dir(
            artifact_dir=None,
            default_parent=DEFAULT_WORKBENCH_OUTPUT_DIR,
            name="shield-depth-3",
        )
        try:
            self.assertNotEqual(first, second)
            self.assertTrue(first.exists())
            self.assertTrue(second.exists())
        finally:
            shutil.rmtree(first, ignore_errors=True)
            shutil.rmtree(second, ignore_errors=True)
