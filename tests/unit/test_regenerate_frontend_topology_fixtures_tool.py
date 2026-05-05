from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

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
        self.assertEqual(targets[-1].name, "tuebingen-triangle-depth-3")
        self.assertEqual(len(targets), 11)

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
                                "topologyRevision": "fixture-pinwheel-depth-3",
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

    def test_main_check_all_passes_for_checked_in_manifest(self) -> None:
        self.assertEqual(main(["--all", "--check"]), 0)


if __name__ == "__main__":
    unittest.main()
