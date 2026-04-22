import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mine_dodecagonal_square_triangle_structure import (
    build_mining_summary,
    main,
)


class MineDodecagonalSquareTriangleStructureToolTests(unittest.TestCase):
    def test_build_mining_summary_reports_repeated_local_classes_and_square_candidates(self) -> None:
        summary = build_mining_summary(
            max_source_depth=6,
            neighborhood_radius=2,
            region_radius=3,
            max_candidate_size=8,
            min_candidate_size=2,
            beam_width=20,
            top_groups=5,
        )

        self.assertGreater(summary.source_cell_count, 1000)
        self.assertGreater(summary.max_available_depth, 20)
        self.assertTrue(summary.local_neighborhood_classes)
        self.assertGreaterEqual(summary.local_neighborhood_classes[0].count, 10)
        self.assertTrue(summary.macro_candidate_groups)
        top_group = summary.macro_candidate_groups[0]
        self.assertEqual(top_group.macro_kind, "square")
        self.assertEqual(top_group.cell_count, 2)
        self.assertGreaterEqual(top_group.occurrence_count, 10)
        self.assertTrue(summary.seeded_supertile_groups)
        top_supertile = summary.seeded_supertile_groups[0]
        self.assertEqual(top_supertile.seed_macro_kind, "square")
        self.assertEqual(top_supertile.seed_cell_count, 2)
        self.assertEqual(top_supertile.grown_cell_count, 5)
        self.assertGreaterEqual(top_supertile.occurrence_count, 10)
        self.assertGreaterEqual(top_supertile.selected_slot_count, 3)
        self.assertEqual(len(top_supertile.boundary_direction_histogram), 8)
        self.assertIn(("square:-", 1), top_supertile.marked_cell_signature)
        self.assertIn(("triangle:red", 4), top_supertile.marked_cell_signature)
        self.assertTrue(summary.inflation_candidate_groups)
        top_inflation = summary.inflation_candidate_groups[0]
        self.assertEqual(top_inflation.seed_macro_kind, "square")
        self.assertEqual(top_inflation.base_cell_count, 5)
        self.assertEqual(top_inflation.grown_cell_count, 10)
        self.assertGreaterEqual(top_inflation.occurrence_count, 10)
        self.assertGreaterEqual(top_inflation.combo_size, 4)
        self.assertGreater(top_inflation.inflation_estimate, 1.5)
        self.assertGreaterEqual(len(top_inflation.boundary_direction_histogram), 10)
        self.assertIn((90, 2), top_inflation.boundary_direction_histogram)
        self.assertTrue(summary.boundary_template_groups)
        top_template = summary.boundary_template_groups[0]
        self.assertEqual(top_template.seed_macro_kind, "square")
        self.assertEqual(top_template.base_cell_count, 5)
        self.assertEqual(top_template.candidate_cell_count, 10)
        self.assertGreaterEqual(top_template.template_match_count, 7)
        self.assertGreaterEqual(top_template.template_variant_count, 2)
        self.assertEqual(len(top_template.canonical_vertices), 14)
        self.assertTrue(top_template.line_families)
        self.assertEqual(top_template.line_families[0].axis_angle, 0)
        self.assertIn(120, [family.axis_angle for family in top_template.line_families])
        self.assertTrue(summary.supertile_decomposition_groups)
        top_decomposition = summary.supertile_decomposition_groups[0]
        self.assertEqual(top_decomposition.seed_macro_kind, "square")
        self.assertEqual(top_decomposition.base_cell_count, 5)
        self.assertEqual(top_decomposition.candidate_cell_count, 10)
        self.assertGreaterEqual(top_decomposition.template_match_count, 7)
        self.assertEqual(len(top_decomposition.line_equations), 10)
        self.assertTrue(top_decomposition.component_groups)
        self.assertEqual(top_decomposition.component_groups[0].component_macro_kind, "triangle")
        self.assertEqual(top_decomposition.component_groups[0].cell_count, 1)
        self.assertGreaterEqual(top_decomposition.component_groups[0].occurrence_count, 10)

    def test_main_json_output_contains_expected_summary_fields(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = main([
                "--max-source-depth", "6",
                "--top-groups", "3",
                "--json",
            ])

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["source_cell_count"], 4999)
        self.assertEqual(payload["seed_index"], 3557)
        self.assertEqual(payload["max_available_depth"], 61)
        self.assertEqual(payload["analyzed_root_count"], 84)
        self.assertTrue(payload["local_neighborhood_classes"])
        self.assertTrue(payload["macro_candidate_groups"])
        self.assertEqual(payload["macro_candidate_groups"][0]["macro_kind"], "square")
        self.assertEqual(payload["macro_candidate_groups"][0]["cell_count"], 2)
        self.assertTrue(payload["seeded_supertile_groups"])
        self.assertEqual(payload["seeded_supertile_groups"][0]["seed_macro_kind"], "square")
        self.assertEqual(payload["seeded_supertile_groups"][0]["grown_cell_count"], 5)
        self.assertTrue(payload["inflation_candidate_groups"])
        self.assertEqual(payload["inflation_candidate_groups"][0]["seed_macro_kind"], "square")
        self.assertEqual(payload["inflation_candidate_groups"][0]["grown_cell_count"], 10)
        self.assertTrue(payload["boundary_template_groups"])
        self.assertEqual(payload["boundary_template_groups"][0]["seed_macro_kind"], "square")
        self.assertEqual(payload["boundary_template_groups"][0]["candidate_cell_count"], 10)
        self.assertTrue(payload["supertile_decomposition_groups"])
        self.assertEqual(payload["supertile_decomposition_groups"][0]["seed_macro_kind"], "square")
        self.assertEqual(payload["supertile_decomposition_groups"][0]["candidate_cell_count"], 10)


if __name__ == "__main__":
    unittest.main()
