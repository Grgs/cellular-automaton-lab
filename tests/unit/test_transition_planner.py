import unittest
from typing import ClassVar

from backend.payload_types import TopologySpecPatch, TopologySpecPayload
from backend.rules import RuleRegistry
from backend.simulation.models import SimulationConfig, SimulationStateData
from backend.simulation.topology import empty_board
from backend.simulation.transition_planner import (
    plan_config_transition,
    plan_reset_transition,
    plan_restore_transition,
)
from tests.unit.board_test_support import board_from_grid


class TransitionPlannerTests(unittest.TestCase):
    rule_registry: ClassVar[RuleRegistry]

    @classmethod
    def setUpClass(cls) -> None:
        cls.rule_registry = RuleRegistry()

    def create_regular_state(self) -> SimulationStateData:
        topology_spec: TopologySpecPayload = {
            "tiling_family": "square",
            "adjacency_mode": "edge",
            "sizing_mode": "grid",
            "width": 10,
            "height": 6,
            "patch_depth": 0,
        }
        config = SimulationConfig.from_values(
            topology_spec=topology_spec,
            speed=5,
        )
        return SimulationStateData(
            config=config,
            running=False,
            generation=0,
            rule=self.rule_registry.get("conway"),
            board=board_from_grid([[0] * config.width for _ in range(config.height)]),
        )

    def create_penrose_state(self, geometry: str = "penrose-p3-rhombs") -> SimulationStateData:
        board = empty_board(geometry, 10, 6, patch_depth=4)
        topology_spec: TopologySpecPayload = {
            "tiling_family": "penrose-p3-rhombs" if geometry == "penrose-p3-rhombs-vertex" else geometry,
            "adjacency_mode": "vertex" if geometry == "penrose-p3-rhombs-vertex" else "edge",
            "sizing_mode": "patch_depth",
            "patch_depth": 4,
            "width": board.topology.width,
            "height": board.topology.height,
        }
        return SimulationStateData(
            config=SimulationConfig.from_values(
                topology_spec=topology_spec,
                speed=5,
            ),
            running=False,
            generation=0,
            rule=self.rule_registry.default_for_geometry(geometry),
            board=board,
        )

    def test_reset_plan_uses_geometry_default_rule_and_normalized_config(self) -> None:
        plan = plan_reset_transition(
            self.create_regular_state(),
            self.rule_registry,
            topology_spec={"tiling_family": "hex", "adjacency_mode": "edge", "width": 9, "height": 7},
            speed=6,
        )

        self.assertEqual(plan.config.geometry, "hex")
        self.assertEqual(plan.config.width, 9)
        self.assertEqual(plan.config.height, 7)
        self.assertEqual(plan.config.speed, 6.0)
        self.assertEqual(plan.rule.name, "hexlife")
        self.assertEqual(plan.board_mode, "empty")

    def test_reset_plan_marks_randomized_resets(self) -> None:
        plan = plan_reset_transition(
            self.create_regular_state(),
            self.rule_registry,
            rule_name="conway",
            randomize=True,
        )

        self.assertEqual(plan.board_mode, "randomize")

    def test_config_plan_ignores_resize_for_patch_depth_geometries(self) -> None:
        state = self.create_penrose_state()
        resize_patch: TopologySpecPatch = {"width": 999, "height": 888}
        plan = plan_config_transition(
            state,
            self.rule_registry,
            topology_spec=resize_patch,
            speed=7,
            rule_name="penrose-greenberg-hastings",
        )

        self.assertEqual(plan.config.geometry, "penrose-p3-rhombs")
        self.assertEqual(plan.config.width, state.config.width)
        self.assertEqual(plan.config.height, state.config.height)
        self.assertEqual(plan.config.patch_depth, 4)
        self.assertEqual(plan.config.speed, 7.0)
        self.assertEqual(plan.rule.name, "penrose-greenberg-hastings")
        self.assertEqual(plan.board_mode, "reuse")
        self.assertTrue(plan.coerce_rule_states)

    def test_config_plan_preserves_rectangular_whirlpool_dimensions(self) -> None:
        resize_patch: TopologySpecPatch = {"width": 12, "height": 8}
        plan = plan_config_transition(
            self.create_regular_state(),
            self.rule_registry,
            topology_spec=resize_patch,
            rule_name="whirlpool",
        )

        self.assertEqual(plan.config.width, 12)
        self.assertEqual(plan.config.height, 8)
        self.assertEqual(plan.rule.name, "whirlpool")
        self.assertEqual(plan.board_mode, "transfer")
        self.assertTrue(plan.coerce_rule_states)

    def test_config_plan_reuses_board_when_only_speed_changes(self) -> None:
        plan = plan_config_transition(
            self.create_regular_state(),
            self.rule_registry,
            speed=9,
        )

        self.assertEqual(plan.board_mode, "reuse")
        self.assertFalse(plan.coerce_rule_states)
        self.assertEqual(plan.config.speed, 9.0)

    def test_restore_plan_preserves_requested_rule_across_topologies(self) -> None:
        plan = plan_restore_transition(
            {
                "topology_spec": {
                    "tiling_family": "triangle",
                    "adjacency_mode": "edge",
                    "width": 5,
                    "height": 4,
                },
                "speed": 8,
                "generation": 6,
                "rule": "conway",
                "cells_by_id": {"c:0:0": 1, "c:2:0": 1, "c:4:0": 1},
            },
            fallback_state=self.create_regular_state(),
            rule_registry=self.rule_registry,
        )

        self.assertEqual(plan.config.geometry, "triangle")
        self.assertEqual(plan.rule.name, "conway")
        self.assertEqual(plan.board_payload_kind, "cells_by_id")
        self.assertEqual(plan.generation, 6)

    def test_restore_plan_distinguishes_grid_and_cell_state_payloads(self) -> None:
        cell_state_plan = plan_restore_transition(
            {
                "topology_spec": {
                    "tiling_family": "trihexagonal-3-6-3-6",
                    "adjacency_mode": "edge",
                    "width": 4,
                    "height": 4,
                },
                "rule": "kagome-life",
                "cells_by_id": {"h:0:0": 1},
            },
            fallback_state=self.create_regular_state(),
            rule_registry=self.rule_registry,
        )
        empty_plan = plan_restore_transition(
            {"topology_spec": {"tiling_family": "square", "adjacency_mode": "edge"}},
            fallback_state=self.create_regular_state(),
            rule_registry=self.rule_registry,
        )

        self.assertEqual(cell_state_plan.board_payload_kind, "cells_by_id")
        self.assertEqual(cell_state_plan.rule.name, "kagome-life")
        self.assertEqual(empty_plan.board_payload_kind, "empty")


if __name__ == "__main__":
    unittest.main()
