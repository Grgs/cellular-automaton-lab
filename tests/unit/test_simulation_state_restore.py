import sys
import unittest
from pathlib import Path
from typing import ClassVar

try:
    from backend.defaults import APP_DEFAULTS
    from backend.rules import RuleRegistry
    from backend.simulation.models import SimulationConfig, SimulationStateData
    from backend.simulation.state_restore import SimulationStateRestorer
    from tests.unit.board_test_support import board_from_grid, regular_grid_from_board
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.defaults import APP_DEFAULTS
    from backend.rules import RuleRegistry
    from backend.simulation.models import SimulationConfig, SimulationStateData
    from backend.simulation.state_restore import SimulationStateRestorer
    from tests.unit.board_test_support import board_from_grid, regular_grid_from_board


class SimulationStateRestoreTests(unittest.TestCase):
    rule_registry: ClassVar[RuleRegistry]

    @classmethod
    def setUpClass(cls) -> None:
        cls.rule_registry = RuleRegistry()

    def setUp(self) -> None:
        self.restorer = SimulationStateRestorer(self.rule_registry)
        self.fallback_state = SimulationStateData(
            config=SimulationConfig(),
            running=True,
            generation=12,
            rule=self.rule_registry.default_for_geometry("square"),
            board=board_from_grid(
                [[0] * SimulationConfig().width for _ in range(SimulationConfig().height)]
            ),
        )

    def test_restore_normalizes_invalid_geometry_numeric_values_and_missing_rule(self) -> None:
        restored = self.restorer.restore(
            {
                "topology_spec": {
                    "tiling_family": "zigzag",
                    "adjacency_mode": "edge",
                    "width": "bad",
                    "height": 2,
                },
                "speed": "fast",
                "running": True,
                "generation": -4,
                "rule": "missing-rule",
                "cells_by_id": {
                    "c:1:0": 1,
                    "c:3:0": 2,
                },
            },
            fallback_state=self.fallback_state,
        )

        grid = regular_grid_from_board(restored.board)
        assert grid is not None
        self.assertEqual(
            restored.config.tiling_family,
            APP_DEFAULTS["simulation"]["topology_spec"]["tiling_family"],
        )
        self.assertEqual(
            restored.config.adjacency_mode,
            APP_DEFAULTS["simulation"]["topology_spec"]["adjacency_mode"],
        )
        self.assertEqual(
            restored.config.patch_depth, APP_DEFAULTS["simulation"]["topology_spec"]["patch_depth"]
        )
        self.assertEqual(
            restored.config.width, APP_DEFAULTS["simulation"]["topology_spec"]["width"]
        )
        self.assertEqual(
            restored.config.height, APP_DEFAULTS["simulation"]["topology_spec"]["height"]
        )
        self.assertEqual(restored.config.speed, self.fallback_state.config.speed)
        self.assertFalse(restored.running)
        self.assertEqual(restored.generation, 0)
        self.assertEqual(restored.rule.name, APP_DEFAULTS["simulation"]["rule"])
        self.assertEqual(grid[0][1], 1)
        self.assertEqual(grid[0][3], 0)
        self.assertEqual(len(grid), APP_DEFAULTS["simulation"]["topology_spec"]["height"])

    def test_restore_preserves_requested_rule_across_topologies(self) -> None:
        restored = self.restorer.restore(
            {
                "topology_spec": {
                    "tiling_family": "triangle",
                    "adjacency_mode": "edge",
                    "width": 5,
                    "height": 4,
                },
                "speed": 8,
                "running": True,
                "generation": 6,
                "rule": "conway",
                "cells_by_id": {
                    "c:0:0": 1,
                    "c:2:0": 1,
                    "c:4:0": 1,
                    "c:1:1": 1,
                    "c:3:1": 1,
                    "c:0:2": 1,
                    "c:2:2": 1,
                    "c:4:2": 1,
                    "c:1:3": 1,
                    "c:3:3": 1,
                },
            },
            fallback_state=self.fallback_state,
        )

        grid = regular_grid_from_board(restored.board)
        assert grid is not None
        self.assertEqual(restored.config.geometry, "triangle")
        self.assertEqual(restored.rule.name, "conway")
        self.assertFalse(restored.running)
        self.assertEqual(restored.generation, 6)
        self.assertEqual(grid[0], [1, 0, 1, 0, 1])
        self.assertEqual(grid[1], [0, 1, 0, 1, 0])

    def test_restore_preserves_requested_multistate_rule_and_coerces_grid(self) -> None:
        restored = self.restorer.restore(
            {
                "topology_spec": {
                    "tiling_family": "hex",
                    "adjacency_mode": "edge",
                    "width": 4,
                    "height": 2,
                },
                "speed": 99,
                "running": True,
                "generation": 4,
                "rule": "wireworld",
                "cells_by_id": {
                    "c:1:0": 1,
                    "c:0:1": 1,
                    "c:2:1": 1,
                    "c:3:1": 1,
                },
            },
            fallback_state=self.fallback_state,
        )

        grid = regular_grid_from_board(restored.board)
        assert grid is not None
        self.assertEqual(restored.config.geometry, "hex")
        self.assertEqual(restored.config.width, 4)
        self.assertEqual(restored.config.height, 3)
        self.assertEqual(restored.config.speed, 30.0)
        self.assertFalse(restored.running)
        self.assertEqual(restored.generation, 4)
        self.assertEqual(restored.rule.name, "wireworld")
        self.assertEqual(grid[0], [0, 1, 0, 0])
        self.assertEqual(grid[1], [1, 0, 1, 1])
        self.assertEqual(grid[2], [0, 0, 0, 0])

    def test_restore_regenerates_archimedean_topology_from_cell_states(self) -> None:
        restored = self.restorer.restore(
            {
                "topology_spec": {
                    "tiling_family": "archimedean-4-8-8",
                    "adjacency_mode": "edge",
                    "width": 5,
                    "height": 5,
                },
                "speed": 7,
                "running": True,
                "generation": 3,
                "rule": "archlife488",
                "cells_by_id": {"o:2:2": 1, "s:2:2": 1},
            },
            fallback_state=self.fallback_state,
        )

        self.assertEqual(restored.config.geometry, "archimedean-4-8-8")
        self.assertEqual(restored.rule.name, "archlife488")
        self.assertFalse(restored.running)
        self.assertEqual(restored.generation, 3)
        self.assertEqual(
            restored.topology.topology_revision, restored.board.topology.topology_revision
        )
        self.assertEqual(restored.topology.cell_count, 61)
        self.assertIsNone(regular_grid_from_board(restored.board))
        self.assertEqual(restored.board.state_for("o:2:2"), 1)
        self.assertEqual(restored.board.state_for("s:2:2"), 1)

    def test_restore_regenerates_kagome_topology_from_cell_states(self) -> None:
        restored = self.restorer.restore(
            {
                "topology_spec": {
                    "tiling_family": "trihexagonal-3-6-3-6",
                    "adjacency_mode": "edge",
                    "width": 4,
                    "height": 4,
                },
                "speed": 7,
                "running": True,
                "generation": 3,
                "rule": "kagome-life",
                "cells_by_id": {"h:1:1": 1, "tu:1:0": 1},
            },
            fallback_state=self.fallback_state,
        )

        self.assertEqual(restored.config.geometry, "trihexagonal-3-6-3-6")
        self.assertEqual(restored.rule.name, "kagome-life")
        self.assertFalse(restored.running)
        self.assertEqual(restored.generation, 3)
        self.assertEqual(restored.topology.cell_count, 4 * 4 * 3)
        self.assertIsNone(regular_grid_from_board(restored.board))
        self.assertEqual(restored.board.state_for("h:1:1"), 1)
        self.assertEqual(restored.board.state_for("tu:1:0"), 1)

    def test_restore_preserves_rectangular_hexwhirlpool_state(self) -> None:
        restored = self.restorer.restore(
            {
                "topology_spec": {
                    "tiling_family": "hex",
                    "adjacency_mode": "edge",
                    "width": 7,
                    "height": 5,
                },
                "speed": 9,
                "running": True,
                "generation": 4,
                "rule": "hexwhirlpool",
                "cells_by_id": {
                    "c:1:1": 1,
                    "c:2:1": 2,
                    "c:3:1": 3,
                },
            },
            fallback_state=self.fallback_state,
        )

        grid = regular_grid_from_board(restored.board)
        assert grid is not None
        self.assertEqual(restored.rule.name, "whirlpool")
        self.assertEqual(restored.config.width, 7)
        self.assertEqual(restored.config.height, 5)
        self.assertEqual(grid[1][1:4], [1, 2, 3])

    def test_restore_ignores_unknown_cell_ids_and_invalid_cell_state_values(self) -> None:
        restored = self.restorer.restore(
            {
                "topology_spec": {
                    "tiling_family": "square",
                    "adjacency_mode": "edge",
                    "width": 4,
                    "height": 4,
                },
                "rule": "conway",
                "cells_by_id": {
                    "c:1:1": "1",
                    "c:9:9": 1,
                    "": 1,
                    123: 1,
                    "c:2:2": "bad",
                    "c:0:0": 0,
                },
            },
            fallback_state=self.fallback_state,
        )

        grid = regular_grid_from_board(restored.board)
        assert grid is not None
        self.assertEqual(grid[1][1], 1)
        self.assertEqual(grid[2][2], 0)
        self.assertEqual(grid[0][0], 0)
        self.assertEqual(sum(sum(row) for row in grid), 1)

    def test_restore_treats_non_dict_cells_payload_as_empty_board(self) -> None:
        restored = self.restorer.restore(
            {
                "topology_spec": {
                    "tiling_family": "square",
                    "adjacency_mode": "edge",
                    "width": 4,
                    "height": 4,
                },
                "rule": "conway",
                "cells_by_id": ["c:1:1"],
            },
            fallback_state=self.fallback_state,
        )

        grid = regular_grid_from_board(restored.board)
        assert grid is not None
        self.assertTrue(all(cell == 0 for row in grid for cell in row))


if __name__ == "__main__":
    unittest.main()
