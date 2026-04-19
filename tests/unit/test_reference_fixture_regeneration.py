import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.regenerate_reference_fixtures import (
    CanonicalFixtureTarget,
    FixtureRegenerationError,
    LocalFixtureTarget,
    _canonical_drift_lines,
    check_fixture_drift,
    discover_canonical_fixture_targets,
    discover_local_fixture_targets,
    regenerate_canonical_fixtures,
    regenerate_local_fixtures,
    _read_canonical_fixtures,
    _read_local_fixtures,
)


class ReferenceFixtureRegenerationTests(unittest.TestCase):
    def test_existing_local_fixture_targets_regenerate_to_checked_in_payloads(self) -> None:
        fixtures = _read_local_fixtures()
        targets = discover_local_fixture_targets(fixtures)

        regenerated = regenerate_local_fixtures(fixtures, targets)

        self.assertEqual(regenerated, fixtures)

    def test_existing_canonical_fixture_targets_regenerate_to_checked_in_payloads(self) -> None:
        fixtures = _read_canonical_fixtures()
        targets = discover_canonical_fixture_targets(fixtures)

        regenerated = regenerate_canonical_fixtures(fixtures, targets)

        self.assertEqual(regenerated, fixtures)

    def test_check_reports_success_when_checked_in_fixtures_match(self) -> None:
        self.assertEqual(
            check_fixture_drift(
                mode="both",
                all_targets=True,
                geometry=None,
                depth=None,
            ),
            [],
        )

    def test_check_style_comparison_reports_mutated_canonical_payload(self) -> None:
        fixtures = _read_canonical_fixtures()
        targets = discover_canonical_fixture_targets(
            fixtures,
            geometry="shield",
            depth=3,
        )
        regenerated = regenerate_canonical_fixtures(fixtures, targets)
        mutated = copy.deepcopy(regenerated)
        mutated["shield"]["dense-depth-3"]["cells"][0]["kind"] = "not-a-shield"

        self.assertEqual(
            _canonical_drift_lines(regenerated, mutated, targets),
            ["canonical shield depth 3 fixture dense-depth-3"],
        )

    def test_canonical_target_discovery_uses_spec_owned_include_id_for_missing_fixture(self) -> None:
        fixtures = _read_canonical_fixtures()
        mutated = copy.deepcopy(fixtures)
        mutated["pinwheel"].pop("exact-depth-1", None)

        self.assertEqual(
            discover_canonical_fixture_targets(
                mutated,
                geometry="pinwheel",
                depth=1,
            ),
            (
                CanonicalFixtureTarget(
                    geometry="pinwheel",
                    depth=1,
                    fixture_key="exact-depth-1",
                    include_id=True,
                ),
            ),
        )

    def test_missing_local_anchor_fails_clearly(self) -> None:
        fixtures = _read_local_fixtures()

        with self.assertRaisesRegex(FixtureRegenerationError, "Missing local fixture anchor"):
            regenerate_local_fixtures(
                fixtures,
                (
                    LocalFixtureTarget(
                        geometry="chair",
                        depth=3,
                        anchor_ids=("not-a-chair-cell",),
                    ),
                ),
            )


if __name__ == "__main__":
    unittest.main()
