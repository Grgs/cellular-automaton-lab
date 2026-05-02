from dataclasses import replace
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.literature_reference_specs import REFERENCE_FAMILY_SPECS
from backend.simulation.literature_reference_verification import (
    _canonicalize_vertex_configuration,
    _parse_periodic_face_cell_id,
    _periodic_face_descriptor_failures,
    _periodic_face_interior_vertex_configuration_frequencies,
    _periodic_face_interior_vertex_configurations,
    _periodic_face_sample_size,
    _verify_periodic_face_id_roundtrip,
    verify_reference_family,
)
from backend.simulation.periodic_face_tilings import get_periodic_face_tiling_descriptor


class LiteratureReferenceVerificationPeriodicTests(unittest.TestCase):
    def test_periodic_face_reference_verifier_checks_descriptor_family(self) -> None:
        result = verify_reference_family("cairo-pentagonal")

        self.assertEqual(result.status, "PASS")
        self.assertFalse(result.failures)
        self.assertEqual(result.observations[0].signature, "e33351b2ed77")
        self.assertEqual(
            result.observations[0].degree_histogram, ((2, 3), (3, 8), (4, 13), (5, 12))
        )

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

    def test_periodic_face_interior_vertex_configuration_frequencies_match_zero_offset_family(
        self,
    ) -> None:
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

    def test_periodic_face_interior_vertex_configuration_frequencies_match_odd_row_offset_family(
        self,
    ) -> None:
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

    def test_periodic_face_descriptor_reports_wrong_vertex_configuration_frequency_expectation(
        self,
    ) -> None:
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
                failure.code
                in {
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
            any(failure.code == "descriptor-dual-candidate-class-mismatch" for failure in failures)
        )

    def test_periodic_face_descriptor_reports_wrong_dual_candidate_structure_expectation(
        self,
    ) -> None:
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


if __name__ == "__main__":
    unittest.main()
