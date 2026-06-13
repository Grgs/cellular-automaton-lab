import tempfile
import unittest
from pathlib import Path

from backend.rules import RuleRegistry
from backend.simulation.sessions import (
    SimulationSessionError,
    SimulationSessionRegistry,
    validate_session_id,
)


class SimulationSessionRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.instance_path = Path(self._tmp.name)
        self.registry = SimulationSessionRegistry(
            rule_registry=RuleRegistry(),
            instance_path=self.instance_path,
            max_sessions=2,
        )
        self.addCleanup(self.registry.shutdown)

    def test_distinct_session_ids_get_isolated_coordinators(self) -> None:
        first = self.registry.get("alpha")
        second = self.registry.get("beta")
        self.assertIsNot(first, second)

    def test_same_session_id_reuses_the_coordinator(self) -> None:
        first = self.registry.get("alpha")
        self.assertIs(self.registry.get("alpha"), first)

    def test_registry_evicts_least_recently_used_over_cap(self) -> None:
        alpha = self.registry.get("alpha")
        self.registry.get("beta")
        # Third distinct session exceeds the cap of 2 and evicts the LRU (alpha).
        self.registry.get("gamma")
        self.assertIsNot(self.registry.get("alpha"), alpha)

    def test_access_refreshes_recency_so_touched_sessions_survive(self) -> None:
        alpha = self.registry.get("alpha")
        beta = self.registry.get("beta")
        # Touching alpha makes beta the least-recently-used entry.
        self.registry.get("alpha")
        self.registry.get("gamma")
        self.assertIs(self.registry.get("alpha"), alpha)
        self.assertIsNot(self.registry.get("beta"), beta)

    def test_eviction_flushes_session_state_to_disk(self) -> None:
        self.registry.get("alpha")
        # Push alpha out of the cache; eviction shuts it down and flushes state.
        self.registry.get("beta")
        self.registry.get("gamma")
        self.assertTrue((self.instance_path / "sessions" / "alpha.json").exists())

    def test_malformed_session_id_is_rejected(self) -> None:
        with self.assertRaises(SimulationSessionError):
            self.registry.get("not a valid id!")

    def test_max_sessions_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            SimulationSessionRegistry(
                rule_registry=RuleRegistry(),
                instance_path=self.instance_path,
                max_sessions=0,
            )

    def test_validate_session_id_returns_the_id_when_valid(self) -> None:
        self.assertEqual(validate_session_id("s-123_ABC"), "s-123_ABC")


if __name__ == "__main__":
    unittest.main()
