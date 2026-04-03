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


if __name__ == "__main__":
    unittest.main()
