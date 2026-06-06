import sys
import unittest
from pathlib import Path

try:
    from backend.simulation.rule_context import RuleContext, build_rule_contexts_for_board
    from backend.simulation.topology import board_from_cells_by_id
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.simulation.rule_context import RuleContext, build_rule_contexts_for_board
    from backend.simulation.topology import board_from_cells_by_id


class CountNeighborsTests(unittest.TestCase):
    """Pin the fast count_* paths against independent references.

    ``neighbor_states()`` and the topology frame are not part of the optimised
    counting path, so checking against them catches regressions the engine
    reference test cannot (that test runs the same counting code on both sides).
    """

    def _seeded_contexts(self, geometry: str) -> tuple[RuleContext, ...]:
        board = board_from_cells_by_id(
            geometry,
            8,
            8,
            {"c:3:3": 1, "c:4:3": 2, "c:3:4": 1, "c:4:4": 3, "c:2:3": 1},
        )
        return build_rule_contexts_for_board(board)

    def test_counts_match_neighbor_states(self) -> None:
        for geometry in ("square", "hex", "triangle"):
            for ctx in self._seeded_contexts(geometry):
                states = ctx.neighbor_states()
                with self.subTest(geometry=geometry, cell=ctx.cell_id):
                    self.assertEqual(ctx.count_neighbors(), len(states))
                    self.assertEqual(
                        ctx.count_live_neighbors(), sum(1 for state in states if state != 0)
                    )
                    self.assertEqual(ctx.count_neighbors(1), states.count(1))
                    self.assertEqual(
                        ctx.count_neighbors(1, 2),
                        sum(1 for state in states if state in (1, 2)),
                    )

    def test_radial_and_turn_filters_match_frame(self) -> None:
        for ctx in self._seeded_contexts("square"):
            frame = ctx.frame
            neighbors = frame.cells[frame.index_for(ctx.cell_id)].neighbors
            for radial in ("inward", "outward", "level"):
                with self.subTest(cell=ctx.cell_id, radial=radial):
                    expected = sum(1 for neighbor in neighbors if neighbor.radial == radial)
                    self.assertEqual(ctx.count_neighbors(radial=radial), expected)
            for turn in ("clockwise", "counterclockwise"):
                with self.subTest(cell=ctx.cell_id, turn=turn):
                    expected_live = sum(
                        1
                        for neighbor in neighbors
                        if neighbor.turn == turn
                        and ctx.state_for(frame.cells[neighbor.index].id) != 0
                    )
                    self.assertEqual(ctx.count_live_neighbors(turn=turn), expected_live)


if __name__ == "__main__":
    unittest.main()
