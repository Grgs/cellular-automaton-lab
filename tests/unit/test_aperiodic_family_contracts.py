from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.bootstrap_data import build_bootstrap_payload, describe_aperiodic_families
from backend.simulation.aperiodic_family_manifest import APERIODIC_FAMILY_IDS, APERIODIC_FAMILY_MANIFEST
from backend.simulation.literature_reference_specs import REFERENCE_FAMILY_SPECS
from backend.simulation.topology_catalog import PENROSE_VERTEX_GEOMETRY, TOPOLOGY_VARIANTS


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

    def test_bootstrap_aperiodic_families_match_manifest(self) -> None:
        expected = [
            {
                "tiling_family": geometry,
                "label": APERIODIC_FAMILY_MANIFEST[geometry].catalog_label,
                "experimental": APERIODIC_FAMILY_MANIFEST[geometry].experimental,
                "public_cell_kinds": list(APERIODIC_FAMILY_MANIFEST[geometry].public_cell_kinds),
            }
            for geometry in APERIODIC_FAMILY_IDS
        ]

        self.assertEqual(describe_aperiodic_families(), expected)
        self.assertEqual(
            build_bootstrap_payload({"app_name": "cellular-automaton-lab"})["aperiodic_families"],
            expected,
        )

    def test_old_square_triangle_id_is_absent(self) -> None:
        self.assertNotIn("square-triangle", APERIODIC_FAMILY_MANIFEST)
        self.assertNotIn(
            "square-triangle",
            {
                entry["tiling_family"]
                for entry in build_bootstrap_payload({"app_name": "cellular-automaton-lab"})["aperiodic_families"]
            },
        )


if __name__ == "__main__":
    unittest.main()
