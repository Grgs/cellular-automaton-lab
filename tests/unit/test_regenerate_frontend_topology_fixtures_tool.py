from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backend.simulation.topology_types import (
    CONTENT_REVISION_HASH_LENGTH,
)
from backend.simulation.topology_types import (
    topology_content_revision as compute_content_revision,
)
from tools.regenerate_frontend_topology_fixtures import (
    DEFAULT_FIXTURE_MANIFEST_PATH,
    discover_fixture_targets,
    fixture_drift_lines,
    load_fixture_targets,
    main,
    regenerate_fixture_payload,
    write_regenerated_fixtures,
)


class FrontendTopologyFixtureRegenerationToolTests(unittest.TestCase):
    def test_load_fixture_targets_reads_checked_in_manifest(self) -> None:
        targets = load_fixture_targets()

        self.assertEqual(DEFAULT_FIXTURE_MANIFEST_PATH.name, "fixture-manifest.json")
        self.assertEqual(targets[0].name, "archimedean-4-8-8-3x3")
        self.assertEqual(targets[-1].name, "turtle-monotile-depth-3")
        self.assertEqual(len(targets), 14)

    def test_discover_fixture_targets_rejects_missing_selection(self) -> None:
        with self.assertRaises(ValueError):
            discover_fixture_targets(
                manifest_path=DEFAULT_FIXTURE_MANIFEST_PATH,
                all_targets=False,
                names=(),
            )

    def test_regenerate_fixture_payload_matches_existing_checked_in_fixture(self) -> None:
        shield_target = next(
            target for target in load_fixture_targets() if target.name == "shield-depth-3"
        )
        regenerated = regenerate_fixture_payload(shield_target)
        current = json.loads(shield_target.path.read_text(encoding="utf-8"))

        self.assertEqual(regenerated, current)

    def test_fixture_drift_and_write_work_against_temp_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="frontend-fixture-regeneration-") as tmpdir:
            tmpdir_path = Path(tmpdir)
            fixture_path = tmpdir_path / "pinwheel-depth-3.json"
            fixture_path.write_text(
                json.dumps(
                    {
                        "geometry": "pinwheel",
                        "width": 0,
                        "height": 0,
                        "patchDepth": 3,
                        "cellSize": 12,
                        "topology": {
                            "topology_spec": {
                                "tiling_family": "pinwheel",
                                "adjacency_mode": "edge",
                                "sizing_mode": "patch_depth",
                                "width": 0,
                                "height": 0,
                                "patch_depth": 3,
                            },
                            "topology_revision": "stale",
                            "cells": [],
                        },
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            manifest_path = tmpdir_path / "fixture-manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "fixtures": [
                            {
                                "name": "pinwheel-depth-3",
                                "path": "pinwheel-depth-3.json",
                                "family": "pinwheel",
                                "width": 0,
                                "height": 0,
                                "patchDepth": 3,
                                "cellSize": 12,
                            }
                        ]
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            targets = discover_fixture_targets(
                manifest_path=manifest_path,
                all_targets=True,
                names=(),
            )

            self.assertEqual(fixture_drift_lines(targets), ["pinwheel-depth-3"])
            write_regenerated_fixtures(targets)
            self.assertEqual(fixture_drift_lines(targets), [])

    def test_compute_content_revision_is_stable_and_ignores_existing_revision(self) -> None:
        base_payload = {
            "topology_spec": {"tiling_family": "demo"},
            "cells": [{"id": "c:0:0", "kind": "cell", "neighbors": []}],
            "topology_revision": "anything",
        }
        first_hash = compute_content_revision(base_payload)
        # Same content with a different placeholder revision must hash identically.
        second_payload = dict(base_payload, topology_revision="different")
        self.assertEqual(first_hash, compute_content_revision(second_payload))
        self.assertEqual(len(first_hash), CONTENT_REVISION_HASH_LENGTH)
        # Changing actual content must change the hash.
        mutated_payload = dict(
            base_payload,
            cells=[{"id": "c:0:0", "kind": "cell", "neighbors": ["c:1:0"]}],
        )
        self.assertNotEqual(first_hash, compute_content_revision(mutated_payload))

    def test_compute_content_revision_normalizes_negative_zero(self) -> None:
        # Some backend builders (e.g. taylor-socolar) produce ``-0.0`` for
        # some center / vertex coordinates on one platform and ``0.0`` on
        # another (libm differences in trig identities like sin(pi)).
        # Python treats ``-0.0 == 0.0`` so the dict-equality drift check
        # is happy; the content hash must match too or the checked-in
        # revision becomes platform-dependent. This test locks in the
        # normalization that keeps hashes stable across platforms.
        positive_zero_payload = {
            "topology_spec": {"tiling_family": "demo"},
            "cells": [
                {
                    "id": "c:0:0",
                    "kind": "cell",
                    "neighbors": [],
                    "center": {"x": 0.0, "y": 1.5},
                    "vertices": [{"x": 0.0, "y": 0.0}],
                }
            ],
        }
        negative_zero_payload = {
            "topology_spec": {"tiling_family": "demo"},
            "cells": [
                {
                    "id": "c:0:0",
                    "kind": "cell",
                    "neighbors": [],
                    "center": {"x": -0.0, "y": 1.5},
                    "vertices": [{"x": -0.0, "y": 0.0}],
                }
            ],
        }
        self.assertEqual(
            compute_content_revision(positive_zero_payload),
            compute_content_revision(negative_zero_payload),
        )

    def test_regenerated_payload_revision_matches_computed_content_hash(self) -> None:
        shield_target = next(
            target for target in load_fixture_targets() if target.name == "shield-depth-3"
        )
        regenerated = regenerate_fixture_payload(shield_target)
        topology = regenerated["topology"]
        embedded_revision = topology["topology_revision"]
        self.assertEqual(embedded_revision, compute_content_revision(topology))

    def test_main_check_all_passes_for_checked_in_manifest(self) -> None:
        self.assertEqual(main(["--all", "--check"]), 0)


if __name__ == "__main__":
    unittest.main()
