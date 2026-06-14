import unittest

from backend.rules import RuleRegistry
from backend.rules.base import RuleTopologyCompatibilityError
from backend.simulation.service_boards import build_initial_state
from backend.simulation.topology_catalog import (
    GEOMETRY_DEFAULT_RULES,
    get_topology_variant_for_geometry,
)
from backend.simulation.transition_planner import (
    plan_config_transition,
    plan_reset_transition,
    plan_restore_transition,
)

UNIVERSAL_RULE = "conway"
KIND_RULE = "kagome-life"
KIND_RULE_FAMILY = "trihexagonal-3-6-3-6"


class RuleTopologyCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = RuleRegistry()

    def test_universal_rule_supports_any_family(self) -> None:
        rule = self.registry.get(UNIVERSAL_RULE)
        self.assertTrue(rule.supports_all_topologies)
        self.assertIsNone(rule.compatible_tiling_families)
        self.assertTrue(rule.supports_tiling_family("square"))
        self.assertTrue(rule.supports_tiling_family("spectre"))

    def test_kind_rule_only_supports_declared_families(self) -> None:
        rule = self.registry.get(KIND_RULE)
        self.assertFalse(rule.supports_all_topologies)
        self.assertTrue(rule.supports_tiling_family(KIND_RULE_FAMILY))
        self.assertFalse(rule.supports_tiling_family("square"))

    def test_every_geometry_default_rule_supports_its_own_family(self) -> None:
        # Drift guard: a geometry's default rule must always be allowed on that
        # geometry. If a new geometry defaults to a restricted rule, this fails
        # until the rule declares the geometry's family.
        for geometry, rule_name in GEOMETRY_DEFAULT_RULES.items():
            with self.subTest(geometry=geometry):
                rule = self.registry.get(rule_name)
                tiling_family = get_topology_variant_for_geometry(geometry).tiling_family
                self.assertTrue(
                    rule.supports_tiling_family(tiling_family),
                    f"default rule '{rule_name}' rejects its own family '{tiling_family}'",
                )

    def test_reset_transition_rejects_incompatible_rule(self) -> None:
        state = build_initial_state(self.registry)
        with self.assertRaises(RuleTopologyCompatibilityError):
            plan_reset_transition(
                state,
                self.registry,
                topology_spec={"tiling_family": "square"},
                rule_name=KIND_RULE,
            )

    def test_config_transition_rejects_incompatible_rule(self) -> None:
        state = build_initial_state(self.registry)  # default square topology
        with self.assertRaises(RuleTopologyCompatibilityError):
            plan_config_transition(state, self.registry, rule_name=KIND_RULE)

    def test_compatible_rule_passes_transition(self) -> None:
        state = build_initial_state(self.registry)
        plan = plan_reset_transition(
            state,
            self.registry,
            topology_spec={"tiling_family": KIND_RULE_FAMILY},
            rule_name=KIND_RULE,
        )
        self.assertEqual(plan.rule.name, KIND_RULE)

    def test_restore_transition_tolerates_incompatible_pairing(self) -> None:
        # Restore must stay lenient so older persisted snapshots still load,
        # even if the saved rule/topology pairing is no longer offered.
        state = build_initial_state(self.registry)
        plan = plan_restore_transition(
            {"topology_spec": {"tiling_family": "square"}, "rule": KIND_RULE},
            fallback_state=state,
            rule_registry=self.registry,
        )
        self.assertEqual(plan.rule.name, KIND_RULE)


if __name__ == "__main__":
    unittest.main()
