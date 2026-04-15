from dataclasses import replace
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.literature_reference_specs import REFERENCE_FAMILY_SPECS
from backend.simulation.topology_catalog import TOPOLOGY_VARIANTS
from backend.simulation.literature_reference_verification import (
    _canonical_patch_payload,
    _depth_topology_expectation_failures,
    _canonicalize_vertex_configuration,
    _local_reference_fixture_failures,
    _parse_periodic_face_cell_id,
    _periodic_face_sample_size,
    _periodic_face_descriptor_failures,
    _periodic_face_interior_vertex_configuration_frequencies,
    _periodic_face_interior_vertex_configurations,
    _verify_periodic_face_id_roundtrip,
    observe_reference_patch,
    verify_all_reference_families,
    verify_reference_family,
)
from backend.simulation.periodic_face_tilings import get_periodic_face_tiling_descriptor
from backend.simulation.topology import build_topology
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
        self.assertEqual(first.hole_count, second.hole_count)

    def test_reference_observation_records_connectivity_stats(self) -> None:
        observation = observe_reference_patch("pinwheel", 3)

        self.assertEqual(observation.connected_component_count, 1)
        self.assertEqual(observation.disconnected_component_sizes, ())
        self.assertEqual(observation.largest_component_size, observation.total_cells)
        self.assertEqual(observation.isolated_cell_count, 0)

    def test_reference_observation_records_surface_hole_stats(self) -> None:
        dodecagonal_square_triangle_observation = observe_reference_patch("dodecagonal-square-triangle", 3)
        shield_observation = observe_reference_patch("shield", 3)
        chair_observation = observe_reference_patch("chair", 3)
        hat_observation = observe_reference_patch("hat-monotile", 3)

        self.assertEqual(dodecagonal_square_triangle_observation.hole_count, 0)
        self.assertEqual(shield_observation.hole_count, 0)
        self.assertEqual(chair_observation.hole_count, 0)
        self.assertEqual(hat_observation.hole_count, 0)

    def test_reference_verifier_reports_passes_and_blocking_surface_or_connectivity_failures(self) -> None:
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

    def test_periodic_face_interior_vertex_configurations_match_zero_offset_family(self) -> None:
        descriptor = get_periodic_face_tiling_descriptor("archimedean-4-8-8")

        self.assertEqual(
            _periodic_face_interior_vertex_configurations(descriptor.build_faces(3, 3)),
            (("octagon", "octagon", "square"),),
        )

    def test_periodic_face_interior_vertex_configuration_frequencies_match_zero_offset_family(self) -> None:
        descriptor = get_periodic_face_tiling_descriptor("archimedean-4-8-8")

        self.assertEqual(
            _periodic_face_interior_vertex_configuration_frequencies(descriptor.build_faces(3, 3)),
            ((("octagon", "octagon", "square"), 24),),
        )

    def test_periodic_face_interior_vertex_configurations_match_odd_row_offset_family(self) -> None:
        descriptor = get_periodic_face_tiling_descriptor("trihexagonal-3-6-3-6")

        self.assertEqual(
            _periodic_face_interior_vertex_configurations(descriptor.build_faces(3, 3)),
            (("hexagon", "triangle-down", "hexagon", "triangle-up"),),
        )

    def test_periodic_face_interior_vertex_configuration_frequencies_match_odd_row_offset_family(self) -> None:
        descriptor = get_periodic_face_tiling_descriptor("trihexagonal-3-6-3-6")

        self.assertEqual(
            _periodic_face_interior_vertex_configuration_frequencies(descriptor.build_faces(3, 3)),
            ((("hexagon", "triangle-down", "hexagon", "triangle-up"), 13),),
        )

    def test_periodic_face_sample_size_defaults_to_3x3(self) -> None:
        spec = REFERENCE_FAMILY_SPECS["archimedean-4-8-8"]

        self.assertEqual(_periodic_face_sample_size(spec, 3), (3, 3))

    def test_periodic_face_sample_size_honors_explicit_override(self) -> None:
        spec = REFERENCE_FAMILY_SPECS["archimedean-4-8-8"]
        periodic_descriptor = spec.periodic_descriptor
        if periodic_descriptor is None:
            self.fail("archimedean-4-8-8 must define a periodic descriptor expectation")
        overridden_spec = replace(
            spec,
            periodic_descriptor=replace(periodic_descriptor, canonical_grid_size=(4, 4)),
        )

        self.assertEqual(_periodic_face_sample_size(overridden_spec, 3), (4, 4))

    def test_periodic_face_interior_vertex_configurations_exclude_boundary_vertices(self) -> None:
        descriptor = get_periodic_face_tiling_descriptor("cairo-pentagonal")

        self.assertEqual(
            _periodic_face_interior_vertex_configurations(descriptor.build_faces(3, 3)),
            (
                ("pentagon", "pentagon", "pentagon"),
                ("pentagon", "pentagon", "pentagon", "pentagon"),
            ),
        )

    def test_vertex_configuration_canonicalization_normalizes_rotation_and_direction(self) -> None:
        canonical = _canonicalize_vertex_configuration(
            ("hexagon", "triangle-down", "hexagon", "triangle-up")
        )

        self.assertEqual(
            canonical,
            _canonicalize_vertex_configuration(
                ("triangle-down", "hexagon", "triangle-up", "hexagon")
            ),
        )
        self.assertEqual(
            canonical,
            _canonicalize_vertex_configuration(
                ("triangle-up", "hexagon", "triangle-down", "hexagon")
            ),
        )

    def test_periodic_face_descriptor_reports_wrong_vertex_configuration_expectation(self) -> None:
        spec = REFERENCE_FAMILY_SPECS["archimedean-4-8-8"]
        periodic_descriptor = spec.periodic_descriptor
        if periodic_descriptor is None:
            self.fail("archimedean-4-8-8 must define a periodic descriptor expectation")
        wrong_periodic_descriptor = replace(
            periodic_descriptor,
            expected_interior_vertex_configurations=(("square", "square", "square"),),
        )
        wrong_spec = replace(spec, periodic_descriptor=wrong_periodic_descriptor)

        failures = _periodic_face_descriptor_failures(wrong_spec)

        self.assertTrue(
            any(
                failure.code == "descriptor-interior-vertex-configurations-mismatch"
                for failure in failures
            )
        )

    def test_periodic_face_descriptor_reports_wrong_vertex_configuration_frequency_expectation(self) -> None:
        spec = REFERENCE_FAMILY_SPECS["archimedean-4-8-8"]
        periodic_descriptor = spec.periodic_descriptor
        if periodic_descriptor is None:
            self.fail("archimedean-4-8-8 must define a periodic descriptor expectation")
        wrong_periodic_descriptor = replace(
            periodic_descriptor,
            expected_interior_vertex_configuration_frequencies=(
                (("octagon", "octagon", "square"), 23),
            ),
        )
        wrong_spec = replace(spec, periodic_descriptor=wrong_periodic_descriptor)

        failures = _periodic_face_descriptor_failures(wrong_spec)

        self.assertTrue(
            any(
                failure.code == "descriptor-interior-vertex-configuration-frequencies-mismatch"
                for failure in failures
            )
        )

    def test_periodic_face_descriptor_reports_wrong_dual_expectation(self) -> None:
        spec = REFERENCE_FAMILY_SPECS["archimedean-4-8-8"]
        periodic_descriptor = spec.periodic_descriptor
        if periodic_descriptor is None:
            self.fail("archimedean-4-8-8 must define a periodic descriptor expectation")
        wrong_periodic_descriptor = replace(
            periodic_descriptor,
            expected_dual_geometry="triakis-triangular",
        )
        wrong_spec = replace(spec, periodic_descriptor=wrong_periodic_descriptor)

        failures = _periodic_face_descriptor_failures(wrong_spec)

        self.assertTrue(
            any(
                failure.code in {
                    "descriptor-dual-geometry-not-reciprocal",
                    "descriptor-dual-structure-mismatch",
                }
                for failure in failures
            )
        )

    def test_periodic_face_descriptor_reports_wrong_dual_candidate_class_expectation(self) -> None:
        spec = REFERENCE_FAMILY_SPECS["archimedean-3-4-6-4"]
        periodic_descriptor = spec.periodic_descriptor
        if periodic_descriptor is None:
            self.fail("archimedean-3-4-6-4 must define a periodic descriptor expectation")
        wrong_spec = replace(
            spec,
            periodic_descriptor=replace(
                periodic_descriptor,
                expected_dual_candidate_geometries=("deltoidal-hexagonal",),
            ),
        )

        failures = _periodic_face_descriptor_failures(wrong_spec)

        self.assertTrue(
            any(
                failure.code == "descriptor-dual-candidate-class-mismatch"
                for failure in failures
            )
        )

    def test_periodic_face_descriptor_reports_wrong_dual_candidate_structure_expectation(self) -> None:
        spec = REFERENCE_FAMILY_SPECS["archimedean-3-3-4-3-4"]
        periodic_descriptor = spec.periodic_descriptor
        if periodic_descriptor is None:
            self.fail("archimedean-3-3-4-3-4 must define a periodic descriptor expectation")
        wrong_spec = replace(
            spec,
            periodic_descriptor=replace(
                periodic_descriptor,
                expected_dual_structure_signature=((5, 54),),
            ),
        )

        failures = _periodic_face_descriptor_failures(wrong_spec)

        self.assertTrue(
            any(
                failure.code == "descriptor-dual-candidate-structure-mismatch"
                for failure in failures
            )
        )

    def test_periodic_face_descriptor_reports_wrong_canonical_grid_size(self) -> None:
        spec = REFERENCE_FAMILY_SPECS["archimedean-4-8-8"]
        periodic_descriptor = spec.periodic_descriptor
        if periodic_descriptor is None:
            self.fail("archimedean-4-8-8 must define a periodic descriptor expectation")
        wrong_spec = replace(
            spec,
            periodic_descriptor=replace(periodic_descriptor, canonical_grid_size=(4, 4)),
        )

        failures = _periodic_face_descriptor_failures(wrong_spec)

        self.assertTrue(
            any(
                failure.code == "descriptor-interior-vertex-configuration-frequencies-mismatch"
                for failure in failures
            )
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

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        self.assertEqual(result.observations[0].total_cells, 2)
        self.assertEqual(result.observations[1].total_cells, 10)
        self.assertGreater(result.observations[1].bounds_longest_span, result.observations[0].bounds_longest_span)
        self.assertEqual(result.observations[-1].connected_component_count, 1)

    def test_chair_reference_verifier_accepts_true_substitution_chair_tiles(self) -> None:
        result = verify_reference_family("chair")

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        self.assertEqual(
            [observation.total_cells for observation in result.observations],
            [1, 4, 16, 64],
        )
        self.assertEqual(
            result.observations[-1].orientation_token_counts,
            (("0", 20), ("1", 16), ("2", 12), ("3", 16)),
        )

    def test_hat_reference_verifier_accepts_reflected_neighbor_pattern(self) -> None:
        result = verify_reference_family("hat-monotile")

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        self.assertEqual(result.observations[0].total_cells, 8)
        self.assertEqual(result.observations[0].unique_chirality_tokens, 2)
        self.assertIn(("left", "right"), result.observations[1].chirality_adjacency_pairs)
        self.assertGreaterEqual(
            result.observations[2].three_opposite_chirality_neighbor_cells,
            1,
        )
        self.assertEqual(result.observations[-1].hole_count, 0)

    def test_stronger_substitution_families_match_checked_in_local_reference_fixtures(self) -> None:
        for geometry, depth in (
            ("hat-monotile", 2),
            ("shield", 3),
            ("pinwheel", 3),
            ("dodecagonal-square-triangle", 3),
            ("chair", 3),
        ):
            with self.subTest(geometry=geometry, depth=depth):
                topology = build_topology(geometry, 0, 0, depth)
                self.assertEqual(
                    _local_reference_fixture_failures(geometry, depth, topology),
                    [],
                )

    def test_canonical_patch_payload_is_deterministic(self) -> None:
        first = _canonical_patch_payload(
            build_topology("dodecagonal-square-triangle", 0, 0, 3),
            include_id=False,
        )
        second = _canonical_patch_payload(
            build_topology("dodecagonal-square-triangle", 0, 0, 3),
            include_id=False,
        )

        self.assertEqual(first, second)

    def test_stronger_substitution_families_match_checked_in_canonical_patch_fixtures(self) -> None:
        for geometry, depth in (
            ("spectre", 3),
            ("taylor-socolar", 3),
            ("sphinx", 3),
            ("robinson-triangles", 3),
            ("tuebingen-triangle", 3),
            ("dodecagonal-square-triangle", 3),
            ("shield", 3),
            ("pinwheel", 3),
        ):
            with self.subTest(geometry=geometry, depth=depth):
                result = verify_reference_family(geometry)
                self.assertEqual(result.status, "PASS")
                self.assertFalse(
                    [
                        failure
                        for failure in result.failures
                        if failure.code == "canonical-patch-fixture-mismatch"
                    ]
                )

    def test_canonical_patch_fixture_reports_mismatch(self) -> None:
        topology = build_topology("shield", 0, 0, 3)
        observed_cells = _canonical_patch_payload(topology, include_id=False)
        bad_cells = list(observed_cells)
        bad_cells[0] = {
            **bad_cells[0],
            "kind": "not-a-shield",
        }
        bad_fixtures = {
            "shield": {
                "dense-depth-3": {
                    "depth": 3,
                    "include_id": False,
                    "cells": bad_cells,
                }
            }
        }

        expectation = REFERENCE_FAMILY_SPECS["shield"].depth_expectations[3]
        with patch(
            "backend.simulation.reference_verification.fixtures._load_canonical_reference_fixtures",
            return_value=bad_fixtures,
        ):
            failures = _depth_topology_expectation_failures(
                geometry="shield",
                depth=3,
                topology=topology,
                expectation=expectation,
            )

        self.assertTrue(
            any(failure.code == "canonical-patch-fixture-mismatch" for failure in failures)
        )

    def test_exact_substitution_canonical_patch_fixture_reports_mismatch(self) -> None:
        topology = build_topology("tuebingen-triangle", 0, 0, 3)
        observed_cells = _canonical_patch_payload(topology, include_id=False)
        bad_cells = list(observed_cells)
        bad_cells[0] = {
            **bad_cells[0],
            "kind": "not-a-tuebingen-triangle",
        }
        bad_fixtures = {
            "tuebingen-triangle": {
                "exact-depth-3": {
                    "depth": 3,
                    "include_id": False,
                    "cells": bad_cells,
                }
            }
        }

        expectation = REFERENCE_FAMILY_SPECS["tuebingen-triangle"].depth_expectations[3]
        with patch(
            "backend.simulation.reference_verification.fixtures._load_canonical_reference_fixtures",
            return_value=bad_fixtures,
        ):
            failures = _depth_topology_expectation_failures(
                geometry="tuebingen-triangle",
                depth=3,
                topology=topology,
                expectation=expectation,
            )

        self.assertTrue(
            any(failure.code == "canonical-patch-fixture-mismatch" for failure in failures)
        )

    def test_local_reference_fixture_reports_mismatch(self) -> None:
        topology = build_topology("hat-monotile", 0, 0, 2)
        bad_fixtures = {
            "hat-monotile": {
                "2": {
                    "hat:100": {
                        "root": {
                            "kind": "hat",
                            "orientation_token": "999",
                            "chirality_token": "right",
                            "decoration_tokens": None,
                            "area": 10.730401,
                            "degree": 3,
                        },
                        "neighbors": [],
                    }
                }
            }
        }

        with patch(
            "backend.simulation.reference_verification.fixtures._load_local_reference_fixtures",
            return_value=bad_fixtures,
        ):
            failures = _local_reference_fixture_failures("hat-monotile", 2, topology)

        self.assertTrue(
            any(failure.code == "local-reference-fixture-mismatch" for failure in failures)
        )

    def test_shield_reference_verifier_accepts_orientation_diversity(self) -> None:
        result = verify_reference_family("shield")

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        self.assertGreaterEqual(result.observations[0].unique_orientation_tokens, 10)
        self.assertGreaterEqual(result.observations[1].unique_orientation_tokens, 12)
        self.assertEqual(result.observations[-1].hole_count, 0)

    def test_chair_orientation_count_expectation_reports_mismatch(self) -> None:
        spec = REFERENCE_FAMILY_SPECS["chair"]
        expectation = replace(
            spec.depth_expectations[3],
            expected_orientation_token_counts=(("0", 20), ("1", 16), ("2", 11), ("3", 17)),
        )
        topology = build_topology("chair", 0, 0, 3)

        failures = _depth_topology_expectation_failures(
            geometry="chair",
            depth=3,
            topology=topology,
            expectation=expectation,
        )

        self.assertTrue(
            any(failure.code == "unexpected-orientation-token-counts" for failure in failures)
        )

    def test_dodecagonal_square_triangle_reference_verifier_accepts_dense_hole_free_reference_patch(self) -> None:
        result = verify_reference_family("dodecagonal-square-triangle")

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        depth_three_observation = result.observations[-1]
        self.assertEqual(depth_three_observation.depth, 3)
        self.assertEqual(depth_three_observation.total_cells, 462)
        self.assertEqual(depth_three_observation.connected_component_count, 1)
        self.assertEqual(depth_three_observation.hole_count, 0)
        self.assertEqual(
            depth_three_observation.kind_counts,
            (
                ("dodecagonal-square-triangle-square", 140),
                ("dodecagonal-square-triangle-triangle", 322),
            ),
        )
        self.assertEqual(depth_three_observation.signature, "f66a7171fb67")

    def test_pinwheel_reference_verifier_tracks_expanding_support(self) -> None:
        result = verify_reference_family("pinwheel")

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        spans = [observation.bounds_longest_span for observation in result.observations]
        self.assertTrue(
            all(left < right for left, right in zip(spans, spans[1:]))
        )

    def test_reference_tool_returns_failure_while_blocking_surface_or_connectivity_regressions_exist(self) -> None:
        self.assertEqual(verify_reference_main(), 0)


if __name__ == "__main__":
    unittest.main()
