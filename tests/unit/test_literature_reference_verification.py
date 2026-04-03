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
    def test_reference_specs_cover_only_staged_families(self) -> None:
        self.assertEqual(
            set(REFERENCE_FAMILY_SPECS),
            {
                "hat-monotile",
                "tuebingen-triangle",
                "square-triangle",
                "shield",
                "pinwheel",
            },
        )

    def test_reference_patch_signatures_are_deterministic(self) -> None:
        first = observe_reference_patch("pinwheel", 3)
        second = observe_reference_patch("pinwheel", 3)

        self.assertEqual(first.signature, second.signature)
        self.assertEqual(first.kind_counts, second.kind_counts)
        self.assertEqual(first.adjacency_pairs, second.adjacency_pairs)

    def test_reference_verifier_reports_staged_statuses(self) -> None:
        results = {
            result.geometry: result
            for result in verify_all_reference_families()
        }

        self.assertEqual(results["hat-monotile"].status, "KNOWN_DEVIATION")
        self.assertEqual(results["tuebingen-triangle"].status, "KNOWN_DEVIATION")
        self.assertEqual(results["square-triangle"].status, "KNOWN_DEVIATION")
        self.assertEqual(results["shield"].status, "PASS")
        self.assertEqual(results["pinwheel"].status, "PASS")
        self.assertTrue(all(not result.blocking for result in results.values()))

    def test_pinwheel_reference_verifier_uses_exact_path(self) -> None:
        result = verify_reference_family("pinwheel")

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        self.assertEqual(result.observations[0].total_cells, 2)
        self.assertEqual(result.observations[1].total_cells, 10)

    def test_reference_tool_returns_success_under_staged_waivers(self) -> None:
        self.assertEqual(verify_reference_main(), 0)


if __name__ == "__main__":
    unittest.main()
