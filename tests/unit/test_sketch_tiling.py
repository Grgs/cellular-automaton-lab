"""Tests for ``tools/sketch_tiling.py``.

The example sketch under ``tools/sketch_examples/triangular_square_2uniform.py``
encodes the same 2-uniform tiling that is already wired into the backend
catalog under the geometry key ``triangular-square-2uniform``. These tests
exercise the sketch tool end-to-end (load → build → report) and verify the
result against the backend's reference verifier so we know the tool's
analysis passes match the catalog's own definition of "valid tiling".
"""

from __future__ import annotations

import math
import unittest
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
EXAMPLE_PATH = ROOT_DIR / "tools" / "sketch_examples" / "triangular_square_2uniform.py"


class SketchTilingTests(unittest.TestCase):
    def test_example_sketch_is_valid_and_matches_backend(self) -> None:
        from tools.sketch_tiling import load_sketch, sketch

        input_data = load_sketch(EXAMPLE_PATH)
        report = sketch(input_data, patch_size=3)

        # Same cell count + kind counts the backend's reference verifier sees
        self.assertEqual(len(report.cells), 96)
        self.assertEqual(report.kind_counts, {"triangle": 78, "square": 18})

        # Same interior vertex configuration histogram the backend's
        # reference verifier reports for this geometry
        self.assertEqual(
            report.interior_vertex_kinds,
            {
                ("square", "square", "triangle", "triangle", "triangle"): 25,
                ("triangle",) * 6: 18,
            },
        )

        self.assertEqual(report.overlaps, ())
        self.assertEqual(report.unmatched_edges, ())
        self.assertEqual(report.t_junctions, ())
        self.assertTrue(report.is_valid)

    def test_missing_face_is_flagged_as_invalid(self) -> None:
        from tools.sketch_tiling import SketchInput, sketch

        edge = 1.0
        h = math.sqrt(3) / 2

        # 2-uniform tiling with the central down-triangle removed: the gap
        # leaves unmatched edges and vertex angles short of 360 deg.
        faces: list[dict[str, Any]] = [
            {"slot": "ua", "kind": "triangle", "vertices": [(0, 0), (edge, 0), (edge / 2, h)]},
            {
                "slot": "ub",
                "kind": "triangle",
                "vertices": [(edge, 0), (2 * edge, 0), (3 * edge / 2, h)],
            },
            # missing "da" down-triangle that fills the upper gap
            {
                "slot": "dleft",
                "kind": "triangle",
                "vertices": [(-edge / 2, h), (edge / 2, h), (0, 0)],
                "repeat_x_extra": 1,
            },
        ]
        input_data = SketchInput(
            faces=tuple(faces),
            cell_width=2 * edge,
            cell_height=h,
            geometry="broken",
            label="broken",
        )
        report = sketch(input_data, patch_size=3)
        self.assertFalse(report.is_valid)
        # There should be unmatched interior edges where the missing
        # triangle would have provided the matching edge.
        self.assertGreater(len(report.unmatched_edges), 0)

    def test_overlapping_faces_are_flagged(self) -> None:
        from tools.sketch_tiling import SketchInput, sketch

        # Two identical squares occupying the same cell: 100% overlap.
        faces: list[dict[str, Any]] = [
            {"slot": "a", "kind": "square", "vertices": [(0, 0), (1, 0), (1, 1), (0, 1)]},
            {"slot": "b", "kind": "square", "vertices": [(0, 0), (1, 0), (1, 1), (0, 1)]},
        ]
        input_data = SketchInput(
            faces=tuple(faces),
            cell_width=1.0,
            cell_height=1.0,
            geometry="overlap",
            label="overlap",
        )
        report = sketch(input_data, patch_size=2)
        self.assertGreater(len(report.overlaps), 0)
        self.assertFalse(report.is_valid)


if __name__ == "__main__":
    unittest.main()
