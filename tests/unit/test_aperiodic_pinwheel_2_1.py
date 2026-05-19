from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.aperiodic_pinwheel_2_1 import (
    KIND_LARGE,
    KIND_SMALL,
    TILE_FAMILY,
    _ALL_CHILDREN,
    _BASE_TRIANGLE,
    _subdivide,
    build_pinwheel_2_1_patch,
    collect_pinwheel_2_1_exact_records,
)


ExactPoint = tuple[Fraction, Fraction]
ExactTriangle = tuple[ExactPoint, ExactPoint, ExactPoint]


def _triangle_area_double(triangle: ExactTriangle) -> Fraction:
    """Return 2 * |signed area| of a triangle in exact arithmetic."""
    (ax, ay), (bx, by), (cx, cy) = triangle
    signed_double = ((bx - ax) * (cy - ay)) - ((cx - ax) * (by - ay))
    return signed_double if signed_double >= 0 else -signed_double


def _squared_side_lengths(triangle: ExactTriangle) -> tuple[Fraction, Fraction, Fraction]:
    (ax, ay), (bx, by), (cx, cy) = triangle
    ab_sq = (bx - ax) ** 2 + (by - ay) ** 2
    bc_sq = (cx - bx) ** 2 + (cy - by) ** 2
    ca_sq = (ax - cx) ** 2 + (ay - cy) ** 2
    return tuple(sorted([ab_sq, bc_sq, ca_sq]))  # type: ignore[return-value]


def _is_pinwheel_2_1_shape(triangle: ExactTriangle) -> bool:
    """A 1:4:sqrt(17) right triangle has squared sides in ratio 1 : 16 : 17."""
    sides = _squared_side_lengths(triangle)
    smallest = sides[0]
    if smallest == 0:
        return False
    return (sides[1] / smallest == Fraction(16, 1)) and (sides[2] / smallest == Fraction(17, 1))


class PinwheelTwoOneGeometryTests(unittest.TestCase):
    def test_base_triangle_is_one_to_four_root_seventeen(self) -> None:
        self.assertTrue(_is_pinwheel_2_1_shape(_BASE_TRIANGLE))

    def test_subdivision_has_one_small_and_four_large_children(self) -> None:
        kinds = [kind for kind, _ in _ALL_CHILDREN]
        self.assertEqual(kinds.count(KIND_SMALL), 1)
        self.assertEqual(kinds.count(KIND_LARGE), 4)
        self.assertEqual(len(_ALL_CHILDREN), 5)

    def test_children_tile_parent_exactly_by_area(self) -> None:
        parent_area_double = _triangle_area_double(_BASE_TRIANGLE)
        children = _subdivide(_BASE_TRIANGLE)
        child_area_double_sum = sum(
            (_triangle_area_double(child) for _, child in children), start=Fraction(0)
        )
        self.assertEqual(child_area_double_sum, parent_area_double)

    def test_every_child_is_similar_to_parent(self) -> None:
        for kind, child in _subdivide(_BASE_TRIANGLE):
            with self.subTest(kind=kind, child=child):
                self.assertTrue(_is_pinwheel_2_1_shape(child))

    def test_small_child_has_area_one_seventeenth_of_parent(self) -> None:
        # The small child is the right-angle corner triangle whose legs
        # are the altitude foot from c onto ab. Its area is 1/17 of the
        # parent (linear scale 1/sqrt(17)).
        parent_area_double = _triangle_area_double(_BASE_TRIANGLE)
        small_children = [child for kind, child in _subdivide(_BASE_TRIANGLE) if kind == KIND_SMALL]
        self.assertEqual(len(small_children), 1)
        small_area_double = _triangle_area_double(small_children[0])
        self.assertEqual(small_area_double * 17, parent_area_double)

    def test_each_large_child_has_area_four_seventeenths_of_parent(self) -> None:
        # Each large child has linear scale 2/sqrt(17), so area 4/17.
        parent_area_double = _triangle_area_double(_BASE_TRIANGLE)
        for kind, child in _subdivide(_BASE_TRIANGLE):
            if kind != KIND_LARGE:
                continue
            with self.subTest(child=child):
                self.assertEqual(_triangle_area_double(child) * 17, parent_area_double * 4)

    def test_recursion_preserves_similarity_at_depth_two(self) -> None:
        # If the first-level subdivision produces canonical-orientation
        # similar children, then subdividing each child again should also
        # produce 1:4:sqrt(17) grandchildren.
        for kind, child in _subdivide(_BASE_TRIANGLE):
            for grand_kind, grandchild in _subdivide(child):
                with self.subTest(parent_kind=kind, grand_kind=grand_kind):
                    self.assertTrue(_is_pinwheel_2_1_shape(grandchild))

    def test_depth_two_grandchildren_tile_parent(self) -> None:
        parent_area_double = _triangle_area_double(_BASE_TRIANGLE)
        total = Fraction(0)
        for _, child in _subdivide(_BASE_TRIANGLE):
            for _, grandchild in _subdivide(child):
                total += _triangle_area_double(grandchild)
        self.assertEqual(total, parent_area_double)


class PinwheelTwoOneRecordTests(unittest.TestCase):
    def test_depth_zero_yields_two_large_records_for_paired_roots(self) -> None:
        # Two roots forming a 4:1 rectangle, both labeled as the large
        # prototile at depth 0.
        records = collect_pinwheel_2_1_exact_records(0)
        self.assertEqual(len(records), 2)
        self.assertEqual({r["kind"] for r in records}, {KIND_LARGE})
        for record in records:
            self.assertEqual(record["tile_family"], TILE_FAMILY)

    def test_depth_one_yields_ten_records_in_canonical_split(self) -> None:
        # One small + four large per root × two roots = 10 cells.
        records = collect_pinwheel_2_1_exact_records(1)
        self.assertEqual(len(records), 10)
        kinds = [record["kind"] for record in records]
        self.assertEqual(kinds.count(KIND_SMALL), 2)
        self.assertEqual(kinds.count(KIND_LARGE), 8)

    def test_record_counts_grow_as_two_times_five_to_the_depth(self) -> None:
        for depth in range(4):
            with self.subTest(depth=depth):
                records = collect_pinwheel_2_1_exact_records(depth)
                self.assertEqual(len(records), 2 * 5**depth)

    def test_record_ids_are_unique(self) -> None:
        records = collect_pinwheel_2_1_exact_records(3)
        ids = [record["id"] for record in records]
        self.assertEqual(len(ids), len(set(ids)))

    def test_orientation_and_chirality_tokens_present(self) -> None:
        for record in collect_pinwheel_2_1_exact_records(2):
            with self.subTest(record_id=record["id"]):
                self.assertIn(record.get("chirality_token"), {"left", "right"})
                token = record.get("orientation_token")
                self.assertIsNotNone(token)
                assert token is not None  # narrow for type checker
                self.assertTrue(0 <= int(token) < 360)


class PinwheelTwoOnePatchTests(unittest.TestCase):
    def test_build_patch_returns_cells_matching_record_count(self) -> None:
        for depth in range(3):
            with self.subTest(depth=depth):
                patch = build_pinwheel_2_1_patch(depth)
                self.assertEqual(len(patch.cells), 2 * 5**depth)
                self.assertEqual(patch.patch_depth, depth)

    def test_build_patch_assigns_neighbors_at_depth_two(self) -> None:
        patch = build_pinwheel_2_1_patch(2)
        # In a 50-triangle patch every cell should have at least one
        # segment-overlap neighbor (the patch is connected).
        for cell in patch.cells:
            with self.subTest(cell_id=cell.id):
                self.assertGreater(len(cell.neighbors), 0)


if __name__ == "__main__":
    unittest.main()
