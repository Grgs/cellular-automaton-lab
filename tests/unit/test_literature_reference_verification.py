import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.literature_reference_specs import REFERENCE_FAMILY_SPECS
from backend.simulation.topology_catalog import TOPOLOGY_VARIANTS
from backend.simulation.literature_reference_verification import (
    _parse_periodic_face_cell_id,
    _verify_periodic_face_id_roundtrip,
    observe_reference_patch,
    verify_all_reference_families,
    verify_reference_family,
)
from backend.simulation.periodic_face_tilings import get_periodic_face_tiling_descriptor
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
        self.assertEqual(first.adjacency_pairs, second.adjacency_pairs)
        self.assertEqual(first.connected_component_count, second.connected_component_count)
        self.assertEqual(first.disconnected_component_sizes, second.disconnected_component_sizes)

    def test_reference_observation_records_connectivity_stats(self) -> None:
        observation = observe_reference_patch("shield", 3)

        self.assertGreater(observation.connected_component_count, 1)
        self.assertTrue(observation.disconnected_component_sizes)
        self.assertEqual(
            observation.largest_component_size,
            max(observation.disconnected_component_sizes),
        )
        self.assertGreater(observation.isolated_cell_count, 0)

    def test_reference_verifier_reports_passes_and_blocking_connectivity_failures(self) -> None:
        results = {
            result.geometry: result
            for result in verify_all_reference_families()
        }

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
        self.assertEqual(results["square-triangle"].status, "PASS")
        self.assertEqual(results["shield"].status, "FAIL")
        self.assertEqual(results["pinwheel"].status, "FAIL")
        self.assertFalse(results["chair"].waived)
        self.assertFalse(results["hat-monotile"].waived)
        self.assertFalse(results["shield"].waived)
        self.assertFalse(results["pinwheel"].waived)
        self.assertFalse(results["chair"].blocking)
        self.assertFalse(results["hat-monotile"].blocking)
        self.assertTrue(results["shield"].blocking)
        self.assertTrue(results["pinwheel"].blocking)

    def test_connected_representative_families_remain_connected_under_verifier(self) -> None:
        for geometry in (
            "chair",
            "hat-monotile",
            "square-triangle",
            "tuebingen-triangle",
        ):
            with self.subTest(geometry=geometry):
                result = verify_reference_family(geometry)
                deepest_observation = result.observations[-1]
                self.assertEqual(result.status, "PASS")
                self.assertEqual(deepest_observation.connected_component_count, 1)
                self.assertEqual(deepest_observation.disconnected_component_sizes, ())

    def test_regular_grid_reference_verifier_tracks_open_boundary_histogram(self) -> None:
        result = verify_reference_family("square")

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        self.assertEqual(result.observations[0].degree_histogram, ((3, 4), (5, 4), (8, 1)))

    def test_periodic_face_reference_verifier_checks_descriptor_family(self) -> None:
        result = verify_reference_family("cairo-pentagonal")

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        self.assertEqual(result.observations[0].signature, "e33351b2ed77")
        self.assertEqual(result.observations[0].degree_histogram, ((2, 3), (3, 8), (4, 13), (5, 12)))

    def test_periodic_face_reference_verifier_checks_zero_offset_family(self) -> None:
        result = verify_reference_family("archimedean-4-8-8")

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        self.assertEqual(
            result.observations[0].degree_histogram,
            ((1, 4), (2, 8), (4, 4), (6, 4), (7, 4), (8, 1)),
        )

    def test_periodic_face_id_pattern_roundtrip_matches_generated_cells(self) -> None:
        descriptor = get_periodic_face_tiling_descriptor("cairo-pentagonal")

        cells = descriptor.build_faces(3, 3)
        self.assertTrue(cells)
        for cell in cells:
            parsed = _parse_periodic_face_cell_id(descriptor, cell.id)
            self.assertIsNotNone(parsed)
            self.assertIsNone(_verify_periodic_face_id_roundtrip(descriptor, cell))

    def test_pinwheel_reference_verifier_uses_exact_path(self) -> None:
        result = verify_reference_family("pinwheel")

        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any(failure.code == "disconnected-topology-graph" for failure in result.failures))
        self.assertEqual(result.observations[0].total_cells, 2)
        self.assertEqual(result.observations[1].total_cells, 10)
        self.assertGreater(result.observations[1].bounds_longest_span, result.observations[0].bounds_longest_span)

    def test_chair_reference_verifier_accepts_multiscale_chair_tiles(self) -> None:
        result = verify_reference_family("chair")

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        self.assertGreaterEqual(
            dict(result.observations[1].unique_polygon_areas_by_kind)["chair"],
            2,
        )

    def test_hat_reference_verifier_accepts_reflected_neighbor_pattern(self) -> None:
        result = verify_reference_family("hat-monotile")

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        self.assertIn(("left", "right"), result.observations[1].chirality_adjacency_pairs)
        self.assertGreaterEqual(
            result.observations[2].three_opposite_chirality_neighbor_cells,
            1,
        )

    def test_shield_reference_verifier_accepts_decoration_variants(self) -> None:
        result = verify_reference_family("shield")

        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any(failure.code == "disconnected-topology-graph" for failure in result.failures))
        decoration_counts = dict(result.observations[1].unique_decoration_variants_by_kind)
        self.assertGreaterEqual(decoration_counts["shield-shield"], 2)
        self.assertGreaterEqual(decoration_counts["shield-triangle"], 2)

    def test_pinwheel_reference_verifier_tracks_expanding_support(self) -> None:
        result = verify_reference_family("pinwheel")

        self.assertEqual(result.status, "FAIL")
        self.assertTrue(any(failure.code == "disconnected-topology-graph" for failure in result.failures))
        spans = [observation.bounds_longest_span for observation in result.observations]
        self.assertTrue(
            all(left < right for left, right in zip(spans, spans[1:]))
        )

    def test_reference_tool_returns_failure_while_blocking_connectivity_regressions_exist(self) -> None:
        self.assertEqual(verify_reference_main(), 1)


if __name__ == "__main__":
    unittest.main()
