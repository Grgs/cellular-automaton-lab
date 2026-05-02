from dataclasses import replace
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.literature_reference_specs import REFERENCE_FAMILY_SPECS
from backend.simulation.literature_reference_verification import (
    _canonical_patch_payload,
    _depth_topology_expectation_failures,
    _local_reference_fixture_failures,
    _load_canonical_reference_fixtures,
    verify_reference_family,
)
from backend.simulation.topology import build_topology


class LiteratureReferenceVerificationAperiodicTests(unittest.TestCase):
    def test_pinwheel_reference_verifier_uses_exact_path(self) -> None:
        from backend.simulation.aperiodic_pinwheel import collect_pinwheel_exact_records

        result = verify_reference_family("pinwheel")

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        self.assertEqual(
            [observation.total_cells for observation in result.observations],
            [2, 10, 50, 250],
        )
        self.assertGreater(
            result.observations[1].bounds_longest_span, result.observations[0].bounds_longest_span
        )
        self.assertEqual(result.observations[-1].connected_component_count, 1)
        exact_ids = tuple(sorted(record["id"] for record in collect_pinwheel_exact_records(3)))
        self.assertEqual(len(exact_ids), 250)
        self.assertTrue(any(record_id.startswith("pinwheel:root0") for record_id in exact_ids))
        self.assertTrue(any(record_id.startswith("pinwheel:root1") for record_id in exact_ids))
        self.assertTrue(
            all(
                record_id.startswith("pinwheel:root0") or record_id.startswith("pinwheel:root1")
                for record_id in exact_ids
            )
        )

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

    def test_broadened_direct_canonical_patch_payloads_match_checked_in_fixtures(self) -> None:
        fixtures = _load_canonical_reference_fixtures()

        for geometry, depth in (
            ("robinson-triangles", 1),
            ("robinson-triangles", 3),
            ("tuebingen-triangle", 1),
            ("tuebingen-triangle", 3),
            ("dodecagonal-square-triangle", 1),
            ("dodecagonal-square-triangle", 3),
            ("shield", 1),
            ("shield", 3),
            ("pinwheel", 1),
            ("pinwheel", 3),
        ):
            with self.subTest(geometry=geometry, depth=depth):
                expectation = REFERENCE_FAMILY_SPECS[geometry].depth_expectations[depth]
                fixture_key = expectation.canonical_patch_fixture_key
                if fixture_key is None:
                    self.fail(f"{geometry} depth {depth} is missing a canonical patch fixture key.")
                topology = build_topology(geometry, 0, 0, depth)
                fixture = fixtures[geometry][fixture_key]
                self.assertEqual(
                    bool(fixture["include_id"]),
                    expectation.canonical_patch_include_id,
                )
                self.assertEqual(
                    _canonical_patch_payload(
                        topology,
                        include_id=expectation.canonical_patch_include_id,
                    ),
                    fixture["cells"],
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

    def test_canonical_patch_fixture_reports_include_id_mismatch(self) -> None:
        topology = build_topology("pinwheel", 0, 0, 1)
        bad_fixtures = {
            "pinwheel": {
                "exact-depth-1": {
                    "depth": 1,
                    "include_id": False,
                    "cells": _canonical_patch_payload(topology, include_id=False),
                }
            }
        }

        expectation = REFERENCE_FAMILY_SPECS["pinwheel"].depth_expectations[1]
        with patch(
            "backend.simulation.reference_verification.fixtures._load_canonical_reference_fixtures",
            return_value=bad_fixtures,
        ):
            failures = _depth_topology_expectation_failures(
                geometry="pinwheel",
                depth=1,
                topology=topology,
                expectation=expectation,
            )

        self.assertTrue(
            any(
                failure.code == "canonical-patch-fixture-include-id-mismatch"
                for failure in failures
            )
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
        self.assertGreaterEqual(result.observations[0].unique_orientation_tokens, 1)
        self.assertGreaterEqual(result.observations[1].unique_orientation_tokens, 10)
        self.assertGreaterEqual(result.observations[2].unique_orientation_tokens, 12)
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

    def test_dodecagonal_square_triangle_marked_metadata_count_expectations_report_mismatch(
        self,
    ) -> None:
        spec = REFERENCE_FAMILY_SPECS["dodecagonal-square-triangle"]
        expectation = replace(
            spec.depth_expectations[3],
            expected_tile_family_counts=(("not-dodecagonal-square-triangle", 25),),
            expected_chirality_token_counts=(("blue", 8), ("red", 6), ("yellow", 4)),
        )
        topology = build_topology("dodecagonal-square-triangle", 0, 0, 3)

        failures = _depth_topology_expectation_failures(
            geometry="dodecagonal-square-triangle",
            depth=3,
            topology=topology,
            expectation=expectation,
        )

        self.assertTrue(
            any(failure.code == "unexpected-tile-family-counts" for failure in failures)
        )
        self.assertTrue(
            any(failure.code == "unexpected-chirality-token-counts" for failure in failures)
        )

    def test_dodecagonal_square_triangle_reference_verifier_accepts_dense_hole_free_reference_patch(
        self,
    ) -> None:
        result = verify_reference_family("dodecagonal-square-triangle")

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        depth_three_observation = result.observations[-1]
        self.assertEqual(depth_three_observation.depth, 3)
        self.assertEqual(depth_three_observation.total_cells, 25)
        self.assertEqual(depth_three_observation.connected_component_count, 1)
        self.assertEqual(depth_three_observation.hole_count, 0)
        self.assertEqual(
            depth_three_observation.kind_counts,
            (
                ("dodecagonal-square-triangle-square", 7),
                ("dodecagonal-square-triangle-triangle", 18),
            ),
        )
        self.assertEqual(
            depth_three_observation.tile_family_counts,
            (("dodecagonal-square-triangle", 25),),
        )
        self.assertEqual(
            depth_three_observation.orientation_token_counts,
            (
                ("0", 4),
                ("120", 3),
                ("150", 1),
                ("180", 3),
                ("210", 2),
                ("240", 2),
                ("270", 1),
                ("30", 2),
                ("300", 2),
                ("330", 1),
                ("60", 3),
                ("90", 1),
            ),
        )
        self.assertEqual(
            depth_three_observation.chirality_token_counts,
            (
                ("blue", 4),
                ("red", 6),
                ("yellow", 8),
            ),
        )
        self.assertEqual(
            depth_three_observation.degree_histogram,
            ((1, 6), (2, 6), (3, 8), (4, 5)),
        )
        self.assertEqual(
            depth_three_observation.signature,
            "f264950423a5",  # pragma: allowlist secret
        )

    def test_pinwheel_reference_verifier_tracks_expanding_support(self) -> None:
        result = verify_reference_family("pinwheel")

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        spans = [observation.bounds_longest_span for observation in result.observations]
        self.assertTrue(all(left < right for left, right in zip(spans, spans[1:])))


if __name__ == "__main__":
    unittest.main()
