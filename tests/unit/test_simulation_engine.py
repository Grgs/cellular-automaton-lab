import sys
import unittest
from pathlib import Path

try:
    from backend.rules.base import AutomatonRule
    from backend.rules.archlife488 import ArchLife488Rule
    from backend.rules.conway import ConwayLifeRule
    from backend.rules.hexlife import HexLifeRule
    from backend.rules.trilife import TriLifeRule
    from backend.simulation.engine import SimulationEngine
    from backend.simulation.rule_context import build_rule_contexts_for_board
    from backend.simulation.topology import ARCHIMEDEAN_488_GEOMETRY, SimulationBoard, empty_board
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.rules.base import AutomatonRule
    from backend.rules.archlife488 import ArchLife488Rule
    from backend.rules.conway import ConwayLifeRule
    from backend.rules.hexlife import HexLifeRule
    from backend.rules.trilife import TriLifeRule
    from backend.simulation.engine import SimulationEngine
    from backend.simulation.rule_context import build_rule_contexts_for_board
    from backend.simulation.topology import ARCHIMEDEAN_488_GEOMETRY, SimulationBoard, empty_board

from tests.unit.board_test_support import board_from_grid, regular_grid_from_board
from tests.unit.simulation_test_fixtures import BLINKER_GRID, LiveNeighborTrackingRule, NeighborTrackingRule


def reference_step_board(board: SimulationBoard, rule: AutomatonRule) -> SimulationBoard:
    next_states = [rule.next_state(ctx) for ctx in build_rule_contexts_for_board(board)]
    return SimulationBoard(topology=board.topology, cell_states=next_states)


class SimulationEngineTests(unittest.TestCase):
    def test_engine_steps_blinker_pattern(self) -> None:
        engine = SimulationEngine()
        rule = ConwayLifeRule()

        next_board = engine.step_board(board_from_grid(BLINKER_GRID), rule)
        self.assertEqual(
            regular_grid_from_board(next_board),
            [
                [0, 0, 0],
                [1, 1, 1],
                [0, 0, 0],
            ],
        )

    def test_engine_preserves_neighbor_state_payload_for_neighbor_tracking_rules(self) -> None:
        engine = SimulationEngine()
        rule = NeighborTrackingRule()
        board = board_from_grid(
            [
                [1, 0],
                [0, 1],
            ]
        )
        engine.step_board(board, rule)

        self.assertEqual(len(rule.calls), 4)
        self.assertTrue(all(len(states) >= 3 for states in rule.calls))
        self.assertIn(1, rule.calls[0])

    def test_engine_counts_non_zero_neighbors_instead_of_summing_state_values(self) -> None:
        engine = SimulationEngine()
        rule = LiveNeighborTrackingRule()
        board = board_from_grid(
            [
                [3, 0, 2],
                [0, 0, 0],
                [1, 0, 0],
            ]
        )
        engine.step_board(board, rule)

        self.assertIn(3, rule.calls)

    def test_engine_step_board_matches_reference_logic_for_binary_rules_across_geometries(self) -> None:
        cases = [
            ("square", ConwayLifeRule(), [
                [0, 1, 0, 0],
                [1, 1, 0, 1],
                [0, 0, 1, 0],
                [1, 0, 0, 1],
            ]),
            ("hex", HexLifeRule(), [
                [0, 1, 0, 1],
                [1, 0, 1, 0],
                [0, 1, 1, 0],
                [1, 0, 0, 1],
            ]),
            ("triangle", TriLifeRule(), [
                [0, 1, 0, 1, 0],
                [1, 0, 1, 0, 1],
                [0, 1, 1, 1, 0],
                [1, 0, 1, 0, 1],
            ]),
        ]

        engine = SimulationEngine()
        for geometry, rule, grid in cases:
            with self.subTest(geometry=geometry):
                board = board_from_grid(grid, geometry)
                optimized = engine.step_board(board, rule)
                expected = reference_step_board(board, rule.__class__())
                self.assertEqual(optimized.cell_states, expected.cell_states)

    def test_engine_step_board_matches_reference_logic_for_neighbor_state_rules_across_geometries(self) -> None:
        grid = [
            [0, 1, 2, 0, 3],
            [4, 0, 0, 5, 0],
            [0, 6, 0, 0, 7],
            [8, 0, 9, 0, 0],
        ]

        engine = SimulationEngine()
        for geometry in ("square", "hex", "triangle"):
            with self.subTest(geometry=geometry):
                board = board_from_grid(grid, geometry)
                optimized_rule = NeighborTrackingRule()
                optimized = engine.step_board(board, optimized_rule)

                reference_rule = NeighborTrackingRule()
                expected = reference_step_board(board, reference_rule)

                self.assertEqual(optimized.cell_states, expected.cell_states)
                self.assertEqual(optimized_rule.calls, reference_rule.calls)

    def test_engine_step_board_matches_reference_logic_for_archimedean_rule(self) -> None:
        board = empty_board(ARCHIMEDEAN_488_GEOMETRY, 5, 4)
        seeded_cells = (
            "o:1:1",
            "o:2:1",
            "o:2:2",
            "s:2:2",
            "s:3:2",
        )
        for cell_id in seeded_cells:
            board.set_state_for(cell_id, 1)

        engine = SimulationEngine()
        optimized = engine.step_board(board, ArchLife488Rule())
        expected = reference_step_board(board, ArchLife488Rule())

        self.assertEqual(optimized.cell_states, expected.cell_states)


if __name__ == "__main__":
    unittest.main()
