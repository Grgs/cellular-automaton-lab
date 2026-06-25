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
    SOCOLAR_12_FOLD_RHOMB_30_KIND,
    SOCOLAR_12_FOLD_RHOMB_60_KIND,
    SOCOLAR_12_FOLD_SQUARE_KIND,
)
from backend.simulation.aperiodic_socolar_12_fold import build_socolar_12_fold_patch

# Deterministic multigrid-crop cell counts at half-extent 1.0 * 1.55^d.
_EXPECTED_CELL_COUNTS = {0: 44, 1: 102, 2: 250}

# Each rhombus kind's smallest interior angle (degrees).
_KIND_MIN_ANGLE = {
    SOCOLAR_12_FOLD_RHOMB_30_KIND: 30.0,
    SOCOLAR_12_FOLD_RHOMB_60_KIND: 60.0,
    SOCOLAR_12_FOLD_SQUARE_KIND: 90.0,
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


class SocolarTwelveFoldTests(unittest.TestCase):
    def test_cell_counts_match_multigrid_crop(self) -> None:
        for depth, expected in _EXPECTED_CELL_COUNTS.items():
            patch = build_socolar_12_fold_patch(depth)
            self.assertEqual(len(patch.cells), expected, f"depth {depth}")

    def test_every_cell_is_an_equilateral_rhombus(self) -> None:
        # Independent geometric truth: dodecagonal tiles are rhombi -- four
        # vertices with four equal edge lengths.
        patch = build_socolar_12_fold_patch(2)
        for cell in patch.cells:
            self.assertEqual(len(cell.vertices), 4, cell.id)
            lengths = _edge_lengths(cell.vertices)
            self.assertTrue(
                all(abs(length - lengths[0]) < 1e-6 for length in lengths),
                f"{cell.id}: edges not equal: {lengths}",
            )

    def test_kind_matches_rhombus_angle(self) -> None:
        patch = build_socolar_12_fold_patch(2)
        for cell in patch.cells:
            self.assertIn(cell.kind, _KIND_MIN_ANGLE)
            self.assertAlmostEqual(
                _min_interior_angle(cell.vertices),
                _KIND_MIN_ANGLE[cell.kind],
                delta=0.5,
                msg=cell.id,
            )

    def test_edges_lie_on_the_twelve_fold_star(self) -> None:
        # Every edge direction is a multiple of 30 degrees (mod 180), the
        # signature of a 12-fold dodecagonal rhomb tiling.
        patch = build_socolar_12_fold_patch(1)
        for cell in patch.cells:
            vertices = cell.vertices
            for i in range(len(vertices)):
                start = vertices[i]
                end = vertices[(i + 1) % len(vertices)]
                angle = math.degrees(math.atan2(end[1] - start[1], end[0] - start[0])) % 30.0
                offset = min(angle, 30.0 - angle)
                self.assertLess(offset, 0.5, f"{cell.id}: edge off the 30-degree star")

    def test_all_three_rhombi_present(self) -> None:
        kinds = Counter(cell.kind for cell in build_socolar_12_fold_patch(0).cells)
        self.assertEqual(
            set(kinds),
            {
                SOCOLAR_12_FOLD_RHOMB_30_KIND,
                SOCOLAR_12_FOLD_RHOMB_60_KIND,
                SOCOLAR_12_FOLD_SQUARE_KIND,
            },
        )

    def test_build_is_deterministic(self) -> None:
        first = build_socolar_12_fold_patch(1)
        second = build_socolar_12_fold_patch(1)
        self.assertEqual(
            [cell.id for cell in first.cells],
            [cell.id for cell in second.cells],
        )


if __name__ == "__main__":
    unittest.main()
