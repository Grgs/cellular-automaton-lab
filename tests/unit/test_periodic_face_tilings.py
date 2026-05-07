import json
import unittest
from unittest import mock

from backend.simulation import periodic_face_tilings
from backend.simulation.periodic_face_tilings import PERIODIC_FACE_TILING_GEOMETRIES


class PeriodicFaceTilingRegistrySyncTests(unittest.TestCase):
    """Verify that PERIODIC_FACE_TILING_GEOMETRIES and periodic_face_patterns.json
    are kept in sync — every registered geometry must have a descriptor entry and
    every descriptor entry must be registered."""

    def test_registered_geometries_all_have_json_descriptors(self) -> None:
        descriptors = periodic_face_tilings._loaded_pattern_descriptors()
        missing = sorted(set(PERIODIC_FACE_TILING_GEOMETRIES) - set(descriptors))
        self.assertFalse(
            missing,
            f"Geometries registered in PERIODIC_FACE_TILING_GEOMETRIES but missing "
            f"from periodic_face_patterns.json: {missing}",
        )

    def test_json_descriptors_all_have_registered_geometries(self) -> None:
        descriptors = periodic_face_tilings._loaded_pattern_descriptors()
        orphaned = sorted(set(descriptors) - set(PERIODIC_FACE_TILING_GEOMETRIES))
        self.assertFalse(
            orphaned,
            f"Entries in periodic_face_patterns.json not registered in "
            f"PERIODIC_FACE_TILING_GEOMETRIES: {orphaned}",
        )


class PeriodicFaceTilingPayloadTests(unittest.TestCase):
    def setUp(self) -> None:
        periodic_face_tilings._loaded_pattern_descriptors.cache_clear()
        periodic_face_tilings._descriptor_registry.cache_clear()
        super().setUp()

    def tearDown(self) -> None:
        periodic_face_tilings._loaded_pattern_descriptors.cache_clear()
        periodic_face_tilings._descriptor_registry.cache_clear()
        super().tearDown()

    def test_loaded_pattern_descriptors_rejects_non_object_payload(self) -> None:
        with mock.patch(
            "backend.simulation.periodic_face_tilings.Path.read_text",
            return_value="[]",
        ):
            with self.assertRaisesRegex(ValueError, "invalid"):
                periodic_face_tilings._loaded_pattern_descriptors()

    def test_loaded_pattern_descriptors_rejects_invalid_face_entries(self) -> None:
        malformed_payload = {
            "archimedean-4-8-8": {
                "geometry": "archimedean-4-8-8",
                "label": "Square-Octagon (4.8.8)",
                "unit_width": 1.0,
                "unit_height": 1.0,
                "base_edge": 1.0,
                "min_dimension": 1,
                "min_x": 0.0,
                "min_y": 0.0,
                "max_x": 1.0,
                "max_y": 1.0,
                "cell_count_per_unit": 2,
                "faces": ["bad-face"],
            }
        }
        with mock.patch(
            "backend.simulation.periodic_face_tilings.Path.read_text",
            return_value=json.dumps(malformed_payload),
        ):
            with self.assertRaisesRegex(ValueError, "invalid"):
                periodic_face_tilings._loaded_pattern_descriptors()


if __name__ == "__main__":
    unittest.main()
