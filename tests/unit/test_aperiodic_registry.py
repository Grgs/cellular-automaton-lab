import sys
import unittest
from pathlib import Path

try:
    from backend.simulation.aperiodic_prototiles import build_aperiodic_patch
    from backend.simulation.topology import build_topology
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.simulation.aperiodic_prototiles import build_aperiodic_patch
    from backend.simulation.topology import build_topology


class AperiodicRegistryTests(unittest.TestCase):
    def test_taylor_socolar_patch_builder_matches_topology_builder_output(self) -> None:
        patch = build_aperiodic_patch("taylor-socolar", 2)
        topology = build_topology("taylor-socolar", 0, 0, patch_depth=2)

        self.assertEqual(patch.patch_depth, topology.patch_depth)
        self.assertEqual(patch.width, topology.width)
        self.assertEqual(patch.height, topology.height)
        self.assertEqual([cell.id for cell in patch.cells], [cell.id for cell in topology.cells])

    def test_chair_patch_builder_matches_topology_builder_output(self) -> None:
        patch = build_aperiodic_patch("chair", 3)
        topology = build_topology("chair", 0, 0, patch_depth=3)

        self.assertEqual(patch.patch_depth, topology.patch_depth)
        self.assertEqual(patch.width, topology.width)
        self.assertEqual(patch.height, topology.height)
        self.assertEqual([cell.id for cell in patch.cells], [cell.id for cell in topology.cells])

    def test_robinson_triangles_patch_builder_matches_topology_builder_output(self) -> None:
        patch = build_aperiodic_patch("robinson-triangles", 3)
        topology = build_topology("robinson-triangles", 0, 0, patch_depth=3)

        self.assertEqual(patch.patch_depth, topology.patch_depth)
        self.assertEqual(patch.width, topology.width)
        self.assertEqual(patch.height, topology.height)
        self.assertEqual([cell.id for cell in patch.cells], [cell.id for cell in topology.cells])

    def test_new_tiling_patch_builders_match_topology_builder_output(self) -> None:
        for geometry, depth in (
            ("hat-monotile", 3),
            ("tuebingen-triangle", 3),
            ("square-triangle", 3),
            ("shield", 3),
            ("pinwheel", 3),
        ):
            with self.subTest(geometry=geometry):
                patch = build_aperiodic_patch(geometry, depth)
                topology = build_topology(geometry, 0, 0, patch_depth=depth)

                self.assertEqual(patch.patch_depth, topology.patch_depth)
                self.assertEqual(patch.width, topology.width)
                self.assertEqual(patch.height, topology.height)
                self.assertEqual([cell.id for cell in patch.cells], [cell.id for cell in topology.cells])

    def test_new_tiling_metadata_survives_patch_build(self) -> None:
        hat_patch = build_aperiodic_patch("hat-monotile", 2)
        shield_patch = build_aperiodic_patch("shield", 2)
        pinwheel_patch = build_aperiodic_patch("pinwheel", 2)

        self.assertTrue(all(cell.tile_family == "hat" for cell in hat_patch.cells))
        self.assertTrue(all(cell.orientation_token is not None for cell in hat_patch.cells))
        self.assertTrue(all(cell.chirality_token is not None for cell in hat_patch.cells))

        self.assertTrue(any(cell.kind == "shield-square" for cell in shield_patch.cells))
        self.assertTrue(any(cell.decoration_tokens for cell in shield_patch.cells if cell.kind == "shield-shield"))

        self.assertTrue(all(cell.tile_family == "pinwheel" for cell in pinwheel_patch.cells))
        self.assertTrue(all(cell.orientation_token is not None for cell in pinwheel_patch.cells))

    def test_pinwheel_patch_uses_segment_overlap_neighbors_to_stay_connected(self) -> None:
        patch = build_aperiodic_patch("pinwheel", 3)
        by_id = {cell.id: cell for cell in patch.cells}

        seen: set[str] = set()
        stack = [patch.cells[0].id]
        seen.add(patch.cells[0].id)
        while stack:
            current = stack.pop()
            for neighbor_id in by_id[current].neighbors:
                if neighbor_id in seen:
                    continue
                seen.add(neighbor_id)
                stack.append(neighbor_id)

        self.assertEqual(len(seen), len(patch.cells))


if __name__ == "__main__":
    unittest.main()
