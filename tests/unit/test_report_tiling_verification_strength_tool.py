import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import ClassVar


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.literature_reference_verification import verify_all_reference_families
from backend.simulation.reference_verification.types import ReferenceVerificationResult
from tools.report_tiling_verification_strength import (
    FailureSummary,
    ObservationSummary,
    VerificationStrengthRow,
    build_verification_strength_rows,
    main,
    render_verification_strength_report,
)


class ReportTilingVerificationStrengthToolTests(unittest.TestCase):
    rows: ClassVar[tuple[VerificationStrengthRow, ...]]
    rows_by_geometry: ClassVar[dict[str, VerificationStrengthRow]]
    live_results: ClassVar[dict[str, ReferenceVerificationResult]]

    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = build_verification_strength_rows()
        cls.rows_by_geometry = {row.geometry: row for row in cls.rows}
        cls.live_results = {result.geometry: result for result in verify_all_reference_families()}

    def test_main_prints_expected_summary_columns_and_rows(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = main([])

        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn(
            "geometry\tsample_mode\timplementation_status\tverification_status\tstrength_tags",
            output,
        )
        self.assertIn(
            "pinwheel\tpatch_depth\texact_affine\tPASS\t"
            "sample-exact,metadata,local-reference,canonical-patch,exact-path,strict-validation",
            output,
        )
        self.assertIn(
            "archimedean-4-8-8\tgrid\t\tPASS\t"
            "sample-exact,descriptor,vertex-stars,dual-checks,strict-validation",
            output,
        )
        self.assertIn(
            "archimedean-3-4-6-4\tgrid\t\tPASS\t"
            "sample-exact,descriptor,vertex-stars,dual-candidate-checks,strict-validation",
            output,
        )
        self.assertIn(
            "chair\tpatch_depth\ttrue_substitution\tPASS\t"
            "sample-exact,metadata,local-reference,strict-validation",
            output,
        )
        self.assertIn(
            "spectre\tpatch_depth\ttrue_substitution\tPASS\t"
            "sample-exact,canonical-patch,strict-validation",
            output,
        )
        self.assertIn(
            "robinson-triangles\tpatch_depth\ttrue_substitution\tPASS\t",
            output,
        )
        self.assertIn(
            "tuebingen-triangle\tpatch_depth\ttrue_substitution\tPASS\t",
            output,
        )
        self.assertIn("shield\tpatch_depth\ttrue_substitution\tPASS\t", output)

    def test_json_output_is_deterministic_and_contains_required_fields(self) -> None:
        first = render_verification_strength_report(self.rows, output_format="json")
        second = render_verification_strength_report(self.rows, output_format="json")

        self.assertEqual(first, second)
        payload = json.loads(first)
        self.assertEqual(payload["schema_version"], 1)
        families = payload["families"]
        self.assertEqual(
            [family["geometry"] for family in families],
            sorted(family["geometry"] for family in families),
        )

        shield = next(family for family in families if family["geometry"] == "shield")
        self.assertEqual(shield["implementation_status"], "true_substitution")
        self.assertEqual(shield["verification_status"], "PASS")
        self.assertIsNone(shield["promotion_blocker"])
        self.assertEqual(shield["depths"], [0, 1, 3])
        self.assertEqual(shield["failure_codes"], [])
        self.assertTrue(shield["has_local_reference"])
        self.assertTrue(shield["has_canonical_patch"])
        self.assertTrue(shield["strict_validation"])
        self.assertTrue(shield["verification_modes"])
        self.assertTrue(shield["observations"])

        robinson = next(family for family in families if family["geometry"] == "robinson-triangles")
        self.assertEqual(robinson["implementation_status"], "true_substitution")
        self.assertEqual(robinson["verification_status"], "PASS")
        self.assertTrue(robinson["has_canonical_patch"])
        self.assertIn("canonical-patch", robinson["strength_tags"])
        self.assertIn("canonical-patch", robinson["verification_modes"])

        tuebingen = next(
            family for family in families if family["geometry"] == "tuebingen-triangle"
        )
        self.assertEqual(tuebingen["implementation_status"], "true_substitution")
        self.assertEqual(tuebingen["verification_status"], "PASS")
        self.assertTrue(tuebingen["has_canonical_patch"])
        self.assertIn("canonical-patch", tuebingen["strength_tags"])
        self.assertIn("canonical-patch", tuebingen["verification_modes"])

        pinwheel = next(family for family in families if family["geometry"] == "pinwheel")
        self.assertEqual(pinwheel["implementation_status"], "exact_affine")
        self.assertEqual(pinwheel["verification_status"], "PASS")
        self.assertTrue(pinwheel["has_local_reference"])
        self.assertTrue(pinwheel["has_canonical_patch"])
        self.assertTrue(pinwheel["strict_validation"])
        self.assertIn("exact-path", pinwheel["strength_tags"])
        self.assertIn("canonical-patch", pinwheel["verification_modes"])

        for geometry in ("spectre", "sphinx", "taylor-socolar"):
            family = next(family for family in families if family["geometry"] == geometry)
            self.assertEqual(family["implementation_status"], "true_substitution")
            self.assertEqual(family["verification_status"], "PASS")
            self.assertTrue(family["has_canonical_patch"])
            self.assertIn("canonical-patch", family["strength_tags"])
            self.assertIn("canonical-patch", family["verification_modes"])

    def test_detail_output_includes_promotion_blocker_and_live_observation_data(self) -> None:
        output = render_verification_strength_report(self.rows, output_format="detail")

        self.assertIn("shield (Shield)", output)
        self.assertIn("implementation_status: true_substitution", output)
        self.assertIn("verification_status: PASS", output)
        self.assertNotIn(
            "promotion_blocker: Experimental until manual visual review accepts the exact marked substitution implementation.",
            output,
        )
        self.assertIn("pinwheel (Pinwheel)", output)
        self.assertIn(
            "promotion_blocker: Experimental until manual visual review accepts the exact-affine implementation.",
            output,
        )
        self.assertIn("exact_reference_mode: pinwheel_exact", output)
        self.assertIn("robinson-triangles (Robinson Triangles)", output)
        self.assertIn("tuebingen-triangle (Tuebingen Triangle)", output)
        self.assertIn("archimedean-4-8-8 (Square-Octagon (4.8.8))", output)
        self.assertIn("archimedean-3-4-6-4 (Rhombitrihexagonal (3.4.6.4))", output)

    def test_detail_output_prints_failure_messages_when_present(self) -> None:
        synthetic_row = VerificationStrengthRow(
            geometry="fixture-geometry",
            display_name="Fixture Geometry",
            sample_mode="patch_depth",
            implementation_status="known_deviation",
            verification_status="FAIL",
            waived=False,
            blocking=True,
            strength_tags=("metadata",),
            verification_modes=("depth-expectations", "metadata"),
            promotion_blocker="Blocked by a synthetic fixture mismatch.",
            source_urls=("https://example.com/reference",),
            depths=(2,),
            exact_reference_mode=None,
            has_local_reference=False,
            has_canonical_patch=False,
            strict_validation=False,
            failure_codes=("fixture-mismatch",),
            observations=(
                ObservationSummary(
                    depth=2,
                    total_cells=17,
                    signature="deadbeef",
                    bounds_longest_span=12.5,
                    unique_orientation_tokens=3,
                    unique_chirality_tokens=1,
                ),
            ),
            failures=(
                FailureSummary(
                    code="fixture-mismatch",
                    message="Synthetic mismatch for renderer coverage.",
                    depth=2,
                ),
            ),
        )

        output = render_verification_strength_report((synthetic_row,), output_format="detail")

        self.assertIn("failure_codes: fixture-mismatch", output)
        self.assertIn("failures:", output)
        self.assertIn("fixture-mismatch[d2]: Synthetic mismatch for renderer coverage.", output)

    def test_live_verification_status_matches_reference_verifier(self) -> None:
        for geometry in (
            "pinwheel",
            "chair",
            "shield",
            "robinson-triangles",
            "tuebingen-triangle",
            "archimedean-4-8-8",
            "archimedean-3-4-6-4",
        ):
            self.assertEqual(
                self.rows_by_geometry[geometry].verification_status,
                self.live_results[geometry].status,
            )
            self.assertEqual(
                self.rows_by_geometry[geometry].blocking,
                self.live_results[geometry].blocking,
            )
            self.assertEqual(
                self.rows_by_geometry[geometry].waived,
                self.live_results[geometry].waived,
            )

    def test_canonical_patch_strength_tags_are_present_for_exact_patch_families(self) -> None:
        for geometry in (
            "spectre",
            "sphinx",
            "taylor-socolar",
            "robinson-triangles",
            "tuebingen-triangle",
        ):
            row = self.rows_by_geometry[geometry]
            self.assertTrue(row.has_canonical_patch)
            self.assertIn("canonical-patch", row.strength_tags)
            self.assertIn("canonical-patch", row.verification_modes)
            self.assertEqual(row.verification_status, "PASS")

    def test_main_can_write_json_output_to_a_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "verification-strength.json"

            exit_code = main(["--format", "json", "--output", str(output_path)])

            self.assertEqual(exit_code, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertIn("families", payload)


if __name__ == "__main__":
    unittest.main()
