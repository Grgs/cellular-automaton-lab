import unittest
from typing import ClassVar

from hypothesis import given
from hypothesis import strategies as st

from backend.rules import RuleRegistry
from backend.simulation.topology_catalog import (
    HEX_GEOMETRY,
    PENROSE_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
    SQUARE_GEOMETRY,
    minimum_grid_dimension_for_geometry,
)
from backend.simulation.models import SimulationConfig, SimulationStateData
from backend.simulation.topology import empty_board
from backend.simulation.transition_planner import plan_config_transition, plan_reset_transition


class HypothesisTransitionPlannerTests(unittest.TestCase):
    rule_registry: ClassVar[RuleRegistry]

    @classmethod
    def setUpClass(cls) -> None:
        cls.rule_registry = RuleRegistry()

    def create_regular_state(self, geometry: str = "square") -> SimulationStateData:
        config = SimulationConfig.from_values(topology_spec={"tiling_family": geometry, "adjacency_mode": "edge", "width": 10, "height": 6}, speed=5)
        board = empty_board(geometry, config.width, config.height)
        return SimulationStateData(
            config=config,
            running=False,
            generation=0,
            rule=self.rule_registry.default_for_geometry(geometry),
            board=board,
        )

    def create_penrose_state(self, geometry: str) -> SimulationStateData:
        board = empty_board(geometry, 10, 6, patch_depth=4)
        return SimulationStateData(
            config=SimulationConfig.from_values(
                topology_spec={
                    "tiling_family": "penrose-p3-rhombs" if geometry == PENROSE_VERTEX_GEOMETRY else geometry,
                    "adjacency_mode": "vertex" if geometry == PENROSE_VERTEX_GEOMETRY else "edge",
                    "width": board.topology.width,
                    "height": board.topology.height,
                    "patch_depth": 4,
                },
                speed=5,
            ),
            running=False,
            generation=0,
            rule=self.rule_registry.default_for_geometry(geometry),
            board=board,
        )

    @given(
        width=st.integers(min_value=1, max_value=40),
        height=st.integers(min_value=1, max_value=40),
    )
    def test_whirlpool_reset_plan_preserves_rectangular_dimensions(
        self,
        width: int,
        height: int,
    ) -> None:
        plan = plan_reset_transition(
            self.create_regular_state(SQUARE_GEOMETRY),
            self.rule_registry,
            topology_spec={"width": width, "height": height},
            rule_name="whirlpool",
        )
        expected_width = max(width, minimum_grid_dimension_for_geometry(SQUARE_GEOMETRY))
        expected_height = max(height, minimum_grid_dimension_for_geometry(SQUARE_GEOMETRY))

        self.assertEqual(plan.config.width, expected_width)
        self.assertEqual(plan.config.height, expected_height)
        self.assertEqual(plan.rule.name, "whirlpool")

    @given(
        width=st.integers(min_value=1, max_value=40),
        height=st.integers(min_value=1, max_value=40),
    )
    def test_hexwhirlpool_config_plan_preserves_rectangular_dimensions(
        self,
        width: int,
        height: int,
    ) -> None:
        plan = plan_config_transition(
            self.create_regular_state(HEX_GEOMETRY),
            self.rule_registry,
            topology_spec={"width": width, "height": height},
            rule_name="hexwhirlpool",
        )
        expected_width = max(width, minimum_grid_dimension_for_geometry(HEX_GEOMETRY))
        expected_height = max(height, minimum_grid_dimension_for_geometry(HEX_GEOMETRY))

        self.assertEqual(plan.config.width, expected_width)
        self.assertEqual(plan.config.height, expected_height)
        self.assertEqual(plan.rule.name, "whirlpool")

    @given(
        geometry=st.sampled_from((PENROSE_GEOMETRY, PENROSE_VERTEX_GEOMETRY)),
        width=st.integers(min_value=1, max_value=200),
        height=st.integers(min_value=1, max_value=200),
    )
    def test_penrose_config_plan_ignores_width_and_height_updates(
        self,
        geometry: str,
        width: int,
        height: int,
    ) -> None:
        state = self.create_penrose_state(geometry)
        plan = plan_config_transition(
            state,
            self.rule_registry,
            topology_spec={"width": width, "height": height},
            speed=7,
        )

        self.assertEqual(plan.config.width, state.config.width)
        self.assertEqual(plan.config.height, state.config.height)
        self.assertEqual(plan.config.patch_depth, state.config.patch_depth)
        self.assertEqual(plan.board_mode, "reuse")
        self.assertEqual(plan.config.speed, 7.0)


if __name__ == "__main__":
    unittest.main()
