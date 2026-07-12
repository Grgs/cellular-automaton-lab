from __future__ import annotations

import json
import math
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.aperiodic_family_manifest import (
    SOCOLAR_HEXAGONAL_HEXAGON_KIND,
    SOCOLAR_HEXAGONAL_RHOMB_KIND,
    SOCOLAR_HEXAGONAL_SQUARE_KIND,
)
from backend.simulation.aperiodic_socolar_hexagonal import (
    _CLASSES,
    _class_tiles,
    _module_xy,
    _reduced_base,
    build_socolar_hexagonal_patch,
)

_SAMPLE_PATH = ROOT / "backend" / "simulation" / "data" / "socolar_hexagonal_literature_sample.json"

# Deterministic cut-and-project ball cell counts at radius 4 + 0.75*d.
_EXPECTED_CELL_COUNTS = {0: 41, 1: 58, 2: 81, 3: 108}

_KIND_EDGE_COUNT = {
    SOCOLAR_HEXAGONAL_HEXAGON_KIND: 6,
    SOCOLAR_HEXAGONAL_SQUARE_KIND: 4,
    SOCOLAR_HEXAGONAL_RHOMB_KIND: 4,
}


def _exact_generated_tiles(radius_units: float) -> dict[tuple[tuple[int, int, int, int], ...], str]:
    """Exact x2-module tile map (sorted verts -> internal kind) at radius."""
    out: dict[tuple[tuple[int, int, int, int], ...], str] = {}
    for spec in _CLASSES:
        if "reduced_base" not in spec:
            spec["reduced_base"] = _reduced_base(spec)
        for _center, verts in _class_tiles(spec, radius_units):
            out[tuple(sorted(verts))] = spec["kind"]
    return out


class SocolarHexagonalLiteratureTests(unittest.TestCase):
    """Tile-for-tile comparison against the vendored Tilings Encyclopedia
    sample (independent of this generator: extracted from the encyclopedia's
    published patch image, exact-snapped to the module)."""

    def test_reproduces_literature_sample_tile_for_tile(self) -> None:
        sample = json.loads(_SAMPLE_PATH.read_text())
        sample_tiles = {
            tuple(sorted(tuple(v) for v in tile["verts"])): tile["kind"] for tile in sample["tiles"]
        }
        # The sample holds every literature tile whose vertices lie within 12
        # tile-edge units of the origin; generate a strictly larger ball.
        generated = _exact_generated_tiles(14.0)

        missing = [key for key in sample_tiles if key not in generated]
        self.assertEqual(missing, [], f"{len(missing)} literature tiles absent from generator")
        for key, kind in sample_tiles.items():
            self.assertEqual(generated[key], kind, f"kind mismatch at {key[0]}")

        # Conversely: every generated tile fully inside the sample's coverage
        # region must be a literature tile (no spurious tiles).
        extras = [
            key
            for key in generated
            if key not in sample_tiles and all(math.hypot(*_module_xy(v)) <= 24.0 for v in key)
        ]
        self.assertEqual(extras, [], f"{len(extras)} generated tiles not in literature sample")


class SocolarHexagonalStructureTests(unittest.TestCase):
    def test_cell_counts_and_kind_census(self) -> None:
        expected_kinds = {
            0: {
                SOCOLAR_HEXAGONAL_HEXAGON_KIND: 10,
                SOCOLAR_HEXAGONAL_RHOMB_KIND: 15,
                SOCOLAR_HEXAGONAL_SQUARE_KIND: 16,
            },
            1: {
                SOCOLAR_HEXAGONAL_HEXAGON_KIND: 16,
                SOCOLAR_HEXAGONAL_RHOMB_KIND: 22,
                SOCOLAR_HEXAGONAL_SQUARE_KIND: 20,
            },
        }
        for depth, expected in _EXPECTED_CELL_COUNTS.items():
            patch = build_socolar_hexagonal_patch(depth)
            self.assertEqual(len(patch.cells), expected, f"depth {depth}")
            if depth in expected_kinds:
                census = Counter(cell.kind for cell in patch.cells)
                self.assertEqual(dict(census), expected_kinds[depth], f"depth {depth}")

    def test_unit_edges_and_kind_shapes(self) -> None:
        patch = build_socolar_hexagonal_patch(2)
        for cell in patch.cells:
            self.assertEqual(len(cell.vertices), _KIND_EDGE_COUNT[cell.kind], cell.id)
            count = len(cell.vertices)
            for i in range(count):
                ax, ay = cell.vertices[i]
                bx, by = cell.vertices[(i + 1) % count]
                self.assertAlmostEqual(math.hypot(bx - ax, by - ay), 1.0, delta=5e-6, msg=cell.id)

    def test_matching_rules_forbid_same_kind_contacts(self) -> None:
        # Socolar matching rules: rhomb-rhomb, square-square, and
        # hexagon-hexagon edge contacts never occur.
        patch = build_socolar_hexagonal_patch(4)
        by_id = {cell.id: cell for cell in patch.cells}
        for cell in patch.cells:
            for neighbor_id in cell.neighbors:
                self.assertNotEqual(
                    cell.kind, by_id[neighbor_id].kind, f"{cell.id} ~ {neighbor_id}"
                )

    def test_shallow_patch_ids_are_subset_of_deeper(self) -> None:
        shallow = {cell.id for cell in build_socolar_hexagonal_patch(1).cells}
        deep = {cell.id for cell in build_socolar_hexagonal_patch(4).cells}
        self.assertTrue(shallow.issubset(deep))

    def test_kind_frequencies_approach_perron_ratios(self) -> None:
        # Rhomb and square frequencies both converge to sqrt(3) x the hexagon
        # frequency in the infinite tiling.
        patch = build_socolar_hexagonal_patch(16)
        census = Counter(cell.kind for cell in patch.cells)
        hexagons = census[SOCOLAR_HEXAGONAL_HEXAGON_KIND]
        self.assertGreater(hexagons, 100)
        for kind in (SOCOLAR_HEXAGONAL_RHOMB_KIND, SOCOLAR_HEXAGONAL_SQUARE_KIND):
            ratio = census[kind] / hexagons
            self.assertAlmostEqual(ratio, math.sqrt(3.0), delta=0.25, msg=kind)


if __name__ == "__main__":
    unittest.main()
