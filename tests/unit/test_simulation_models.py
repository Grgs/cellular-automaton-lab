import sys
import unittest
from pathlib import Path

try:
    from backend.defaults import MAX_GRID_SIZE, MAX_SPEED, MIN_GRID_SIZE
    from backend.rules.conway import ConwayLifeRule
    from backend.simulation.models import RuleSnapshot, SimulationConfig, SimulationSnapshot, SimulationStateData
    from backend.simulation.topology import parse_regular_cell_id
    from tests.unit.board_test_support import board_from_grid
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.defaults import MAX_GRID_SIZE, MAX_SPEED, MIN_GRID_SIZE
    from backend.rules.conway import ConwayLifeRule
    from backend.simulation.models import RuleSnapshot, SimulationConfig, SimulationSnapshot, SimulationStateData
    from backend.simulation.topology import parse_regular_cell_id
    from tests.unit.board_test_support import board_from_grid


class SimulationModelTests(unittest.TestCase):
    def test_simulation_config_clamps_values(self) -> None:
        config = SimulationConfig.from_values(
            topology_spec={"tiling_family": "triangle", "adjacency_mode": "edge", "width": 1, "height": 500},
            speed=99,
        )
        self.assertEqual(config.geometry, "triangle")
        self.assertEqual(config.width, MIN_GRID_SIZE)
        self.assertEqual(config.height, MAX_GRID_SIZE)
        self.assertEqual(config.speed, MAX_SPEED)

    def test_simulation_config_updated_preserves_existing_values(self) -> None:
        config = SimulationConfig.from_values(width=12, height=8, speed=4)
        updated = config.updated(height=10)
        self.assertEqual(updated.width, 12)
        self.assertEqual(updated.height, 10)
        self.assertEqual(updated.speed, 4.0)

    def test_grid_topology_specs_reset_patch_depth_to_default(self) -> None:
        config = SimulationConfig.from_values(
            topology_spec={
                "tiling_family": "square",
                "adjacency_mode": "edge",
                "width": 12,
                "height": 8,
                "patch_depth": 6,
            },
            speed=4,
        )
        self.assertEqual(config.patch_depth, 4)
        self.assertEqual(config.topology_spec.patch_depth, 4)

    def test_ammann_beenker_patch_depth_is_capped_at_four(self) -> None:
        config = SimulationConfig.from_values(
            topology_spec={
                "tiling_family": "ammann-beenker",
                "adjacency_mode": "edge",
                "width": 0,
                "height": 0,
                "patch_depth": 5,
            },
            speed=4,
        )
        self.assertEqual(config.patch_depth, 4)
        self.assertEqual(config.topology_spec.patch_depth, 4)

    def test_other_patch_depth_topologies_preserve_explicit_depth(self) -> None:
        config = SimulationConfig.from_values(
            topology_spec={
                "tiling_family": "penrose-p3-rhombs",
                "adjacency_mode": "edge",
                "width": 0,
                "height": 0,
                "patch_depth": 5,
            },
            speed=4,
        )
        self.assertEqual(config.patch_depth, 5)
        self.assertEqual(config.topology_spec.patch_depth, 5)

    def test_unsafe_size_override_allows_patch_depth_above_family_cap(self) -> None:
        config = SimulationConfig.from_values(
            topology_spec={
                "tiling_family": "spectre",
                "adjacency_mode": "edge",
                "width": 0,
                "height": 0,
                "patch_depth": 9,
                "unsafe_size_override": True,
            },
            speed=4,
        )

        self.assertEqual(config.patch_depth, 9)
        self.assertEqual(config.topology_spec.patch_depth, 9)

    def test_unsafe_size_override_survives_internal_config_updates(self) -> None:
        config = SimulationConfig.from_values(
            topology_spec={
                "tiling_family": "spectre",
                "adjacency_mode": "edge",
                "width": 0,
                "height": 0,
                "patch_depth": 8,
                "unsafe_size_override": True,
            },
            speed=4,
        )

        updated = config.updated(width=5, height=5)

        self.assertEqual(updated.patch_depth, 8)
        self.assertEqual(updated.topology_spec.patch_depth, 8)

    def test_rule_and_snapshot_serialize(self) -> None:
        rule = ConwayLifeRule()
        snapshot = SimulationSnapshot(
            board=board_from_grid([[0, 1], [1, 0]]),
            config=SimulationConfig.from_values(
                topology_spec={"tiling_family": "square", "adjacency_mode": "edge", "width": 2, "height": 2},
                speed=5,
            ),
            running=True,
            generation=3,
            rule=RuleSnapshot.from_rule(rule),
        )

        payload = snapshot.to_dict()
        self.assertEqual(payload["topology_spec"]["tiling_family"], "square")
        self.assertEqual(payload["topology_spec"]["width"], MIN_GRID_SIZE)
        self.assertEqual(payload["topology_spec"]["height"], MIN_GRID_SIZE)
        self.assertEqual(payload["rule"]["name"], "conway")
        self.assertEqual(payload["rule"]["default_paint_state"], 1)
        self.assertTrue(payload["rule"]["supports_randomize"])
        self.assertEqual(payload["rule"]["rule_protocol"], "universal-v1")
        self.assertTrue(payload["rule"]["supports_all_topologies"])
        self.assertNotIn("supported_topologies", payload["rule"])
        self.assertEqual(len(payload["rule"]["states"]), 2)
        self.assertTrue(payload["running"])
        self.assertEqual(payload["generation"], 3)
        self.assertEqual(payload["topology"]["topology_spec"]["tiling_family"], "square")
        self.assertEqual(len(payload["cell_states"]), 4)
        self.assertEqual(payload["topology_revision"], payload["topology"]["topology_revision"])
        self.assertNotIn("logical_x", payload["topology"]["cells"][0])
        self.assertNotIn("logical_y", payload["topology"]["cells"][0])

    def test_snapshot_state_payload_always_includes_topology(self) -> None:
        rule = ConwayLifeRule()
        snapshot = SimulationSnapshot(
            board=board_from_grid([[0, 1], [1, 0]]),
            config=SimulationConfig.from_values(
                topology_spec={"tiling_family": "square", "adjacency_mode": "edge", "width": 2, "height": 2},
                speed=5,
            ),
            running=False,
            generation=1,
            rule=RuleSnapshot.from_rule(rule),
        )

        payload = snapshot.to_dict()
        self.assertIn("topology", payload)
        self.assertEqual(payload["topology_revision"], snapshot.topology.topology_revision)
        self.assertEqual(payload["cell_states"], [0, 1, 1, 0])
        self.assertEqual(payload["topology"]["topology_revision"], payload["topology_revision"])

    def test_simulation_state_data_holds_runtime_fields(self) -> None:
        state = SimulationStateData(
            config=SimulationConfig.from_values(width=6, height=7, speed=8),
            running=True,
            generation=9,
            rule=ConwayLifeRule(),
            board=board_from_grid([[0] * 6 for _ in range(7)]),
        )

        self.assertTrue(state.running)
        self.assertEqual(state.generation, 9)
        self.assertEqual(state.config.width, 6)
        self.assertEqual(state.config.height, 7)
        self.assertEqual(state.rule.name, "conway")

    def test_parse_regular_cell_id_handles_regular_and_non_regular_ids(self) -> None:
        self.assertEqual(parse_regular_cell_id("c:12:8"), (12, 8))
        self.assertIsNone(parse_regular_cell_id("h:3:5"))
        self.assertIsNone(parse_regular_cell_id("cell"))


if __name__ == "__main__":
    unittest.main()
