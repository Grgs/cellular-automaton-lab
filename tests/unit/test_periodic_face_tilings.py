import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from backend.simulation import periodic_face_tilings
from backend.simulation.periodic_face_pattern_data import load_periodic_face_pattern_payloads
from backend.simulation.periodic_face_tilings import PERIODIC_FACE_TILING_GEOMETRIES
from backend.simulation.topology_family_manifest import TOPOLOGY_FAMILY_MANIFEST


class PeriodicFaceTilingRegistrySyncTests(unittest.TestCase):
    """Verify that registered geometries and descriptor files stay in sync."""

    def test_registered_geometries_all_have_json_descriptors(self) -> None:
        descriptors = periodic_face_tilings._loaded_pattern_descriptors()
        missing = sorted(set(PERIODIC_FACE_TILING_GEOMETRIES) - set(descriptors))
        self.assertFalse(
            missing,
            f"Geometries registered in PERIODIC_FACE_TILING_GEOMETRIES but missing "
            f"from the periodic-face descriptor directory: {missing}",
        )

    def test_json_descriptors_all_have_registered_geometries(self) -> None:
        descriptors = periodic_face_tilings._loaded_pattern_descriptors()
        orphaned = sorted(set(descriptors) - set(PERIODIC_FACE_TILING_GEOMETRIES))
        self.assertFalse(
            orphaned,
            f"Periodic-face descriptor files not registered in "
            f"PERIODIC_FACE_TILING_GEOMETRIES: {orphaned}",
        )

    def test_catalog_labels_are_injected_from_family_manifest(self) -> None:
        raw_descriptors = load_periodic_face_pattern_payloads()
        descriptors = periodic_face_tilings._loaded_pattern_descriptors()

        for geometry, raw_descriptor in raw_descriptors.items():
            with self.subTest(geometry=geometry):
                self.assertNotIn("label", raw_descriptor)
                self.assertEqual(
                    descriptors[geometry].label, TOPOLOGY_FAMILY_MANIFEST[geometry].label
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

    def test_loaded_pattern_descriptors_rejects_invalid_face_entries(self) -> None:
        malformed_descriptor = {
            "geometry": "archimedean-4-8-8",
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
        with mock.patch(
            "backend.simulation.periodic_face_tilings.load_periodic_face_pattern_payloads",
            return_value={"archimedean-4-8-8": malformed_descriptor},
        ):
            with self.assertRaisesRegex(ValueError, "invalid"):
                periodic_face_tilings._loaded_pattern_descriptors()


class PeriodicFacePatternDataTests(unittest.TestCase):
    def test_loader_rejects_non_object_descriptor(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "example.json"
            path.write_text(json.dumps([]), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "example.json.*invalid"):
                load_periodic_face_pattern_payloads(Path(temp_dir))

    def test_loader_requires_filename_to_match_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "wrong-name.json"
            path.write_text(json.dumps({"geometry": "example"}), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "must use the geometry key"):
                load_periodic_face_pattern_payloads(Path(temp_dir))


class TJunctionNeighborDetectionTests(unittest.TestCase):
    """Regression tests for the T-junction adjacency pass added to
    ``_attach_neighbors``. Non-edge-to-edge tilings like Stein-14 have one
    cell's vertex sitting on the midpoint of another cell's edge: the two
    cells share a half-edge but the edges have different endpoint pairs, so
    the original endpoint-matching detector missed the adjacency.

    The Pythagorean/Herringbone/Basketweave brick tilings sidestepped this
    by modelling the larger polygon with extra mid-edge vertices, turning
    the T-junction into a shared full edge between matched endpoints.
    Stein-14 is the first catalog tiling that genuinely needs the
    T-junction detection pass.
    """

    def _build_two_cell_t_junction_topology(
        self,
    ) -> list[periodic_face_tilings.PeriodicFaceCell]:
        """Two unit squares sharing a half-edge T-junction.

        Layout (y is up here, the snap precision doesn't care):
            cell A: (0, 0) - (1, 0) - (1, 1) - (0, 1)  [unit square]
            cell B: (1, -0.5) - (2, -0.5) - (2, 0.5) - (1, 0.5)
                                                       ^ this vertex sits
                                                         on cell A's right
                                                         edge midpoint

        The right edge of A goes from (1, 0) to (1, 1). The right edge
        of B has its top corner at (1, 0.5) (= midpoint of A's edge).
        So A and B share a half-edge but their edges have different
        endpoint pairs.
        """
        return [
            periodic_face_tilings.PeriodicFaceCell(
                id="a",
                kind="quad",
                slot="a",
                neighbors=(),
                center=(0.5, 0.5),
                vertices=((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),
            ),
            periodic_face_tilings.PeriodicFaceCell(
                id="b",
                kind="quad",
                slot="b",
                neighbors=(),
                center=(1.5, 0.0),
                vertices=((1.0, -0.5), (2.0, -0.5), (2.0, 0.5), (1.0, 0.5)),
            ),
        ]

    def test_t_junction_pair_becomes_neighbors(self) -> None:
        cells = self._build_two_cell_t_junction_topology()
        attached = periodic_face_tilings._attach_neighbors(cells)
        neighbor_map = {cell.id: set(cell.neighbors) for cell in attached}
        self.assertEqual(neighbor_map["a"], {"b"})
        self.assertEqual(neighbor_map["b"], {"a"})

    def test_full_edge_share_still_works(self) -> None:
        """The new pass must not break ordinary edge-to-edge adjacency."""
        cells = [
            periodic_face_tilings.PeriodicFaceCell(
                id="a",
                kind="quad",
                slot="a",
                neighbors=(),
                center=(0.5, 0.5),
                vertices=((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),
            ),
            periodic_face_tilings.PeriodicFaceCell(
                id="b",
                kind="quad",
                slot="b",
                neighbors=(),
                center=(1.5, 0.5),
                vertices=((1.0, 0.0), (2.0, 0.0), (2.0, 1.0), (1.0, 1.0)),
            ),
        ]
        attached = periodic_face_tilings._attach_neighbors(cells)
        neighbor_map = {cell.id: set(cell.neighbors) for cell in attached}
        self.assertEqual(neighbor_map["a"], {"b"})
        self.assertEqual(neighbor_map["b"], {"a"})

    def test_point_only_touch_is_not_a_neighbor(self) -> None:
        """Two squares meeting at a single corner (diagonal touch) are not
        neighbours - they share a point, not a segment."""
        cells = [
            periodic_face_tilings.PeriodicFaceCell(
                id="a",
                kind="quad",
                slot="a",
                neighbors=(),
                center=(0.5, 0.5),
                vertices=((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),
            ),
            periodic_face_tilings.PeriodicFaceCell(
                id="b",
                kind="quad",
                slot="b",
                neighbors=(),
                center=(1.5, 1.5),
                vertices=((1.0, 1.0), (2.0, 1.0), (2.0, 2.0), (1.0, 2.0)),
            ),
        ]
        attached = periodic_face_tilings._attach_neighbors(cells)
        neighbor_map = {cell.id: set(cell.neighbors) for cell in attached}
        self.assertEqual(neighbor_map["a"], set())
        self.assertEqual(neighbor_map["b"], set())

    def test_stein14_recognizes_t_junction_neighbors(self) -> None:
        """End-to-end: Stein-14 is the live example in the catalog. Verify
        a known T-junction pair shows up in the neighbor graph."""
        from backend.simulation.topology_implementation_registry import (
            get_topology_implementation,
        )

        impl = get_topology_implementation("stein-14-pentagonal")
        result = impl.builder_ref("stein-14-pentagonal", 2, 2, None)
        cells_by_id = {cell.id: cell for cell in result.cells}
        # In a 2x2 patch t2 and t5 at logical (0, 1) share a half-edge
        # (verified geometrically: shared length 50, which is half of edge
        # d = 100). This pair was missed pre-fix.
        t2 = cells_by_id["p:t2:0:1"]
        t5_id = "p:t5:0:1"
        self.assertIn(t5_id, t2.neighbors)
        t5 = cells_by_id[t5_id]
        self.assertIn(t2.id, t5.neighbors)


if __name__ == "__main__":
    unittest.main()
