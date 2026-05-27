from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.aperiodic_support.neighbors import (
    build_edge_neighbors,
    build_exact_neighbors,
)
from backend.simulation.aperiodic_support.types import ExactPatchRecord, PatchRecord


def _point(x: int, y: int) -> tuple[Fraction, Fraction]:
    return (Fraction(x), Fraction(y))


class ExactSegmentOverlapNeighborTests(unittest.TestCase):
    def test_segment_overlap_groups_by_exact_supporting_line(self) -> None:
        records: list[ExactPatchRecord] = [
            {
                "id": "long",
                "kind": "triangle",
                "vertices": (_point(0, 0), _point(4, 4), _point(0, 1)),
            },
            {
                "id": "subsegment",
                "kind": "triangle",
                "vertices": (_point(2, 2), _point(1, 1), _point(1, 2)),
            },
            {
                "id": "parallel",
                "kind": "triangle",
                "vertices": (_point(1, 2), _point(2, 3), _point(1, 3)),
            },
        ]

        neighbors = build_exact_neighbors(records, neighbor_mode="segment_overlap")

        self.assertIn("subsegment", neighbors["long"])
        self.assertIn("long", neighbors["subsegment"])
        self.assertNotIn("parallel", neighbors["long"])
        self.assertNotIn("long", neighbors["parallel"])


class FloatSegmentOverlapNeighborTests(unittest.TestCase):
    def test_segment_overlap_groups_by_rounded_supporting_line(self) -> None:
        records: list[PatchRecord] = [
            {
                "id": "long",
                "kind": "triangle",
                "center": (0.0, 0.0),
                "vertices": ((0.0, 0.0), (4.0, 4.0), (0.0, 1.0)),
            },
            {
                "id": "subsegment",
                "kind": "triangle",
                "center": (0.0, 0.0),
                "vertices": ((2.0, 2.0), (1.0, 1.0), (1.0, 2.0)),
            },
            {
                "id": "parallel",
                "kind": "triangle",
                "center": (0.0, 0.0),
                "vertices": ((1.0, 2.0), (2.0, 3.0), (1.0, 3.0)),
            },
        ]

        neighbors = build_edge_neighbors(records, neighbor_mode="segment_overlap")

        self.assertIn("subsegment", neighbors["long"])
        self.assertIn("long", neighbors["subsegment"])
        self.assertNotIn("parallel", neighbors["long"])
        self.assertNotIn("long", neighbors["parallel"])


if __name__ == "__main__":
    unittest.main()
