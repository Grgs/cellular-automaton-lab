import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.literature_reference_specs import REFERENCE_FAMILY_SPECS
from backend.simulation.topology_catalog import TOPOLOGY_VARIANTS
from backend.simulation.literature_reference_verification import (
    observe_reference_patch,
    verify_all_reference_families,
    verify_reference_family,
)
from tools.verify_reference_tilings import main as verify_reference_main


class LiteratureReferenceVerificationTests(unittest.TestCase):
    def test_reference_specs_cover_full_catalog(self) -> None:
        self.assertEqual(
            set(REFERENCE_FAMILY_SPECS),
            {definition.geometry_key for definition in TOPOLOGY_VARIANTS},
        )
        self.assertNotIn("not-a-geometry", REFERENCE_FAMILY_SPECS)

    def test_reference_patch_signatures_are_deterministic(self) -> None:
        first = observe_reference_patch("pinwheel", 3)
        second = observe_reference_patch("pinwheel", 3)

        self.assertEqual(first.signature, second.signature)
        self.assertEqual(first.kind_counts, second.kind_counts)
        self.assertEqual(first.tile_family_counts, second.tile_family_counts)
        self.assertEqual(first.adjacency_pairs, second.adjacency_pairs)
        self.assertEqual(first.chirality_token_counts, second.chirality_token_counts)
        self.assertEqual(first.connected_component_count, second.connected_component_count)
        self.assertEqual(first.disconnected_component_sizes, second.disconnected_component_sizes)
        self.assertEqual(first.hole_count, second.hole_count)

    def test_reference_observation_records_connectivity_stats(self) -> None:
        observation = observe_reference_patch("pinwheel", 3)

        self.assertEqual(observation.connected_component_count, 1)
        self.assertEqual(observation.disconnected_component_sizes, ())
        self.assertEqual(observation.largest_component_size, observation.total_cells)
        self.assertEqual(observation.isolated_cell_count, 0)

    def test_reference_observation_records_surface_hole_stats(self) -> None:
        dodecagonal_square_triangle_observation = observe_reference_patch(
            "dodecagonal-square-triangle", 3
        )
        shield_observation = observe_reference_patch("shield", 3)
        chair_observation = observe_reference_patch("chair", 3)
        hat_observation = observe_reference_patch("hat-monotile", 3)

        self.assertEqual(dodecagonal_square_triangle_observation.hole_count, 0)
        self.assertEqual(shield_observation.hole_count, 0)
        self.assertEqual(chair_observation.hole_count, 0)
        self.assertEqual(hat_observation.hole_count, 0)
        self.assertEqual(observe_reference_patch("pinwheel", 3).hole_count, 0)

    def test_reference_verifier_reports_passes_and_blocking_surface_or_connectivity_failures(
        self,
    ) -> None:
        results = {result.geometry: result for result in verify_all_reference_families()}

        self.assertEqual(results["square"].status, "PASS")
        self.assertEqual(results["hex"].status, "PASS")
        self.assertEqual(results["triangle"].status, "PASS")
        self.assertEqual(results["archimedean-4-8-8"].status, "PASS")
        self.assertEqual(results["cairo-pentagonal"].status, "PASS")
        self.assertEqual(results["deltoidal-hexagonal"].status, "PASS")
        self.assertEqual(results["snub-square-dual"].status, "PASS")
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
        self.assertEqual(results["dodecagonal-square-triangle"].status, "PASS")
        self.assertEqual(results["shield"].status, "PASS")
        self.assertEqual(results["pinwheel"].status, "PASS")
        self.assertFalse(results["chair"].waived)
        self.assertFalse(results["hat-monotile"].waived)
        self.assertFalse(results["shield"].waived)
        self.assertFalse(results["pinwheel"].waived)
        self.assertFalse(results["chair"].blocking)
        self.assertFalse(results["hat-monotile"].blocking)
        self.assertFalse(results["dodecagonal-square-triangle"].blocking)
        self.assertFalse(results["shield"].blocking)
        self.assertFalse(results["pinwheel"].blocking)

    def test_connected_representative_families_remain_connected_under_observation(self) -> None:
        for geometry in (
            "chair",
            "hat-monotile",
            "pinwheel",
            "dodecagonal-square-triangle",
            "shield",
            "tuebingen-triangle",
        ):
            with self.subTest(geometry=geometry):
                result = verify_reference_family(geometry)
                deepest_observation = result.observations[-1]
                self.assertEqual(deepest_observation.connected_component_count, 1)
                self.assertEqual(deepest_observation.disconnected_component_sizes, ())

    def test_regular_grid_reference_verifier_tracks_open_boundary_histogram(self) -> None:
        result = verify_reference_family("square")

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        self.assertEqual(result.observations[0].degree_histogram, ((3, 4), (5, 4), (8, 1)))

    def test_reference_tool_returns_failure_while_blocking_surface_or_connectivity_regressions_exist(
        self,
    ) -> None:
        self.assertEqual(verify_reference_main(), 0)


if __name__ == "__main__":
    unittest.main()
