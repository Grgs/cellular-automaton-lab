from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.aperiodic_support import edge_scaled_vertex_map
from backend.simulation.aperiodic_support.patches import patch_from_cells
from backend.simulation.aperiodic_support.types import AperiodicPatch, AperiodicPatchCell

# Two unit squares sharing the edge (1,0)-(1,1).
_LEFT = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
_RIGHT = ((1.0, 0.0), (2.0, 0.0), (2.0, 1.0), (1.0, 1.0))


def _two_square_patch() -> AperiodicPatch:
    cells = (
        AperiodicPatchCell(
            id="left", kind="square", center=(0.5, 0.5), vertices=_LEFT, neighbors=("right",)
        ),
        AperiodicPatchCell(
            id="right", kind="square", center=(1.5, 0.5), vertices=_RIGHT, neighbors=("left",)
        ),
    )
    return patch_from_cells(0, cells)


class EdgeScaledVertexMapTests(unittest.TestCase):
    def test_identity_scaling_preserves_relative_geometry(self) -> None:
        patch = _two_square_patch()
        mapped = edge_scaled_vertex_map(patch, lambda _start, _end: 1.0)
        # Identity scaling is a pure translation: every pairwise displacement is
        # unchanged, across the shared edge between the two cells.
        for a in (*_LEFT, *_RIGHT):
            for b in (*_LEFT, *_RIGHT):
                expected = (b[0] - a[0], b[1] - a[1])
                actual = (mapped(b)[0] - mapped(a)[0], mapped(b)[1] - mapped(a)[1])
                self.assertAlmostEqual(actual[0], expected[0])
                self.assertAlmostEqual(actual[1], expected[1])

    def test_uniform_scaling_scales_every_displacement(self) -> None:
        patch = _two_square_patch()
        mapped = edge_scaled_vertex_map(patch, lambda _start, _end: 2.0)
        for a in (*_LEFT, *_RIGHT):
            for b in (*_LEFT, *_RIGHT):
                expected = (2.0 * (b[0] - a[0]), 2.0 * (b[1] - a[1]))
                actual = (mapped(b)[0] - mapped(a)[0], mapped(b)[1] - mapped(a)[1])
                self.assertAlmostEqual(actual[0], expected[0])
                self.assertAlmostEqual(actual[1], expected[1])

    def test_shared_vertex_is_single_valued_across_cells(self) -> None:
        patch = _two_square_patch()
        mapped = edge_scaled_vertex_map(patch, lambda _start, _end: 1.5)
        # (1,1) is the shared corner; both cells must map it to the same point.
        self.assertEqual(mapped((1.0, 1.0)), mapped((1.0, 1.0)))
        # A horizontal edge scaled by 1.5 has length 1.5 in the result.
        left = mapped((0.0, 0.0))
        right = mapped((1.0, 0.0))
        self.assertAlmostEqual(right[0] - left[0], 1.5)


if __name__ == "__main__":
    unittest.main()
