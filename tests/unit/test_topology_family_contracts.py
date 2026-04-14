from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.topology_family_manifest import TOPOLOGY_FAMILY_MANIFEST
from backend.topology_family_contracts import (
    FRONTEND_TOPOLOGY_FAMILY_METADATA_PATH,
    topology_frontend_family_contracts,
)


_FRONTEND_ENTRY_PATTERN = re.compile(
    r'"(?P<tiling_family>[^"]+)": \{\s*'
    r'label: "(?P<label>[^"]+)",\s*'
    r'pickerGroup: "(?P<picker_group>[^"]+)",\s*'
    r'pickerOrder: (?P<picker_order>\d+),\s*'
    r'family: "(?P<family>[^"]+)",\s*'
    r'sizingMode: "(?P<sizing_mode>[^"]+)",\s*'
    r'viewportSyncMode: "(?P<viewport_sync_mode>[^"]+)",\s*'
    r"\}",
    re.MULTILINE,
)


def _load_frontend_topology_family_metadata() -> dict[str, dict[str, object]]:
    text = (ROOT / FRONTEND_TOPOLOGY_FAMILY_METADATA_PATH).read_text(encoding="utf-8")
    parsed: dict[str, dict[str, object]] = {}
    for match in _FRONTEND_ENTRY_PATTERN.finditer(text):
        parsed[match.group("tiling_family")] = {
            "label": match.group("label"),
            "picker_group": match.group("picker_group"),
            "picker_order": int(match.group("picker_order")),
            "family": match.group("family"),
            "sizing_mode": match.group("sizing_mode"),
            "viewport_sync_mode": match.group("viewport_sync_mode"),
        }
    return parsed


class TopologyFamilyContractTests(unittest.TestCase):
    def test_frontend_metadata_covers_every_backend_catalog_family(self) -> None:
        frontend_metadata = _load_frontend_topology_family_metadata()
        self.assertEqual(set(frontend_metadata), set(TOPOLOGY_FAMILY_MANIFEST))

    def test_frontend_metadata_matches_backend_owned_contract(self) -> None:
        frontend_metadata = _load_frontend_topology_family_metadata()

        for contract in topology_frontend_family_contracts():
            with self.subTest(tiling_family=contract.tiling_family):
                self.assertEqual(
                    frontend_metadata[contract.tiling_family],
                    {
                        "label": contract.label,
                        "picker_group": contract.picker_group,
                        "picker_order": contract.picker_order,
                        "family": contract.family,
                        "sizing_mode": contract.sizing_mode,
                        "viewport_sync_mode": contract.viewport_sync_mode,
                    },
                )

    def test_old_square_triangle_id_is_absent(self) -> None:
        frontend_metadata = _load_frontend_topology_family_metadata()
        self.assertNotIn("square-triangle", TOPOLOGY_FAMILY_MANIFEST)
        self.assertNotIn("square-triangle", frontend_metadata)


if __name__ == "__main__":
    unittest.main()
