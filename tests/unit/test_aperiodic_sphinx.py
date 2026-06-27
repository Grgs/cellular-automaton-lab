from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.aperiodic_sphinx import (
    _build_canonical_sphinx_patch,
    build_sphinx_patch,
)


class SphinxPatchTests(unittest.TestCase):
    def test_canonical_patch_counts_grow_as_four_to_the_depth(self) -> None:
        for depth in range(5):
            with self.subTest(depth=depth):
                self.assertEqual(len(_build_canonical_sphinx_patch(depth).cells), 4**depth)

    def test_default_patch_uses_square_two_tile_seed(self) -> None:
        for depth in range(4):
            with self.subTest(depth=depth):
                patch = build_sphinx_patch(depth)
                self.assertEqual(len(patch.cells), 2 * 4**depth)
                self.assertEqual(patch.width, patch.height)

    def test_default_patch_remains_connected(self) -> None:
        patch = build_sphinx_patch(3)
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
