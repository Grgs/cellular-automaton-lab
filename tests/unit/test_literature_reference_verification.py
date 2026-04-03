import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.literature_reference_specs import REFERENCE_FAMILY_SPECS
from backend.simulation.literature_reference_verification import (
    observe_reference_patch,
    verify_all_reference_families,
    verify_reference_family,
)
from tools.verify_reference_tilings import main as verify_reference_main


class LiteratureReferenceVerificationTests(unittest.TestCase):
    def test_reference_specs_cover_selected_aperiodic_families(self) -> None:
        self.assertEqual(
            set(REFERENCE_FAMILY_SPECS),
            {
                "ammann-beenker",
                "chair",
                "hat-monotile",
                "penrose-p2-kite-dart",
                "penrose-p3-rhombs",
                "penrose-p3-rhombs-vertex",
                "pinwheel",
                "robinson-triangles",
                "spectre",
                "sphinx",
                "square-triangle",
                "taylor-socolar",
                "tuebingen-triangle",
                "shield",
            },
        )
        self.assertNotIn("square", REFERENCE_FAMILY_SPECS)

    def test_reference_patch_signatures_are_deterministic(self) -> None:
        first = observe_reference_patch("pinwheel", 3)
        second = observe_reference_patch("pinwheel", 3)

        self.assertEqual(first.signature, second.signature)
        self.assertEqual(first.kind_counts, second.kind_counts)
        self.assertEqual(first.adjacency_pairs, second.adjacency_pairs)

    def test_reference_verifier_reports_passes_for_specd_families(self) -> None:
        results = {
            result.geometry: result
            for result in verify_all_reference_families()
        }

        self.assertEqual(results["ammann-beenker"].status, "PASS")
        self.assertEqual(results["chair"].status, "PASS")
        self.assertEqual(results["hat-monotile"].status, "PASS")
        self.assertEqual(results["penrose-p2-kite-dart"].status, "PASS")
        self.assertEqual(results["penrose-p3-rhombs"].status, "PASS")
        self.assertEqual(results["penrose-p3-rhombs-vertex"].status, "PASS")
        self.assertEqual(results["tuebingen-triangle"].status, "PASS")
        self.assertEqual(results["taylor-socolar"].status, "PASS")
        self.assertEqual(results["spectre"].status, "PASS")
        self.assertEqual(results["sphinx"].status, "PASS")
        self.assertEqual(results["robinson-triangles"].status, "PASS")
        self.assertEqual(results["square-triangle"].status, "PASS")
        self.assertEqual(results["shield"].status, "PASS")
        self.assertEqual(results["pinwheel"].status, "PASS")
        self.assertTrue(all(not result.waived for result in results.values()))
        self.assertTrue(all(not result.blocking for result in results.values()))

    def test_pinwheel_reference_verifier_uses_exact_path(self) -> None:
        result = verify_reference_family("pinwheel")

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        self.assertEqual(result.observations[0].total_cells, 2)
        self.assertEqual(result.observations[1].total_cells, 10)

    def test_reference_tool_returns_success_for_current_spec_set(self) -> None:
        self.assertEqual(verify_reference_main(), 0)


if __name__ == "__main__":
    unittest.main()
