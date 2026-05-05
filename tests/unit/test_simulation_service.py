import sys
import unittest
from pathlib import Path
from typing import ClassVar
from unittest.mock import patch

try:
    from backend.defaults import APP_DEFAULTS, DEFAULT_HEIGHT, DEFAULT_WIDTH
    from backend.rules import RuleRegistry
    from backend.simulation.models import SimulationSnapshot
    from backend.simulation.service import SimulationOperationError, SimulationService
    from tests.unit.board_test_support import regular_grid_from_board
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.defaults import APP_DEFAULTS, DEFAULT_HEIGHT, DEFAULT_WIDTH
    from backend.rules import RuleRegistry
    from backend.simulation.models import SimulationSnapshot
    from backend.simulation.service import SimulationOperationError, SimulationService
    from tests.unit.board_test_support import regular_grid_from_board


class SimulationServiceTests(unittest.TestCase):
    rule_registry: ClassVar[RuleRegistry]

    @classmethod
    def setUpClass(cls) -> None:
        cls.rule_registry = RuleRegistry()

    def setUp(self) -> None:
        self.service = SimulationService(rule_registry=self.rule_registry)

    @staticmethod
    def cell_id(x: int, y: int) -> str:
        return f"c:{x}:{y}"

    @staticmethod
    def grid(snapshot: SimulationSnapshot) -> list[list[int]] | None:
        return regular_grid_from_board(snapshot.board)

    def test_get_state_returns_snapshot(self) -> None:
        state = self.service.get_state()
        self.assertIsInstance(state, SimulationSnapshot)
        self.assertEqual(state.config.width, DEFAULT_WIDTH)
        self.assertEqual(state.config.height, DEFAULT_HEIGHT)
        self.assertEqual(
            state.config.tiling_family, APP_DEFAULTS["simulation"]["topology_spec"]["tiling_family"]
        )
        self.assertEqual(
            state.config.adjacency_mode,
            APP_DEFAULTS["simulation"]["topology_spec"]["adjacency_mode"],
        )
        self.assertEqual(
            state.config.patch_depth, APP_DEFAULTS["simulation"]["topology_spec"]["patch_depth"]
        )
        self.assertEqual(state.rule.name, APP_DEFAULTS["simulation"]["rule"])

    def test_update_config_resizes_grid_and_preserves_existing_cells(self) -> None:
        self.service.toggle_cell_by_id(self.cell_id(1, 1))
        self.service.update_config(
            topology_spec={"width": 40, "height": 25}, speed=12, rule_name="highlife"
        )
        state = self.service.get_state()
        grid = self.grid(state)
        assert grid is not None

        self.assertEqual(state.config.width, 40)
        self.assertEqual(state.config.height, 25)
        self.assertEqual(state.config.speed, 12.0)
        self.assertEqual(state.rule.name, "highlife")
        self.assertEqual(grid[1][1], 1)
        self.assertEqual(len(grid), 25)
        self.assertEqual(len(grid[0]), 40)

    def test_speed_only_update_config_keeps_running(self) -> None:
        self.service.start()

        self.service.update_config(speed=12)
        state = self.service.get_state()

        self.assertTrue(state.running)
        self.assertEqual(state.config.speed, 12.0)

    def test_resize_update_config_pauses_running_simulation(self) -> None:
        self.service.start()

        self.service.update_config(topology_spec={"width": 12, "height": 9})
        state = self.service.get_state()

        self.assertFalse(state.running)
        self.assertEqual(state.config.width, 12)
        self.assertEqual(state.config.height, 9)

    def test_switching_into_hexwhirlpool_preserves_rectangular_dimensions_and_overlap(self) -> None:
        self.service.reset(
            topology_spec={
                "tiling_family": "hex",
                "adjacency_mode": "edge",
                "width": 7,
                "height": 5,
            },
            speed=6,
            randomize=False,
        )
        self.service.set_cells_by_id(
            [
                (self.cell_id(1, 1), 1),
                (self.cell_id(4, 4), 1),
                (self.cell_id(6, 2), 1),
            ]
        )

        self.service.update_config(rule_name="hexwhirlpool")
        state = self.service.get_state()
        grid = self.grid(state)
        assert grid is not None

        self.assertEqual(state.rule.name, "whirlpool")
        self.assertEqual(state.config.width, 7)
        self.assertEqual(state.config.height, 5)
        self.assertEqual(grid[1][1], 1)
        self.assertEqual(grid[4][4], 1)
        self.assertEqual(grid[2][6], 1)
        self.assertEqual(sum(sum(row) for row in grid), 3)

    def test_reset_randomize_false_clears_grid_and_stops_running(self) -> None:
        self.service.toggle_cell_by_id(self.cell_id(0, 0))
        self.service.start()
        self.service.reset(
            topology_spec={"width": 8, "height": 6}, speed=7, rule_name="conway", randomize=False
        )
        state = self.service.get_state()
        grid = self.grid(state)
        assert grid is not None

        self.assertFalse(state.running)
        self.assertEqual(state.generation, 0)
        self.assertEqual(sum(sum(row) for row in grid), 0)
        self.assertEqual(state.config.width, 8)
        self.assertEqual(state.config.height, 6)
        self.assertEqual(state.config.speed, 7.0)

    def test_reset_preserves_rectangular_whirlpool_dimensions(self) -> None:
        self.service.reset(
            topology_spec={"width": 12, "height": 8},
            speed=7,
            rule_name="whirlpool",
            randomize=False,
        )
        state = self.service.get_state()
        grid = self.grid(state)
        assert grid is not None

        self.assertEqual(state.rule.name, "whirlpool")
        self.assertEqual(state.config.width, 12)
        self.assertEqual(state.config.height, 8)
        self.assertEqual(len(grid), 8)
        self.assertEqual(len(grid[0]), 12)

    def test_random_reset_succeeds_for_supported_binary_rules(self) -> None:
        deterministic_rows = [
            [0, 1, 0, 1, 0],
            [1, 0, 1, 0, 1],
            [0, 0, 1, 1, 0],
            [1, 1, 0, 0, 1],
            [0, 1, 1, 0, 0],
        ]
        deterministic_states = [cell for row in deterministic_rows for cell in row]

        for rule_name in ("conway", "highlife"):
            with self.subTest(rule_name=rule_name):
                with patch(
                    "backend.simulation.service.random.choices",
                    return_value=deterministic_states[:],
                ):
                    self.service.start()
                    self.service.toggle_cell_by_id(self.cell_id(0, 0))
                    self.service.reset(
                        topology_spec={"width": 5, "height": 5},
                        speed=8,
                        rule_name=rule_name,
                        randomize=True,
                    )

                state = self.service.get_state()
                grid = self.grid(state)
                assert grid is not None
                allowed_states = self.rule_registry.get(rule_name).state_values()

                self.assertFalse(state.running)
                self.assertEqual(state.generation, 0)
                self.assertEqual(state.config.width, 5)
                self.assertEqual(state.config.height, 5)
                self.assertEqual(state.config.speed, 8.0)
                self.assertEqual(state.rule.name, rule_name)
                self.assertEqual(len(grid), 5)
                self.assertEqual(len(grid[0]), 5)
                self.assertTrue(all(cell in allowed_states for row in grid for cell in row))
                self.assertEqual(grid, deterministic_rows)

    def test_set_cells_by_id_is_atomic_when_validation_fails(self) -> None:
        before = self.grid(self.service.get_state())
        with self.assertRaises(SimulationOperationError):
            self.service.set_cells_by_id([(self.cell_id(1, 1), 1), (self.cell_id(2, 2), 9)])
        after = self.grid(self.service.get_state())
        self.assertEqual(before, after)

    def test_set_cell_state_by_id_ignores_missing_ids(self) -> None:
        before = self.grid(self.service.get_state())

        self.service.set_cell_state_by_id("missing:-1:0", 1)
        self.service.set_cell_state_by_id("missing:0:-1", 1)
        self.service.set_cell_state_by_id(f"missing:{DEFAULT_WIDTH + 1}:0", 1)

        after = self.grid(self.service.get_state())
        self.assertEqual(after, before)

    def test_set_cells_by_id_ignores_missing_ids_but_applies_valid_updates(self) -> None:
        self.service.set_cells_by_id(
            [
                (self.cell_id(1, 1), 1),
                ("missing", 1),
                (self.cell_id(2, 2), 1),
            ]
        )
        state = self.service.get_state()
        grid = self.grid(state)
        assert grid is not None

        self.assertEqual(grid[1][1], 1)
        self.assertEqual(grid[2][2], 1)
        self.assertEqual(sum(sum(row) for row in grid), 2)

    def test_multistate_cells_are_preserved_and_rule_switch_coerces_invalid_values(self) -> None:
        self.service.update_config(rule_name="wireworld")
        self.service.set_cell_state_by_id(self.cell_id(2, 2), 3)
        self.service.set_cells_by_id([(self.cell_id(3, 3), 2), (self.cell_id(4, 4), 1)])
        wireworld_state = self.service.get_state()
        wireworld_grid = self.grid(wireworld_state)
        assert wireworld_grid is not None

        self.assertEqual(wireworld_grid[2][2], 3)
        self.assertEqual(wireworld_grid[3][3], 2)
        self.assertEqual(wireworld_grid[4][4], 1)

        self.service.update_config(rule_name="conway")
        conway_state = self.service.get_state()
        conway_grid = self.grid(conway_state)
        assert conway_grid is not None

        self.assertEqual(conway_grid[2][2], 0)
        self.assertEqual(conway_grid[3][3], 0)
        self.assertEqual(conway_grid[4][4], 1)

    def test_toggle_uses_default_paint_state_for_multistate_rules(self) -> None:
        self.service.update_config(rule_name="wireworld")
        self.service.toggle_cell_by_id(self.cell_id(1, 1))
        first_state = self.service.get_state()
        first_grid = self.grid(first_state)
        assert first_grid is not None
        self.assertEqual(first_grid[1][1], 3)

        self.service.toggle_cell_by_id(self.cell_id(1, 1))
        second_state = self.service.get_state()
        second_grid = self.grid(second_state)
        assert second_grid is not None
        self.assertEqual(second_grid[1][1], 0)

    def test_random_reset_requires_rule_randomization_support(self) -> None:
        with self.assertRaises(SimulationOperationError):
            self.service.reset(rule_name="wireworld", randomize=True)

    def test_reset_to_hex_geometry_selects_hex_default_rule(self) -> None:
        self.service.reset(
            topology_spec={
                "tiling_family": "hex",
                "adjacency_mode": "edge",
                "width": 9,
                "height": 7,
            },
            speed=6,
        )
        state = self.service.get_state()
        grid = self.grid(state)
        assert grid is not None

        self.assertEqual(state.config.geometry, "hex")
        self.assertEqual(state.config.width, 9)
        self.assertEqual(state.config.height, 7)
        self.assertEqual(state.config.speed, 6.0)
        self.assertEqual(state.rule.name, "hexlife")
        self.assertFalse(state.running)
        self.assertEqual(state.generation, 0)
        self.assertEqual(sum(sum(row) for row in grid), 0)

    def test_reset_to_triangle_geometry_selects_triangle_default_rule(self) -> None:
        self.service.reset(
            topology_spec={
                "tiling_family": "triangle",
                "adjacency_mode": "edge",
                "width": 11,
                "height": 9,
            },
            speed=6,
        )
        state = self.service.get_state()
        grid = self.grid(state)
        assert grid is not None

        self.assertEqual(state.config.geometry, "triangle")
        self.assertEqual(state.config.width, 11)
        self.assertEqual(state.config.height, 9)
        self.assertEqual(state.config.speed, 6.0)
        self.assertEqual(state.rule.name, "trilife")
        self.assertFalse(state.running)
        self.assertEqual(state.generation, 0)
        self.assertEqual(sum(sum(row) for row in grid), 0)

    def test_reset_to_kagome_geometry_selects_kagome_default_rule(self) -> None:
        self.service.reset(
            topology_spec={
                "tiling_family": "trihexagonal-3-6-3-6",
                "adjacency_mode": "edge",
                "width": 7,
                "height": 6,
            },
            speed=6,
        )
        state = self.service.get_state()

        self.assertEqual(state.config.geometry, "trihexagonal-3-6-3-6")
        self.assertEqual(state.config.width, 7)
        self.assertEqual(state.config.height, 6)
        self.assertEqual(state.config.speed, 6.0)
        self.assertEqual(state.rule.name, "kagome-life")
        self.assertFalse(state.running)
        self.assertEqual(state.generation, 0)
        self.assertIsNone(self.grid(state))
        self.assertEqual(len(state.board.cell_states), 7 * 6 * 3)
        self.assertTrue(all(cell == 0 for cell in state.board.cell_states))

    def test_update_config_allows_rule_switches_across_topologies(self) -> None:
        self.service.reset(topology_spec={"tiling_family": "hex", "adjacency_mode": "edge"})

        self.service.update_config(rule_name="conway")

        self.assertEqual(self.service.get_state().rule.name, "conway")

    def test_update_config_allows_triangle_rule_switches_across_topologies(self) -> None:
        self.service.reset(topology_spec={"tiling_family": "triangle", "adjacency_mode": "edge"})

        self.service.update_config(rule_name="conway")

        self.assertEqual(self.service.get_state().rule.name, "conway")


if __name__ == "__main__":
    unittest.main()
