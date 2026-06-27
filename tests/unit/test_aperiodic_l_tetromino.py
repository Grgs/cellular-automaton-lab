from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.aperiodic_l_tetromino import (
    _BASE_POLYGON,
    _CANONICAL_CHILDREN,
    _DEFAULT_ROOT_SEEDS,
    _ORIENTATION_TOKEN,
    _collect_canonical_l_tetromino_records,
    _matrix_apply,
    build_l_tetromino_patch,
    collect_l_tetromino_records,
)

Point = tuple[float, float]


def _polygon_area(polygon: list[Point]) -> float:
    total = 0.0
    count = len(polygon)
    for index in range(count):
        x1, y1 = polygon[index]
        x2, y2 = polygon[(index + 1) % count]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def _squared_edge_lengths(polygon: list[Point]) -> list[float]:
    count = len(polygon)
    lengths = []
    for index in range(count):
        x1, y1 = polygon[index]
        x2, y2 = polygon[(index + 1) % count]
        lengths.append((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return sorted(lengths)


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


def _base_points() -> list[Point]:
    return [(vertex.x, vertex.y) for vertex in _BASE_POLYGON]


def _child_polygon_in_doubled_frame(
    matrix: tuple[int, int, int, int], translation: tuple[int, int]
) -> list[Point]:
    tx, ty = translation
    points = []
    for vertex in _BASE_POLYGON:
        rx, ry = _matrix_apply(matrix, vertex.x, vertex.y)
        points.append((rx + tx, ry + ty))
    return points


class LTetrominoGeometryTests(unittest.TestCase):
    def test_base_tile_has_area_of_four_unit_cells(self) -> None:
        self.assertEqual(_polygon_area(_base_points()), 4.0)

    def test_substitution_has_four_children(self) -> None:
        self.assertEqual(len(_CANONICAL_CHILDREN), 4)

    def test_children_are_congruent_to_the_prototile(self) -> None:
        base_edges = _squared_edge_lengths(_base_points())
        for matrix, translation in _CANONICAL_CHILDREN:
            with self.subTest(matrix=matrix):
                child = _child_polygon_in_doubled_frame(matrix, translation)
                self.assertEqual(_squared_edge_lengths(child), base_edges)

    def test_children_tile_the_doubled_parent_by_area(self) -> None:
        doubled_parent = [(2.0 * x, 2.0 * y) for (x, y) in _base_points()]
        child_area_sum = sum(
            _polygon_area(_child_polygon_in_doubled_frame(matrix, translation))
            for matrix, translation in _CANONICAL_CHILDREN
        )
        self.assertEqual(child_area_sum, _polygon_area(doubled_parent))

    def test_children_cover_the_parent_without_overlap(self) -> None:
        doubled_parent = [(2.0 * x, 2.0 * y) for (x, y) in _base_points()]
        parent_cells = _covered_unit_cells(doubled_parent)
        covered_once: set[tuple[int, int]] = set()
        child_cell_count = 0
        for child in (
            _child_polygon_in_doubled_frame(matrix, translation)
            for matrix, translation in _CANONICAL_CHILDREN
        ):
            child_cells = _covered_unit_cells(child)
            child_cell_count += len(child_cells)
            self.assertTrue(child_cells <= parent_cells)
            self.assertTrue(covered_once.isdisjoint(child_cells))
            covered_once.update(child_cells)

        self.assertEqual(covered_once, parent_cells)
        self.assertEqual(child_cell_count, len(parent_cells))


class LTetrominoRecordTests(unittest.TestCase):
    def test_canonical_record_counts_grow_as_four_to_the_depth(self) -> None:
        for depth in range(5):
            with self.subTest(depth=depth):
                self.assertEqual(len(_collect_canonical_l_tetromino_records(depth)), 4**depth)

    def test_default_record_counts_use_wide_two_tile_seed(self) -> None:
        for depth in range(5):
            with self.subTest(depth=depth):
                self.assertEqual(len(collect_l_tetromino_records(depth)), 2 * 4**depth)

    def test_orientation_tokens_are_evenly_split(self) -> None:
        for depth in range(1, 4):
            counts: dict[str, int] = {}
            for record in collect_l_tetromino_records(depth):
                token = record["orientation_token"]
                assert token is not None
                counts[token] = counts.get(token, 0) + 1
            with self.subTest(depth=depth):
                self.assertEqual(set(counts), {"0", "1", "2", "3"})
                self.assertEqual(set(counts.values()), {2 * 4 ** (depth - 1)})

    def test_canonical_depth_zero_is_single_identity_tile(self) -> None:
        records = _collect_canonical_l_tetromino_records(0)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["orientation_token"], "0")

    def test_default_depth_zero_is_wide_rectangular_seed(self) -> None:
        records = collect_l_tetromino_records(0)
        self.assertEqual(len(records), len(_DEFAULT_ROOT_SEEDS))
        self.assertEqual({record["orientation_token"] for record in records}, {"2", "3"})
        covered_once: set[tuple[int, int]] = set()
        for record in records:
            cells = _covered_unit_cells([(x, y) for x, y in record["vertices"]])
            self.assertTrue(covered_once.isdisjoint(cells))
            covered_once.update(cells)
        self.assertEqual(covered_once, {(x, y) for x in range(4) for y in range(2)})

    def test_record_ids_are_unique(self) -> None:
        ids = [record["id"] for record in collect_l_tetromino_records(3)]
        self.assertEqual(len(ids), len(set(ids)))

    def test_only_four_orientation_matrices_are_used(self) -> None:
        self.assertEqual(len(_ORIENTATION_TOKEN), 4)


class LTetrominoPatchTests(unittest.TestCase):
    def test_patch_cell_count_matches_records(self) -> None:
        for depth in range(4):
            with self.subTest(depth=depth):
                patch = build_l_tetromino_patch(depth)
                self.assertEqual(len(patch.cells), 2 * 4**depth)
                self.assertEqual(patch.patch_depth, depth)

    def test_patch_uses_wide_rectangular_extent(self) -> None:
        for depth in range(4):
            with self.subTest(depth=depth):
                patch = build_l_tetromino_patch(depth)
                self.assertEqual(patch.width, 4)
                self.assertEqual(patch.height, 2)

    def test_patch_is_connected_at_depth_two(self) -> None:
        patch = build_l_tetromino_patch(2)
        for cell in patch.cells:
            with self.subTest(cell_id=cell.id):
                self.assertGreater(len(cell.neighbors), 0)
        # Single connected component via BFS over the edge-adjacency graph.
        by_id = {cell.id: cell for cell in patch.cells}
        start = next(iter(by_id))
        seen = {start}
        stack = [start]
        while stack:
            current = stack.pop()
            for neighbor in by_id[current].neighbors:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        self.assertEqual(len(seen), len(patch.cells))


if __name__ == "__main__":
    unittest.main()
