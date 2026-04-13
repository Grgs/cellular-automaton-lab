from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.aperiodic_family_contracts import (
    FRONTEND_APERIODIC_METADATA_PATH,
    aperiodic_frontend_family_contracts,
)
from backend.simulation.aperiodic_family_manifest import APERIODIC_FAMILY_IDS, APERIODIC_FAMILY_MANIFEST
from backend.simulation.literature_reference_specs import REFERENCE_FAMILY_SPECS
from backend.simulation.topology_catalog import PENROSE_VERTEX_GEOMETRY, TOPOLOGY_VARIANTS


_FRONTEND_ENTRY_PATTERN = re.compile(
    r'"(?P<geometry>[^"]+)": \{\s*'
    r'label: "(?P<label>[^"]+)",\s*'
    r'experimental: (?P<experimental>true|false),\s*'
    r'publicCellKinds: \[(?P<kinds>[^\]]*)\],\s*'
    r"\}",
    re.MULTILINE,
)
_TOPOLOGY_METADATA_IMPORT = 'from "./aperiodic-family-metadata.js";'


def _load_frontend_aperiodic_metadata() -> dict[str, dict[str, object]]:
    text = (ROOT / FRONTEND_APERIODIC_METADATA_PATH).read_text(encoding="utf-8")
    parsed: dict[str, dict[str, object]] = {}
    for match in _FRONTEND_ENTRY_PATTERN.finditer(text):
        kinds = tuple(
            kind.strip().strip('"')
            for kind in match.group("kinds").split(",")
            if kind.strip()
        )
        parsed[match.group("geometry")] = {
            "label": match.group("label"),
            "experimental": match.group("experimental") == "true",
            "publicCellKinds": kinds,
        }
    return parsed


class AperiodicFamilyContractTests(unittest.TestCase):
    def test_every_aperiodic_family_has_exactly_one_manifest_entry(self) -> None:
        self.assertEqual(set(APERIODIC_FAMILY_MANIFEST), set(APERIODIC_FAMILY_IDS))
        self.assertEqual(len(APERIODIC_FAMILY_IDS), len(set(APERIODIC_FAMILY_IDS)))

    def test_public_cell_kind_names_are_unique_across_aperiodic_families(self) -> None:
        public_kinds = [
            kind
            for geometry in APERIODIC_FAMILY_IDS
            for kind in APERIODIC_FAMILY_MANIFEST[geometry].public_cell_kinds
        ]
        self.assertEqual(len(public_kinds), len(set(public_kinds)))

    def test_manifest_aligns_with_catalog_contracts_and_reference_specs(self) -> None:
        catalog_families = {
            variant.tiling_family
            for variant in TOPOLOGY_VARIANTS
            if variant.family == "aperiodic" and variant.geometry_key != PENROSE_VERTEX_GEOMETRY
        }
        reference_families = {
            geometry
            for geometry in REFERENCE_FAMILY_SPECS
            if geometry in APERIODIC_FAMILY_IDS
        }

        self.assertEqual(catalog_families, set(APERIODIC_FAMILY_IDS))
        self.assertEqual(reference_families, set(APERIODIC_FAMILY_IDS))

    def test_frontend_metadata_matches_backend_owned_contract(self) -> None:
        frontend_metadata = _load_frontend_aperiodic_metadata()

        self.assertEqual(set(frontend_metadata), set(APERIODIC_FAMILY_IDS))
        for contract in aperiodic_frontend_family_contracts():
            with self.subTest(geometry=contract.geometry):
                self.assertEqual(
                    frontend_metadata[contract.geometry],
                    {
                        "label": contract.label,
                        "experimental": contract.experimental,
                        "publicCellKinds": contract.public_cell_kinds,
                    },
                )

    def test_topology_module_reexports_frontend_aperiodic_metadata_owner(self) -> None:
        topology_text = (ROOT / "frontend/topology.ts").read_text(encoding="utf-8")
        self.assertIn(_TOPOLOGY_METADATA_IMPORT, topology_text)

    def test_old_square_triangle_id_is_absent(self) -> None:
        frontend_metadata = _load_frontend_aperiodic_metadata()
        self.assertNotIn("square-triangle", APERIODIC_FAMILY_MANIFEST)
        self.assertNotIn("square-triangle", frontend_metadata)


if __name__ == "__main__":
    unittest.main()
