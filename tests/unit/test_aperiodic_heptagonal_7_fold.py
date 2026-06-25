from __future__ import annotations

import math
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.aperiodic_family_manifest import (
    HEPTAGONAL_7_FOLD_MEDIUM_KIND,
    HEPTAGONAL_7_FOLD_THIN_KIND,
    HEPTAGONAL_7_FOLD_WIDE_KIND,
)
from backend.simulation.aperiodic_heptagonal_7_fold import build_heptagonal_7_fold_patch

# Deterministic multigrid-crop cell counts at half-extent 1.0 * 1.5^d.
_EXPECTED_CELL_COUNTS = {0: 62, 1: 139, 2: 317}

# Each rhombus kind's acute (smallest) interior angle is k * 180/7 degrees.
_STEP = 180.0 / 7.0
_KIND_MIN_ANGLE = {
    HEPTAGONAL_7_FOLD_THIN_KIND: 1 * _STEP,
    HEPTAGONAL_7_FOLD_MEDIUM_KIND: 2 * _STEP,
    HEPTAGONAL_7_FOLD_WIDE_KIND: 3 * _STEP,
}


def _edge_lengths(vertices: tuple[tuple[float, float], ...]) -> list[float]:
    count = len(vertices)
    return [
        math.hypot(
            vertices[(i + 1) % count][0] - vertices[i][0],
            vertices[(i + 1) % count][1] - vertices[i][1],
        )
        for i in range(count)
    ]


def _min_interior_angle(vertices: tuple[tuple[float, float], ...]) -> float:
    count = len(vertices)
    smallest = 360.0
    for i in range(count):
        previous = vertices[(i - 1) % count]
        current = vertices[i]
        following = vertices[(i + 1) % count]
        ax, ay = previous[0] - current[0], previous[1] - current[1]
        bx, by = following[0] - current[0], following[1] - current[1]
        cosine = (ax * bx + ay * by) / (math.hypot(ax, ay) * math.hypot(bx, by))
        smallest = min(smallest, math.degrees(math.acos(max(-1.0, min(1.0, cosine)))))
    return smallest


class HeptagonalSevenFoldTests(unittest.TestCase):
    def test_cell_counts_match_multigrid_crop(self) -> None:
        for depth, expected in _EXPECTED_CELL_COUNTS.items():
            patch = build_heptagonal_7_fold_patch(depth)
            self.assertEqual(len(patch.cells), expected, f"depth {depth}")

    def test_every_cell_is_an_equilateral_rhombus(self) -> None:
        # Independent geometric truth: every de Bruijn dual cell of a regular
        # multigrid is a rhombus -- four vertices with four equal edge lengths
        # (each edge is a single unit family vector). 1e-4 clears the
        # coordinate-rounding noise (precision 6) while still rejecting any
        # genuinely malformed quadrilateral.
        patch = build_heptagonal_7_fold_patch(2)
        for cell in patch.cells:
            self.assertEqual(len(cell.vertices), 4, cell.id)
            lengths = _edge_lengths(cell.vertices)
            self.assertTrue(
                all(abs(length - lengths[0]) < 1e-4 for length in lengths),
                f"{cell.id}: edges not equal: {lengths}",
            )

    def test_kind_matches_rhombus_angle(self) -> None:
        patch = build_heptagonal_7_fold_patch(2)
        for cell in patch.cells:
            self.assertIn(cell.kind, _KIND_MIN_ANGLE)
            self.assertAlmostEqual(
                _min_interior_angle(cell.vertices),
                _KIND_MIN_ANGLE[cell.kind],
                delta=0.5,
                msg=cell.id,
            )

    def test_edges_lie_on_the_seven_fold_star(self) -> None:
        # In the de Bruijn dual each rhombus edge is a family normal vector
        # ``e_i``, so edge directions (mod 180 deg) are exactly the seven family
        # normal directions ``2*pi*i/7``. Build that allowed-direction set from
        # first principles and assert each edge is within tolerance of one.
        allowed = sorted(math.degrees(2.0 * math.pi * i / 7.0) % 180.0 for i in range(7))
        patch = build_heptagonal_7_fold_patch(1)
        for cell in patch.cells:
            vertices = cell.vertices
            for i in range(len(vertices)):
                start = vertices[i]
                end = vertices[(i + 1) % len(vertices)]
                angle = math.degrees(math.atan2(end[1] - start[1], end[0] - start[0])) % 180.0
                nearest = min(min(abs(angle - a), 180.0 - abs(angle - a)) for a in allowed)
                self.assertLess(nearest, 0.5, f"{cell.id}: edge off the 7-fold star")

    def test_all_three_rhombi_present(self) -> None:
        kinds = Counter(cell.kind for cell in build_heptagonal_7_fold_patch(0).cells)
        self.assertEqual(
            set(kinds),
            {
                HEPTAGONAL_7_FOLD_THIN_KIND,
                HEPTAGONAL_7_FOLD_MEDIUM_KIND,
                HEPTAGONAL_7_FOLD_WIDE_KIND,
            },
        )

    def test_build_is_deterministic(self) -> None:
        first = build_heptagonal_7_fold_patch(1)
        second = build_heptagonal_7_fold_patch(1)
        self.assertEqual(
            [cell.id for cell in first.cells],
            [cell.id for cell in second.cells],
        )


if __name__ == "__main__":
    unittest.main()
