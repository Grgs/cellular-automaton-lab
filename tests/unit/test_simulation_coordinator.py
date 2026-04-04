import sys
import unittest
from pathlib import Path
from typing import ClassVar
from unittest.mock import Mock, patch

try:
    from backend.defaults import APP_DEFAULTS, DEFAULT_HEIGHT, DEFAULT_WIDTH
    from backend.rules import RuleRegistry
    from backend.simulation.coordinator import SimulationCoordinator
    from backend.simulation.models import SimulationSnapshot
    from tests.unit.board_test_support import regular_grid_from_board
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.defaults import APP_DEFAULTS, DEFAULT_HEIGHT, DEFAULT_WIDTH
    from backend.rules import RuleRegistry
    from backend.simulation.coordinator import SimulationCoordinator
    from backend.simulation.models import SimulationSnapshot
    from tests.unit.board_test_support import regular_grid_from_board


class SimulationCoordinatorTests(unittest.TestCase):
    rule_registry: ClassVar[RuleRegistry]

    @classmethod
    def setUpClass(cls) -> None:
        cls.rule_registry = RuleRegistry()

    def setUp(self) -> None:
        self.manager = SimulationCoordinator(rule_registry=self.rule_registry)

    def tearDown(self) -> None:
        self.manager.stop_background_loop()

    def test_get_state_returns_snapshot(self) -> None:
        state = self.manager.get_state()
        self.assertIsInstance(state, SimulationSnapshot)
        self.assertEqual(state.config.width, DEFAULT_WIDTH)
        self.assertEqual(state.config.height, DEFAULT_HEIGHT)
        self.assertEqual(state.rule.name, APP_DEFAULTS["simulation"]["rule"])

    def test_public_mutation_methods_update_observable_state(self) -> None:
        self.manager.toggle_cell_by_id("c:1:1")
        self.manager.set_cell_state_by_id("c:2:2", 1)
        self.manager.set_cells_by_id([("c:3:3", 1)])
        self.manager.update_config(topology_spec={"width": 12, "height": 9}, speed=7, rule_name="highlife")
        state = self.manager.get_state()
        grid = regular_grid_from_board(state.board)
        assert grid is not None

        self.assertEqual(state.config.width, 12)
        self.assertEqual(state.config.height, 9)
        self.assertEqual(state.config.speed, 7.0)
        self.assertEqual(state.rule.name, "highlife")
        self.assertEqual(grid[1][1], 1)
        self.assertEqual(grid[2][2], 1)
        self.assertEqual(grid[3][3], 1)

    def test_public_control_methods_change_running_and_generation(self) -> None:
        self.manager.step()
        stepped = self.manager.get_state()
        self.assertEqual(stepped.generation, 1)
        self.assertFalse(stepped.running)

        self.manager.start()
        self.assertTrue(self.manager.get_state().running)

        self.manager.pause()
        self.assertFalse(self.manager.get_state().running)

        self.manager.resume()
        self.assertTrue(self.manager.get_state().running)

        self.manager.reset(randomize=False)
        reset = self.manager.get_state()
        self.assertFalse(reset.running)
        self.assertEqual(reset.generation, 0)

    def test_step_while_running_pauses_before_advancing(self) -> None:
        self.manager.start()
        self.assertTrue(self.manager.get_state().running)

        self.manager.step()
        stepped = self.manager.get_state()

        self.assertEqual(stepped.generation, 1)
        self.assertFalse(stepped.running)

    def test_update_config_only_pauses_when_board_is_reshaped(self) -> None:
        self.manager.start()
        self.assertTrue(self.manager.get_state().running)

        self.manager.update_config(speed=9)
        speed_only = self.manager.get_state()
        self.assertTrue(speed_only.running)
        self.assertEqual(speed_only.config.speed, 9.0)

        self.manager.update_config(topology_spec={"width": 12, "height": 9})
        resized = self.manager.get_state()
        self.assertFalse(resized.running)
        self.assertEqual(resized.config.width, 12)
        self.assertEqual(resized.config.height, 9)

    def test_background_loop_lifecycle_smoke(self) -> None:
        self.manager.start_background_loop()
        self.assertIsNotNone(self.manager.runtime._thread)
        self.manager.stop_background_loop()
        self.assertIsNone(self.manager.runtime._thread)

    def test_persist_state_logs_save_failures_without_raising(self) -> None:
        failing_store = Mock()
        failing_store.load.return_value = None
        failing_store.save.side_effect = RuntimeError("boom")
        self.manager.stop_background_loop()
        self.manager = SimulationCoordinator(rule_registry=self.rule_registry, state_store=failing_store)

        with self.assertLogs("backend.simulation.coordinator", level="WARNING") as logs:
            self.manager.persist_state()

        self.assertIn("Failed to persist simulation state", "\n".join(logs.output))

    def test_restore_state_logs_invalid_payloads_without_raising(self) -> None:
        with (
            patch.object(self.manager, "_load_persisted_payload", return_value={"version": 4}),
            patch.object(self.manager, "_restore_payload", side_effect=RuntimeError("bad restore")),
            self.assertLogs("backend.simulation.coordinator", level="WARNING") as logs,
        ):
            self.manager.restore_state()

        self.assertIn("Persisted simulation state was invalid", "\n".join(logs.output))


if __name__ == "__main__":
    unittest.main()
