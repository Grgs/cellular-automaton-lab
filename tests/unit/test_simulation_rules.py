import sys
import unittest
from pathlib import Path
from typing import ClassVar, TypedDict

try:
    from backend.defaults import DEFAULT_RULE_NAME
    from backend.rules import RuleRegistry
    from backend.rules.base import AutomatonRule
    from backend.rules.archlife488 import ArchLife488Rule
    from backend.rules.archlife_extended import (
        ArchLife31212Rule,
        ArchLife33336Rule,
        ArchLife33344Rule,
        ArchLife33434Rule,
        ArchLife3464Rule,
        ArchLife4612Rule,
    )
    from backend.rules.hexlife import HexLifeRule
    from backend.rules.kagome_life import KagomeLifeRule
    from backend.rules.life_b2s23 import LifeB2S23Rule
    from backend.rules.penrose_greenberg_hastings import PenroseGreenbergHastingsRule
    from backend.rules.trilife import TriLifeRule
    from backend.rules.whirlpool import WhirlpoolRule
    from backend.rules.wireworld import WireWorldRule
    from backend.simulation.models import RuleSnapshot
    from backend.simulation.rule_context import (
        RuleContext,
        TopologyCellFrame,
        TopologyFrame,
        TopologyNeighborFrame,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.defaults import DEFAULT_RULE_NAME
    from backend.rules import RuleRegistry
    from backend.rules.base import AutomatonRule
    from backend.rules.archlife488 import ArchLife488Rule
    from backend.rules.archlife_extended import (
        ArchLife31212Rule,
        ArchLife33336Rule,
        ArchLife33344Rule,
        ArchLife33434Rule,
        ArchLife3464Rule,
        ArchLife4612Rule,
    )
    from backend.rules.hexlife import HexLifeRule
    from backend.rules.kagome_life import KagomeLifeRule
    from backend.rules.life_b2s23 import LifeB2S23Rule
    from backend.rules.penrose_greenberg_hastings import PenroseGreenbergHastingsRule
    from backend.rules.trilife import TriLifeRule
    from backend.rules.whirlpool import WhirlpoolRule
    from backend.rules.wireworld import WireWorldRule
    from backend.simulation.models import RuleSnapshot
    from backend.simulation.rule_context import (
        RuleContext,
        TopologyCellFrame,
        TopologyFrame,
        TopologyNeighborFrame,
    )


class NeighborSpec(TypedDict):
    id: str
    state: int
    radial: str
    turn: str
    radial_delta: float
    angle_delta: float
    clockwise_index: int
    kind: str
    shell_rank: int
    radial_ratio: float


def make_neighbor_spec(
    state: int,
    *,
    neighbor_id: str,
    radial: str = "level",
    turn: str = "aligned",
    radial_delta: float = 0.0,
    angle_delta: float = 0.0,
    clockwise_index: int = 0,
    kind: str = "neighbor",
    shell_rank: int = 1,
    radial_ratio: float = 0.5,
) -> NeighborSpec:
    return {
        "id": neighbor_id,
        "state": state,
        "radial": radial,
        "turn": turn,
        "radial_delta": radial_delta,
        "angle_delta": angle_delta,
        "clockwise_index": clockwise_index,
        "kind": kind,
        "shell_rank": shell_rank,
        "radial_ratio": radial_ratio,
    }


def build_context(
    current_state: int,
    *,
    neighbor_specs: list[NeighborSpec] | None = None,
    kind: str = "cell",
    shell_rank: int = 1,
    radial_ratio: float = 0.5,
    cell_id: str = "cell",
) -> RuleContext:
    neighbor_specs = neighbor_specs or []
    current_neighbors = tuple(
        TopologyNeighborFrame(
            index=index + 1,
            radial=spec["radial"],
            turn=spec["turn"],
            radial_delta=float(spec["radial_delta"]),
            angle_delta=float(spec["angle_delta"]),
            clockwise_index=int(spec["clockwise_index"]),
        )
        for index, spec in enumerate(neighbor_specs)
    )
    cells = [
        TopologyCellFrame(
            id=cell_id,
            kind=kind,
            center=(0.0, 0.0),
            vertices=None,
            degree=len(current_neighbors),
            shell_rank=shell_rank,
            radial_distance=float(radial_ratio),
            radial_ratio=radial_ratio,
            polar_angle=0.0,
            neighbors=current_neighbors,
        )
    ]
    states = [current_state]
    for spec in neighbor_specs:
        cells.append(
            TopologyCellFrame(
                id=spec["id"],
                kind=spec["kind"],
                center=(0.0, 0.0),
                vertices=None,
                degree=0,
                shell_rank=int(spec["shell_rank"]),
                radial_distance=float(spec["radial_ratio"]),
                radial_ratio=float(spec["radial_ratio"]),
                polar_angle=0.0,
                neighbors=(),
            )
        )
        states.append(int(spec["state"]))
    frame = TopologyFrame(
        adjacency_mode="edge",
        topology_revision=f"ctx:{cell_id}:{len(neighbor_specs)}",
        center=(0.0, 0.0),
        cell_count=len(cells),
        bounds=(0.0, 0.0, 0.0, 0.0),
        max_shell_rank=max(
            [shell_rank, *[int(spec["shell_rank"]) for spec in neighbor_specs]], default=shell_rank
        ),
        max_radial_distance=1.0,
        cells=tuple(cells),
        _index_by_id={cell.id: index for index, cell in enumerate(cells)},
    )
    return RuleContext(frame, states, 0)


def build_source_context(rule: WhirlpoolRule, *, target_state: int | None = None) -> RuleContext:
    resolved_target_state = rule.RESTING if target_state is None else target_state
    cells = (
        TopologyCellFrame(
            id="target",
            kind="cell",
            center=(0.0, 0.0),
            vertices=None,
            degree=1,
            shell_rank=1,
            radial_distance=0.5,
            radial_ratio=0.5,
            polar_angle=0.0,
            neighbors=(
                TopologyNeighborFrame(
                    index=1,
                    radial="inward",
                    turn="aligned",
                    radial_delta=-0.2,
                    angle_delta=0.0,
                    clockwise_index=0,
                ),
            ),
        ),
        TopologyCellFrame(
            id="source",
            kind="cell",
            center=(1.0, 0.0),
            vertices=None,
            degree=3,
            shell_rank=2,
            radial_distance=0.8,
            radial_ratio=0.8,
            polar_angle=0.0,
            neighbors=(
                TopologyNeighborFrame(
                    index=0,
                    radial="outward",
                    turn="clockwise",
                    radial_delta=0.4,
                    angle_delta=-0.3,
                    clockwise_index=0,
                ),
                TopologyNeighborFrame(
                    index=2,
                    radial="level",
                    turn="aligned",
                    radial_delta=0.0,
                    angle_delta=0.0,
                    clockwise_index=1,
                ),
                TopologyNeighborFrame(
                    index=3,
                    radial="inward",
                    turn="counterclockwise",
                    radial_delta=-0.4,
                    angle_delta=0.2,
                    clockwise_index=2,
                ),
            ),
        ),
        TopologyCellFrame(
            id="fallback",
            kind="cell",
            center=(1.0, 1.0),
            vertices=None,
            degree=0,
            shell_rank=2,
            radial_distance=0.9,
            radial_ratio=0.9,
            polar_angle=0.0,
            neighbors=(),
        ),
        TopologyCellFrame(
            id="excited",
            kind="cell",
            center=(2.0, 0.0),
            vertices=None,
            degree=0,
            shell_rank=3,
            radial_distance=1.0,
            radial_ratio=1.0,
            polar_angle=0.0,
            neighbors=(),
        ),
    )
    frame = TopologyFrame(
        adjacency_mode="edge",
        topology_revision="source-test",
        center=(0.0, 0.0),
        cell_count=4,
        bounds=(0.0, 0.0, 0.0, 0.0),
        max_shell_rank=3,
        max_radial_distance=1.0,
        cells=cells,
        _index_by_id={cell.id: index for index, cell in enumerate(cells)},
    )
    return RuleContext(frame, [resolved_target_state, rule.SOURCE, rule.RESTING, rule.EXCITED], 0)


class SimulationRuleTests(unittest.TestCase):
    rule_registry: ClassVar[RuleRegistry]

    @classmethod
    def setUpClass(cls) -> None:
        cls.rule_registry = RuleRegistry()

    def test_rule_registry_includes_expected_rules(self) -> None:
        self.assertTrue(self.rule_registry.has("archlife488"))
        self.assertTrue(self.rule_registry.has("hexlife"))
        self.assertTrue(self.rule_registry.has("hexwhirlpool"))
        self.assertTrue(self.rule_registry.has("kagome-life"))
        self.assertTrue(self.rule_registry.has("life-b2-s23"))
        self.assertTrue(self.rule_registry.has("penrose-life"))
        self.assertTrue(self.rule_registry.has("penrose-vertex-life"))
        self.assertTrue(self.rule_registry.has("whirlpool"))
        self.assertFalse(self.rule_registry.has("ammann-beenker-life"))
        self.assertFalse(self.rule_registry.has("custom"))

    def test_rule_registry_falls_back_to_default_rule_for_none_or_unknown_names(self) -> None:
        default_rule = self.rule_registry.get(None)

        self.assertEqual(default_rule.name, DEFAULT_RULE_NAME)
        self.assertIs(self.rule_registry.get("missing-rule"), default_rule)
        self.assertEqual(
            self.rule_registry.default_for_geometry("archimedean-4-8-8").name, "archlife488"
        )
        self.assertEqual(self.rule_registry.default_for_geometry("hex").name, "hexlife")
        self.assertEqual(self.rule_registry.default_for_geometry("triangle").name, "trilife")
        self.assertEqual(
            self.rule_registry.default_for_geometry("penrose-p3-rhombs").name, "life-b2-s23"
        )
        self.assertEqual(
            self.rule_registry.default_for_geometry("penrose-p3-rhombs-vertex").name, "conway"
        )

    def test_rule_registry_uses_general_fallback_when_geometry_has_no_default(self) -> None:
        self.assertEqual(
            self.rule_registry.default_for_geometry("missing-geometry").name, DEFAULT_RULE_NAME
        )

    def test_rule_registry_describes_rules_in_display_name_order(self) -> None:
        descriptions = self.rule_registry.describe_rules()
        display_names = [rule["display_name"] for rule in descriptions]
        rule_names = [rule["name"] for rule in descriptions]

        self.assertEqual(display_names, sorted(display_names, key=str.lower))
        self.assertNotIn("hexwhirlpool", rule_names)
        for description in descriptions:
            self.assertEqual(description["rule_protocol"], "universal-v1")
            self.assertTrue(description["supports_all_topologies"])
            self.assertNotIn("supported_topologies", description)

    def assert_rule_snapshot(self, rule: AutomatonRule) -> None:
        payload = RuleSnapshot.from_rule(rule).to_dict()
        self.assertEqual(payload["rule_protocol"], "universal-v1")
        self.assertTrue(payload["supports_all_topologies"])
        self.assertNotIn("supported_topologies", payload)

    def test_wireworld_rule_transitions(self) -> None:
        rule = WireWorldRule()
        self.assert_rule_snapshot(rule)

        self.assertEqual(rule.next_state(build_context(0)), 0)
        self.assertEqual(rule.next_state(build_context(1)), 2)
        self.assertEqual(rule.next_state(build_context(2)), 3)
        self.assertEqual(
            rule.next_state(
                build_context(
                    3,
                    neighbor_specs=[
                        make_neighbor_spec(1, neighbor_id="n0"),
                        make_neighbor_spec(1, neighbor_id="n1"),
                    ],
                )
            ),
            1,
        )

    def test_whirlpool_rule_metadata_and_state_cycle(self) -> None:
        rule = WhirlpoolRule()

        self.assertEqual(rule.name, "whirlpool")
        self.assertEqual(rule.display_name, "Excitable: Outward Whirlpool")
        self.assertEqual([state.value for state in rule.state_definitions()], [0, 1, 2, 3, 4])
        self.assertEqual(rule.default_paint_state, 1)
        self.assertFalse(rule.supports_randomize)
        self.assert_rule_snapshot(rule)
        self.assertEqual(rule.next_state(build_context(rule.EXCITED)), rule.TRAILING)
        self.assertEqual(rule.next_state(build_context(rule.TRAILING)), rule.REFRACTORY)
        self.assertEqual(
            rule.next_state(build_context(rule.REFRACTORY, shell_rank=1, radial_ratio=0.4)),
            rule.RESTING,
        )
        self.assertEqual(rule.next_state(build_context(rule.SOURCE)), rule.SOURCE)

    def test_hexlife_rule_metadata_and_transitions(self) -> None:
        rule = HexLifeRule()
        self.assert_rule_snapshot(rule)
        self.assertTrue(rule.supports_randomize)
        self.assertEqual(
            rule.next_state(
                build_context(
                    0,
                    neighbor_specs=[
                        make_neighbor_spec(1, neighbor_id="n0"),
                        make_neighbor_spec(1, neighbor_id="n1"),
                    ],
                )
            ),
            1,
        )
        self.assertEqual(
            rule.next_state(
                build_context(
                    1,
                    neighbor_specs=[
                        make_neighbor_spec(1, neighbor_id=f"n{index}") for index in range(3)
                    ],
                )
            ),
            1,
        )
        self.assertEqual(
            rule.next_state(
                build_context(
                    1,
                    neighbor_specs=[
                        make_neighbor_spec(1, neighbor_id=f"n{index}") for index in range(4)
                    ],
                )
            ),
            1,
        )
        self.assertEqual(
            rule.next_state(
                build_context(
                    1,
                    neighbor_specs=[
                        make_neighbor_spec(1, neighbor_id=f"n{index}") for index in range(2)
                    ],
                )
            ),
            0,
        )

    def test_trilife_rule_metadata_and_transitions(self) -> None:
        rule = TriLifeRule()
        self.assert_rule_snapshot(rule)
        self.assertTrue(rule.supports_randomize)
        self.assertEqual(
            rule.next_state(
                build_context(
                    0,
                    neighbor_specs=[
                        make_neighbor_spec(1, neighbor_id=f"n{index}") for index in range(4)
                    ],
                )
            ),
            1,
        )
        self.assertEqual(
            rule.next_state(
                build_context(
                    1,
                    neighbor_specs=[
                        make_neighbor_spec(1, neighbor_id=f"n{index}") for index in range(4)
                    ],
                )
            ),
            1,
        )
        self.assertEqual(
            rule.next_state(
                build_context(
                    1,
                    neighbor_specs=[
                        make_neighbor_spec(1, neighbor_id=f"n{index}") for index in range(5)
                    ],
                )
            ),
            1,
        )

    def test_archlife_rule_metadata_and_kind_specific_transitions(self) -> None:
        rule = ArchLife488Rule()
        self.assert_rule_snapshot(rule)
        self.assertTrue(rule.supports_randomize)
        self.assertEqual(
            rule.next_state(
                build_context(
                    0,
                    kind="square",
                    neighbor_specs=[
                        make_neighbor_spec(1, neighbor_id="a"),
                        make_neighbor_spec(1, neighbor_id="b"),
                    ],
                )
            ),
            1,
        )
        self.assertEqual(
            rule.next_state(
                build_context(
                    1,
                    kind="square",
                    neighbor_specs=[
                        make_neighbor_spec(1, neighbor_id="a"),
                        make_neighbor_spec(1, neighbor_id="b"),
                    ],
                )
            ),
            1,
        )
        self.assertEqual(
            rule.next_state(
                build_context(
                    0,
                    kind="octagon",
                    neighbor_specs=[
                        make_neighbor_spec(1, neighbor_id=f"n{index}") for index in range(3)
                    ],
                )
            ),
            1,
        )

    def test_kagome_rule_metadata_and_kind_specific_transitions(self) -> None:
        rule = KagomeLifeRule()
        self.assert_rule_snapshot(rule)
        self.assertTrue(rule.supports_randomize)
        self.assertEqual(
            rule.next_state(
                build_context(
                    0,
                    kind="triangle-up",
                    neighbor_specs=[
                        make_neighbor_spec(1, neighbor_id="a"),
                        make_neighbor_spec(1, neighbor_id="b"),
                    ],
                )
            ),
            1,
        )
        self.assertEqual(
            rule.next_state(
                build_context(
                    0,
                    kind="hexagon",
                    neighbor_specs=[
                        make_neighbor_spec(1, neighbor_id=f"n{index}") for index in range(3)
                    ],
                )
            ),
            1,
        )

    def test_life_b2_s23_rule_metadata_and_transitions(self) -> None:
        rule = LifeB2S23Rule()
        self.assert_rule_snapshot(rule)
        self.assertTrue(rule.supports_randomize)
        self.assertEqual(rule.name, "life-b2-s23")
        self.assertEqual(rule.display_name, "Life: B2/S23")
        self.assertEqual([state.value for state in rule.state_definitions()], [0, 1])
        self.assertEqual(rule.default_paint_state, 1)
        self.assertEqual(
            rule.next_state(
                build_context(
                    0,
                    neighbor_specs=[
                        make_neighbor_spec(1, neighbor_id="a"),
                        make_neighbor_spec(1, neighbor_id="b"),
                    ],
                )
            ),
            1,
        )
        self.assertEqual(
            rule.next_state(
                build_context(
                    1,
                    neighbor_specs=[
                        make_neighbor_spec(1, neighbor_id="a"),
                        make_neighbor_spec(1, neighbor_id="b"),
                    ],
                )
            ),
            1,
        )

    def test_extended_archlife_rules_have_expected_kind_thresholds(self) -> None:
        cases = [
            (
                ArchLife31212Rule(),
                [("triangle", 0, 2, 1), ("dodecagon", 0, 3, 1), ("dodecagon", 1, 1, 0)],
            ),
            (
                ArchLife3464Rule(),
                [("triangle", 0, 2, 1), ("square", 0, 2, 1), ("hexagon", 0, 3, 1)],
            ),
            (
                ArchLife4612Rule(),
                [("square", 0, 2, 1), ("hexagon", 0, 3, 1), ("dodecagon", 0, 4, 1)],
            ),
            (
                ArchLife33434Rule(),
                [("triangle", 0, 2, 1), ("square", 0, 3, 1), ("square", 1, 1, 0)],
            ),
            (
                ArchLife33344Rule(),
                [("triangle", 0, 2, 1), ("square", 0, 2, 1), ("square", 1, 3, 1)],
            ),
            (
                ArchLife33336Rule(),
                [("triangle", 0, 2, 1), ("hexagon", 0, 4, 1), ("hexagon", 1, 1, 0)],
            ),
        ]

        for rule, transitions in cases:
            with self.subTest(rule=rule.name):
                self.assert_rule_snapshot(rule)
                self.assertTrue(rule.supports_randomize)
                for kind, current_state, live_neighbors, expected in transitions:
                    neighbor_specs = [
                        make_neighbor_spec(1, neighbor_id=f"n{index}")
                        for index in range(live_neighbors)
                    ]
                    self.assertEqual(
                        rule.next_state(
                            build_context(current_state, kind=kind, neighbor_specs=neighbor_specs)
                        ),
                        expected,
                    )

    def test_penrose_greenberg_hastings_metadata_and_state_cycle(self) -> None:
        rule = PenroseGreenbergHastingsRule()
        self.assert_rule_snapshot(rule)
        self.assertEqual([state.value for state in rule.state_definitions()], [0, 1, 2, 3])
        self.assertEqual(rule.default_paint_state, 1)
        self.assertTrue(rule.supports_randomize)
        self.assertEqual(rule.next_state(build_context(1)), 2)
        self.assertEqual(rule.next_state(build_context(2)), 3)
        self.assertEqual(rule.next_state(build_context(3)), 0)
        self.assertEqual(
            rule.next_state(
                build_context(0, neighbor_specs=[make_neighbor_spec(1, neighbor_id="n0")])
            ),
            1,
        )

    def test_penrose_aliases_resolve_to_canonical_life_rules(self) -> None:
        self.assertIs(self.rule_registry.get("penrose-life"), self.rule_registry.get("life-b2-s23"))
        self.assertIs(
            self.rule_registry.get("penrose-vertex-life"), self.rule_registry.get("conway")
        )
        self.assertIs(self.rule_registry.get("hexwhirlpool"), self.rule_registry.get("whirlpool"))

    def test_directional_counts_only_real_excited_neighbors(self) -> None:
        rule = WhirlpoolRule()
        ctx = build_context(
            rule.RESTING,
            neighbor_specs=[
                make_neighbor_spec(
                    rule.EXCITED, neighbor_id="n0", radial="outward", clockwise_index=0
                ),
                make_neighbor_spec(
                    rule.SOURCE,
                    neighbor_id="n1",
                    radial="inward",
                    turn="clockwise",
                    radial_delta=-0.2,
                    angle_delta=-0.3,
                    clockwise_index=1,
                ),
            ],
        )

        counts = ctx.directional_counts(rule.EXCITED)
        self.assertEqual(counts["outward"], 1)
        self.assertEqual(counts["inward"], 0)
        self.assertEqual(counts["clockwise"], 0)
        self.assertEqual(counts["total"], 1)

    def test_select_neighbor_prefers_outward_clockwise(self) -> None:
        ctx = build_context(
            0,
            neighbor_specs=[
                make_neighbor_spec(
                    0, neighbor_id="fallback", radial="level", turn="aligned", clockwise_index=1
                ),
                make_neighbor_spec(
                    0,
                    neighbor_id="best",
                    radial="outward",
                    turn="clockwise",
                    radial_delta=0.5,
                    angle_delta=-0.2,
                    clockwise_index=2,
                ),
            ],
        )

        self.assertEqual(
            ctx.select_neighbor_id(
                0,
                tiers=(
                    ("outward", "clockwise"),
                    ("outward", None),
                    (None, "clockwise"),
                    (None, None),
                ),
            ),
            "best",
        )

    def test_whirlpool_eye_cells_reignite_when_supported(self) -> None:
        rule = WhirlpoolRule()
        specs = [
            make_neighbor_spec(rule.EXCITED, neighbor_id="n0", radial="outward", clockwise_index=0)
        ]
        resting_ctx = build_context(
            rule.RESTING, neighbor_specs=specs, shell_rank=0, radial_ratio=0.05
        )
        refractory_ctx = build_context(
            rule.REFRACTORY, neighbor_specs=specs, shell_rank=0, radial_ratio=0.05
        )

        self.assertEqual(rule.next_state(resting_ctx), rule.EXCITED)
        self.assertEqual(rule.next_state(refractory_ctx), rule.EXCITED)

    def test_whirlpool_source_emits_clockwise_outward_pulse(self) -> None:
        rule = WhirlpoolRule()
        target_ctx = build_source_context(rule)

        self.assertEqual(rule.source_emission_target_id(target_ctx, "source"), "target")
        self.assertTrue(rule.has_incoming_source_pulse(target_ctx))
        self.assertEqual(rule.next_state(target_ctx), rule.EXCITED)

    def test_whirlpool_source_does_not_overwrite_non_resting_target(self) -> None:
        rule = WhirlpoolRule()
        target_ctx = build_source_context(rule, target_state=rule.TRAILING)

        self.assertFalse(rule.has_incoming_source_pulse(target_ctx))
        self.assertEqual(rule.next_state(target_ctx), rule.REFRACTORY)

    def test_whirlpool_shear_zone_requires_clockwise_bias(self) -> None:
        rule = WhirlpoolRule()
        blocked_ctx = build_context(
            rule.RESTING,
            radial_ratio=0.42,
            neighbor_specs=[
                make_neighbor_spec(
                    rule.EXCITED,
                    neighbor_id="in-cw",
                    radial="inward",
                    turn="clockwise",
                    clockwise_index=0,
                ),
                make_neighbor_spec(
                    rule.EXCITED,
                    neighbor_id="level-ccw",
                    radial="level",
                    turn="counterclockwise",
                    clockwise_index=1,
                ),
            ],
        )
        allowed_ctx = build_context(
            rule.RESTING,
            radial_ratio=0.42,
            neighbor_specs=[
                make_neighbor_spec(
                    rule.EXCITED,
                    neighbor_id="in-cw",
                    radial="inward",
                    turn="clockwise",
                    clockwise_index=0,
                ),
                make_neighbor_spec(
                    rule.EXCITED,
                    neighbor_id="in-align",
                    radial="inward",
                    turn="aligned",
                    clockwise_index=1,
                ),
            ],
        )

        self.assertEqual(rule.next_state(blocked_ctx), rule.RESTING)
        self.assertEqual(rule.next_state(allowed_ctx), rule.EXCITED)

    def test_whirlpool_outer_zone_requires_positive_clockwise_margin(self) -> None:
        rule = WhirlpoolRule()
        blocked_ctx = build_context(
            rule.RESTING,
            radial_ratio=0.72,
            neighbor_specs=[
                make_neighbor_spec(
                    rule.EXCITED,
                    neighbor_id="in-cw",
                    radial="inward",
                    turn="clockwise",
                    clockwise_index=0,
                ),
                make_neighbor_spec(
                    rule.EXCITED,
                    neighbor_id="in-ccw",
                    radial="inward",
                    turn="counterclockwise",
                    clockwise_index=1,
                ),
                make_neighbor_spec(
                    rule.EXCITED,
                    neighbor_id="in-align",
                    radial="inward",
                    turn="aligned",
                    clockwise_index=2,
                ),
            ],
        )
        allowed_ctx = build_context(
            rule.RESTING,
            radial_ratio=0.72,
            neighbor_specs=[
                make_neighbor_spec(
                    rule.EXCITED,
                    neighbor_id="in-cw-0",
                    radial="inward",
                    turn="clockwise",
                    clockwise_index=0,
                ),
                make_neighbor_spec(
                    rule.EXCITED,
                    neighbor_id="in-cw-1",
                    radial="inward",
                    turn="clockwise",
                    clockwise_index=1,
                ),
                make_neighbor_spec(
                    rule.EXCITED,
                    neighbor_id="in-align",
                    radial="inward",
                    turn="aligned",
                    clockwise_index=2,
                ),
            ],
        )

        self.assertEqual(rule.next_state(blocked_ctx), rule.RESTING)
        self.assertEqual(rule.next_state(allowed_ctx), rule.EXCITED)


if __name__ == "__main__":
    unittest.main()
