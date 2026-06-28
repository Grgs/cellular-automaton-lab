from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.aperiodic_chair import (
    _DEFAULT_ROOT_SEEDS,
    _UNIT_CHAIR_POLYGONS,
    _collect_canonical_chair_records,
    build_chair_patch,
    collect_chair_records,
)

Point = tuple[float, float]


def _point_in_polygon(point: Point, polygon: list[Point]) -> bool:
    x, y = point
    inside = False
    count = len(polygon)
    previous = count - 1
    for index in range(count):
        xi, yi = polygon[index]
        xj, yj = polygon[previous]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        previous = index
    return inside


def _covered_unit_cells(polygon: list[Point]) -> set[tuple[int, int]]:
    min_x = int(min(x for x, _ in polygon))
    max_x = int(max(x for x, _ in polygon))
    min_y = int(min(y for _, y in polygon))
    max_y = int(max(y for _, y in polygon))
    covered: set[tuple[int, int]] = set()
    for x in range(min_x, max_x):
        for y in range(min_y, max_y):
            if _point_in_polygon((x + 0.5, y + 0.5), polygon):
                covered.add((x, y))
    return covered


class ChairRecordTests(unittest.TestCase):
    def test_canonical_record_counts_grow_as_four_to_the_depth(self) -> None:
        for depth in range(5):
            with self.subTest(depth=depth):
                self.assertEqual(len(_collect_canonical_chair_records(depth)), 4**depth)

    def test_default_record_counts_use_wide_two_tile_seed(self) -> None:
        for depth in range(5):
            with self.subTest(depth=depth):
                self.assertEqual(len(collect_chair_records(depth)), 2 * 4**depth)

    def test_default_depth_zero_is_wide_rectangular_seed(self) -> None:
        records = collect_chair_records(0)
        self.assertEqual(len(records), len(_DEFAULT_ROOT_SEEDS))
        self.assertEqual({record["orientation_token"] for record in records}, {"0", "2"})
        covered_once: set[tuple[int, int]] = set()
        for record in records:
            cells = _covered_unit_cells([(x, y) for x, y in record["vertices"]])
            self.assertTrue(covered_once.isdisjoint(cells))
            covered_once.update(cells)
        self.assertEqual(covered_once, {(x, y) for x in range(3) for y in range(2)})

    def test_unit_chair_orientations_have_three_unit_cells(self) -> None:
        for orientation, vertices in _UNIT_CHAIR_POLYGONS.items():
            with self.subTest(orientation=orientation):
                cells = _covered_unit_cells([(vertex.x, vertex.y) for vertex in vertices])
                self.assertEqual(len(cells), 3)


class ChairPatchTests(unittest.TestCase):
    def test_patch_uses_wide_rectangular_extent(self) -> None:
        for depth in range(4):
            with self.subTest(depth=depth):
                patch = build_chair_patch(depth)
                self.assertEqual(len(patch.cells), 2 * 4**depth)
                self.assertEqual(patch.width, 3)
                self.assertEqual(patch.height, 2)


if __name__ == "__main__":
    unittest.main()
