import sys
import subprocess
import unittest
from pathlib import Path

try:
    from backend.simulation.aperiodic_contracts import APERIODIC_IMPLEMENTATION_CONTRACTS
    from backend.simulation.aperiodic_prototiles import build_aperiodic_patch
    from backend.simulation.aperiodic_shield import build_shield_patch_for_window_threshold
    from backend.simulation.topology import build_topology
    from backend.simulation.topology_catalog import TOPOLOGY_VARIANTS
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.simulation.aperiodic_contracts import APERIODIC_IMPLEMENTATION_CONTRACTS
    from backend.simulation.aperiodic_prototiles import build_aperiodic_patch
    from backend.simulation.aperiodic_shield import build_shield_patch_for_window_threshold
    from backend.simulation.topology import build_topology
    from backend.simulation.topology_catalog import TOPOLOGY_VARIANTS


class AperiodicRegistryTests(unittest.TestCase):
    def test_every_aperiodic_family_has_an_implementation_contract(self) -> None:
        aperiodic_geometries = {
            variant.geometry_key
            for variant in TOPOLOGY_VARIANTS
            if variant.family == "aperiodic"
        }

        self.assertEqual(set(APERIODIC_IMPLEMENTATION_CONTRACTS), aperiodic_geometries)
        for geometry, contract in APERIODIC_IMPLEMENTATION_CONTRACTS.items():
            with self.subTest(geometry=geometry):
                self.assertEqual(contract.geometry, geometry)
                self.assertTrue(contract.source_urls)
                self.assertTrue(contract.public_cell_kinds)
                self.assertTrue(contract.depth_semantics)
                self.assertTrue(contract.verification_modes)

    def test_experimental_aperiodics_keep_explicit_promotion_blockers(self) -> None:
        for geometry in ("dodecagonal-square-triangle", "shield", "pinwheel"):
            with self.subTest(geometry=geometry):
                self.assertIsNotNone(
                    APERIODIC_IMPLEMENTATION_CONTRACTS[geometry].promotion_blocker
                )

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
            ("dodecagonal-square-triangle", 3),
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

    def test_shield_explicit_threshold_builder_preserves_shipped_threshold_output(self) -> None:
        shipped_patch = build_aperiodic_patch("shield", 3)
        explicit_patch = build_shield_patch_for_window_threshold(3, window_threshold=214.8816)

        self.assertEqual(shipped_patch.patch_depth, explicit_patch.patch_depth)
        self.assertEqual(shipped_patch.width, explicit_patch.width)
        self.assertEqual(shipped_patch.height, explicit_patch.height)
        self.assertEqual([cell.id for cell in shipped_patch.cells], [cell.id for cell in explicit_patch.cells])

    def test_new_tiling_metadata_survives_patch_build(self) -> None:
        chair_patch = build_aperiodic_patch("chair", 3)
        hat_patch = build_aperiodic_patch("hat-monotile", 2)
        tuebingen_patch = build_aperiodic_patch("tuebingen-triangle", 2)
        shield_patch = build_aperiodic_patch("shield", 2)
        pinwheel_patch = build_aperiodic_patch("pinwheel", 2)

        self.assertTrue(all(cell.orientation_token is not None for cell in chair_patch.cells))

        self.assertTrue(all(cell.tile_family == "hat" for cell in hat_patch.cells))
        self.assertTrue(all(cell.orientation_token is not None for cell in hat_patch.cells))
        self.assertTrue(all(cell.chirality_token is not None for cell in hat_patch.cells))

        self.assertTrue(all(cell.tile_family == "tuebingen" for cell in tuebingen_patch.cells))
        self.assertTrue(all(cell.orientation_token is not None for cell in tuebingen_patch.cells))
        self.assertTrue(all(cell.chirality_token is not None for cell in tuebingen_patch.cells))

        self.assertTrue(all(cell.tile_family == "shield" for cell in shield_patch.cells))
        self.assertTrue(all(cell.orientation_token is not None for cell in shield_patch.cells))
        self.assertTrue(any(cell.kind == "shield-square" for cell in shield_patch.cells))

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

    def test_tuebingen_patch_uses_segment_overlap_neighbors_to_stay_connected(self) -> None:
        patch = build_aperiodic_patch("tuebingen-triangle", 3)
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

    def test_tuebingen_patch_is_not_geometry_identical_to_robinson(self) -> None:
        robinson_patch = build_aperiodic_patch("robinson-triangles", 3)
        tuebingen_patch = build_aperiodic_patch("tuebingen-triangle", 3)

        self.assertNotEqual(
            sorted(tuple(cell.vertices) for cell in robinson_patch.cells),
            sorted(tuple(cell.vertices) for cell in tuebingen_patch.cells),
        )

    def test_tuebingen_patch_support_expands_with_depth(self) -> None:
        shallow_patch = build_aperiodic_patch("tuebingen-triangle", 1)
        deep_patch = build_aperiodic_patch("tuebingen-triangle", 3)

        self.assertGreater(deep_patch.width, shallow_patch.width)
        self.assertGreater(deep_patch.height, shallow_patch.height)

    def test_aperiodic_registry_remains_importable_without_shapely(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        script = """
import builtins
import sys

original_import = builtins.__import__

def fake_import(name, *args, **kwargs):
    if name.startswith("shapely"):
        raise ModuleNotFoundError("No module named shapely")
    return original_import(name, *args, **kwargs)

builtins.__import__ = fake_import
from backend.simulation.aperiodic_prototiles import build_aperiodic_patch

chair_patch = build_aperiodic_patch("chair", 1)
spectre_patch = build_aperiodic_patch("spectre", 1)
assert chair_patch.cells
assert spectre_patch.cells
print(len(chair_patch.cells), len(spectre_patch.cells))
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"Subprocess failed without shapely.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
