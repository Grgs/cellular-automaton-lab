import json
import sys
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import ClassVar

try:
    from backend.defaults import APP_DEFAULTS
    from backend.rules import RuleRegistry
    from backend.simulation.coordinator import SimulationCoordinator
    from backend.simulation.models import SimulationSnapshot
    from backend.simulation.persistence import SNAPSHOT_VERSION, SimulationStateStore
    from tests.unit.board_test_support import regular_grid_from_board
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.defaults import APP_DEFAULTS
    from backend.rules import RuleRegistry
    from backend.simulation.coordinator import SimulationCoordinator
    from backend.simulation.models import SimulationSnapshot
    from backend.simulation.persistence import SNAPSHOT_VERSION, SimulationStateStore
    from tests.unit.board_test_support import regular_grid_from_board


class RecordingStateStore(SimulationStateStore):
    def __init__(self, path: str | Path) -> None:
        super().__init__(path)
        self.save_count = 0

    def save(self, snapshot: SimulationSnapshot) -> None:
        self.save_count += 1
        super().save(snapshot)


class FakeTimer:
    def __init__(self, delay_seconds: float, callback: Callable[[], None]) -> None:
        self.delay_seconds = delay_seconds
        self.callback = callback
        self.started = False
        self.cancelled = False

    def start(self) -> None:
        self.started = True

    def cancel(self) -> None:
        self.cancelled = True

    def fire(self) -> None:
        if not self.cancelled:
            self.callback()


class FakeTimerFactory:
    def __init__(self) -> None:
        self.timers: list[FakeTimer] = []

    def __call__(self, delay_seconds: float, callback: Callable[[], None]) -> FakeTimer:
        timer = FakeTimer(delay_seconds, callback)
        self.timers.append(timer)
        return timer

    def fire_latest(self) -> None:
        for timer in reversed(self.timers):
            if not timer.cancelled:
                timer.fire()
                return
        raise AssertionError("No active timer was scheduled.")


class SimulationPersistenceTests(unittest.TestCase):
    rule_registry: ClassVar[RuleRegistry]

    @classmethod
    def setUpClass(cls) -> None:
        cls.rule_registry = RuleRegistry()

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix="cellular-automaton-persistence-")
        self.state_path = Path(self.temp_dir.name) / "simulation_state.json"
        self.state_store = RecordingStateStore(self.state_path)
        self.timer_factory = FakeTimerFactory()
        self.manager: SimulationCoordinator | None = None

    def tearDown(self) -> None:
        if self.manager is not None:
            self.manager.shutdown()
        self.temp_dir.cleanup()

    def create_manager(self) -> SimulationCoordinator:
        manager = SimulationCoordinator(
            rule_registry=self.rule_registry,
            state_store=self.state_store,
            timer_factory=self.timer_factory,
        )
        self.manager = manager
        return manager

    def test_state_store_load_returns_none_when_snapshot_is_missing(self) -> None:
        self.assertIsNone(self.state_store.load())

    def test_state_store_load_rejects_non_object_payloads_and_unsupported_versions(self) -> None:
        self.state_path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "JSON object"):
            self.state_store.load()

        self.state_path.write_text(json.dumps({"version": SNAPSHOT_VERSION - 1}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unsupported"):
            self.state_store.load()

    def test_state_store_load_rejects_invalid_snapshot_fields(self) -> None:
        self.state_path.write_text(
            json.dumps(
                {
                    "version": SNAPSHOT_VERSION,
                    "topology_spec": "bad",
                    "speed": 5,
                    "running": False,
                    "generation": 0,
                    "rule": "conway",
                    "cells_by_id": {},
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "topology spec"):
            self.state_store.load()

        self.state_path.write_text(
            json.dumps(
                {
                    "version": SNAPSHOT_VERSION,
                    "topology_spec": {
                        "tiling_family": "square",
                        "adjacency_mode": "edge",
                        "width": 10,
                        "height": 6,
                        "patch_depth": 4,
                    },
                    "speed": 5,
                    "running": False,
                    "generation": 0,
                    "rule": "conway",
                    "cells_by_id": {"c:1:1": "bad"},
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "cells_by_id"):
            self.state_store.load()

    def test_serialize_snapshot_persists_topology_spec_and_sparse_cells_only(self) -> None:
        manager = self.create_manager()
        manager.toggle_cell_by_id("c:1:1")
        self.timer_factory.fire_latest()

        payload = self.state_store.load()
        assert payload is not None

        self.assertEqual(payload["version"], SNAPSHOT_VERSION)
        self.assertEqual(
            payload["topology_spec"], manager.get_state().config.topology_spec.to_dict()
        )
        self.assertEqual(payload["cells_by_id"], {"c:1:1": 1})
        self.assertNotIn("grid", payload)
        self.assertNotIn("cell_states", payload)

    def test_deferred_cell_edits_flush_after_timer_fires(self) -> None:
        manager = self.create_manager()
        manager.toggle_cell_by_id("c:1:1")

        self.assertIsNone(self.state_store.load())

        self.timer_factory.fire_latest()
        payload = self.state_store.load()
        assert payload is not None

        self.assertEqual(payload["version"], SNAPSHOT_VERSION)
        self.assertEqual(payload["topology_spec"]["tiling_family"], "square")
        self.assertEqual(payload["topology_spec"]["adjacency_mode"], "edge")
        self.assertEqual(payload["rule"], manager.get_state().rule.name)
        self.assertEqual(payload["generation"], 0)
        self.assertEqual(payload["cells_by_id"], {"c:1:1": 1})

    def test_state_store_persists_archimedean_cell_states_without_grid(self) -> None:
        manager = self.create_manager()
        manager.reset(
            topology_spec={
                "tiling_family": "archimedean-4-8-8",
                "adjacency_mode": "edge",
                "width": 5,
                "height": 5,
            },
            randomize=False,
        )
        manager.set_cells_by_id([("o:2:2", 1), ("s:2:2", 1)])
        self.timer_factory.fire_latest()

        payload = self.state_store.load()
        assert payload is not None

        self.assertEqual(payload["topology_spec"]["tiling_family"], "archimedean-4-8-8")
        self.assertEqual(payload["rule"], "archlife488")
        self.assertNotIn("cell_states", payload)
        self.assertNotIn("grid", payload)
        self.assertEqual(payload["cells_by_id"], {"o:2:2": 1, "s:2:2": 1})

    def test_state_store_persists_kagome_cell_states_without_grid(self) -> None:
        manager = self.create_manager()
        manager.reset(
            topology_spec={
                "tiling_family": "trihexagonal-3-6-3-6",
                "adjacency_mode": "edge",
                "width": 4,
                "height": 4,
            },
            randomize=False,
        )
        manager.set_cells_by_id([("h:1:1", 1), ("tu:1:1", 1), ("td:1:1", 1)])
        self.timer_factory.fire_latest()

        payload = self.state_store.load()
        assert payload is not None

        self.assertEqual(payload["topology_spec"]["tiling_family"], "trihexagonal-3-6-3-6")
        self.assertEqual(payload["rule"], "kagome-life")
        self.assertNotIn("cell_states", payload)
        self.assertNotIn("grid", payload)
        self.assertEqual(payload["cells_by_id"], {"h:1:1": 1, "tu:1:1": 1, "td:1:1": 1})

    def test_manager_uses_defaults_when_no_persisted_state_exists(self) -> None:
        manager = self.create_manager()
        state = manager.get_state()

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
        self.assertEqual(state.config.width, APP_DEFAULTS["simulation"]["topology_spec"]["width"])
        self.assertEqual(state.config.height, APP_DEFAULTS["simulation"]["topology_spec"]["height"])
        self.assertFalse(state.running)
        self.assertEqual(state.generation, 0)
        self.assertEqual(state.rule.name, APP_DEFAULTS["simulation"]["rule"])

    def test_manager_uses_defaults_when_persisted_state_is_corrupt(self) -> None:
        self.state_path.write_text("{bad json", encoding="utf-8")

        with self.assertLogs("backend.simulation.coordinator", level="WARNING"):
            manager = self.create_manager()
        state = manager.get_state()

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
        self.assertEqual(state.config.width, APP_DEFAULTS["simulation"]["topology_spec"]["width"])
        self.assertEqual(state.config.height, APP_DEFAULTS["simulation"]["topology_spec"]["height"])
        self.assertFalse(state.running)
        self.assertEqual(state.generation, 0)
        self.assertEqual(state.rule.name, APP_DEFAULTS["simulation"]["rule"])

    def test_manager_restores_state_from_store_and_forces_paused(self) -> None:
        self.state_path.write_text(
            json.dumps(
                {
                    "version": SNAPSHOT_VERSION,
                    "topology_spec": {
                        "tiling_family": "hex",
                        "adjacency_mode": "edge",
                        "width": 7,
                        "height": 5,
                        "patch_depth": 4,
                        "sizing_mode": "grid",
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
                }
            ),
            encoding="utf-8",
        )

        manager = self.create_manager()
        restored = manager.get_state()

        self.assertEqual(restored.config.geometry, "hex")
        self.assertEqual(restored.config.width, 7)
        self.assertEqual(restored.config.height, 5)
        self.assertEqual(restored.config.speed, 9.0)
        self.assertFalse(restored.running)
        self.assertEqual(restored.generation, 4)
        self.assertEqual(restored.rule.name, "whirlpool")
        restored_grid = regular_grid_from_board(restored.board)
        assert restored_grid is not None
        self.assertEqual(restored_grid[1][1:4], [1, 2, 3])

    def test_deferred_cell_edits_leave_existing_snapshot_unchanged_until_timer_fires(self) -> None:
        manager = self.create_manager()
        manager.reset(randomize=False)
        baseline_payload = self.state_store.load()
        assert baseline_payload is not None
        manager.toggle_cell_by_id("c:1:1")

        persisted_before_timer = self.state_store.load()
        assert persisted_before_timer is not None
        self.assertEqual(persisted_before_timer["cells_by_id"], baseline_payload["cells_by_id"])

        self.timer_factory.fire_latest()
        persisted_after_timer = self.state_store.load()
        assert persisted_after_timer is not None
        self.assertEqual(persisted_after_timer["cells_by_id"], {"c:1:1": 1})

    def test_immediate_mutations_flush_without_waiting(self) -> None:
        manager = self.create_manager()
        manager.step()
        persisted_after_step = self.state_store.load()
        assert persisted_after_step is not None
        self.assertEqual(persisted_after_step["generation"], 1)

        manager.start()
        persisted_after_start = self.state_store.load()
        assert persisted_after_start is not None
        manager.runtime.run_once()
        persisted_after_runtime_step = self.state_store.load()
        assert persisted_after_runtime_step is not None

        manager.update_config(speed=7)
        persisted_after_update = self.state_store.load()
        assert persisted_after_update is not None
        manager.resume()
        persisted_after_resume = self.state_store.load()
        assert persisted_after_resume is not None
        manager.pause()
        persisted_after_pause = self.state_store.load()
        assert persisted_after_pause is not None
        manager.reset(topology_spec={"width": 12, "height": 7}, randomize=False)
        persisted_after_reset = self.state_store.load()
        assert persisted_after_reset is not None

        self.assertEqual(persisted_after_update["speed"], 7.0)
        self.assertFalse(persisted_after_start["running"])
        self.assertEqual(persisted_after_runtime_step["generation"], 1)
        self.assertTrue(persisted_after_update["running"])
        self.assertTrue(persisted_after_resume["running"])
        self.assertEqual(persisted_after_pause["generation"], 2)
        self.assertFalse(persisted_after_pause["running"])
        self.assertEqual(persisted_after_reset["topology_spec"]["width"], 12)
        self.assertEqual(persisted_after_reset["topology_spec"]["height"], 7)

    def test_immediate_flush_cancels_pending_deferred_timer(self) -> None:
        manager = self.create_manager()
        manager.toggle_cell_by_id("c:1:1")

        self.assertEqual(self.state_store.save_count, 0)

        manager.step()
        self.assertEqual(self.state_store.save_count, 1)

        self.assertTrue(self.timer_factory.timers[-1].cancelled)
        self.timer_factory.timers[-1].fire()
        self.assertEqual(self.state_store.save_count, 1)

    def test_shutdown_persists_latest_runtime_state_for_restore(self) -> None:
        manager = self.create_manager()
        manager.toggle_cell_by_id("c:1:1")
        manager.start()
        manager.runtime.run_once()
        current_state = manager.get_state()
        manager.shutdown()
        self.manager = None

        restored_manager = self.create_manager()
        restored = restored_manager.get_state()

        self.assertEqual(restored.generation, current_state.generation)
        self.assertEqual(
            regular_grid_from_board(restored.board),
            regular_grid_from_board(current_state.board),
        )
        self.assertFalse(restored.running)


if __name__ == "__main__":
    unittest.main()
