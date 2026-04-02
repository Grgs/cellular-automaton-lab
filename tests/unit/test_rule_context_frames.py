import sys
import unittest
from pathlib import Path

try:
    from backend.simulation.rule_context import build_rule_contexts_for_board, topology_frame_for
    from backend.simulation.topology import LatticeTopology, build_topology, empty_board
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.simulation.rule_context import build_rule_contexts_for_board, topology_frame_for
    from backend.simulation.topology import LatticeTopology, build_topology, empty_board


class RuleContextFrameTests(unittest.TestCase):
    def test_topology_frame_cache_reuses_revision_key(self) -> None:
        topology = build_topology("square", 3, 3)
        duplicated_topology = LatticeTopology(
            geometry=topology.geometry,
            width=topology.width,
            height=topology.height,
            cells=topology.cells,
            topology_revision=topology.topology_revision,
            patch_depth=topology.patch_depth,
        )

        first = topology_frame_for(topology)
        second = topology_frame_for(duplicated_topology)

        self.assertIs(first, second)

    def test_topology_frame_computes_shell_rank_and_radial_metadata(self) -> None:
        topology = build_topology("square", 3, 3)

        frame = topology_frame_for(topology)
        center_cell = frame.cell_for("c:1:1")
        corner_cell = frame.cell_for("c:0:0")

        self.assertEqual(center_cell.shell_rank, 0)
        self.assertEqual(frame.max_shell_rank, 1)
        self.assertTrue(all(neighbor.radial == "outward" for neighbor in center_cell.neighbors))
        self.assertTrue(any(neighbor.radial == "inward" for neighbor in corner_cell.neighbors))
        self.assertTrue(any(neighbor.turn == "clockwise" for neighbor in corner_cell.neighbors))

    def test_build_rule_contexts_for_board_shares_a_single_frame(self) -> None:
        board = empty_board("square", 3, 3)

        contexts = build_rule_contexts_for_board(board)

        self.assertEqual(len(contexts), board.topology.cell_count)
        self.assertTrue(all(context.frame is contexts[0].frame for context in contexts))


if __name__ == "__main__":
    unittest.main()
