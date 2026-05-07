from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.generate_tiling_preview import _generate_polygon_data, _load_descriptors, _tiled_vertices


class GenerateTilingPreviewToolTests(unittest.TestCase):
    def test_kagome_tiled_vertices_apply_row_offset_on_odd_rows(self) -> None:
        descriptors = _load_descriptors()
        descriptor = descriptors["trihexagonal-3-6-3-6"]
        vertex = descriptor["faces"][0]["vertices"][0]
        expected = (
            vertex["x"] + descriptor["row_offset_x"],
            vertex["y"] + descriptor["unit_height"],
        )

        tiled_vertices = _tiled_vertices(
            descriptor["faces"],
            unit_width=descriptor["unit_width"],
            unit_height=descriptor["unit_height"],
            row_offset_x=descriptor["row_offset_x"],
        )

        self.assertIn(expected, tiled_vertices)

    def test_cairo_tiled_vertices_apply_row_offset_on_odd_rows(self) -> None:
        descriptors = _load_descriptors()
        descriptor = descriptors["cairo-pentagonal"]
        vertex = descriptor["faces"][0]["vertices"][0]
        expected = (
            vertex["x"] + descriptor["row_offset_x"],
            vertex["y"] + descriptor["unit_height"],
        )

        tiled_vertices = _tiled_vertices(
            descriptor["faces"],
            unit_width=descriptor["unit_width"],
            unit_height=descriptor["unit_height"],
            row_offset_x=descriptor["row_offset_x"],
        )

        self.assertIn(expected, tiled_vertices)

    def test_kagome_polygon_data_changes_when_row_offset_is_removed(self) -> None:
        descriptors = _load_descriptors()
        descriptor = descriptors["trihexagonal-3-6-3-6"]
        without_stagger = copy.deepcopy(descriptor)
        without_stagger["row_offset_x"] = 0.0

        generated = _generate_polygon_data(descriptor, fill_count=3)
        unstaggered = _generate_polygon_data(without_stagger, fill_count=3)

        self.assertNotEqual(generated, unstaggered)

    def test_cairo_polygon_data_changes_when_row_offset_is_removed(self) -> None:
        descriptors = _load_descriptors()
        descriptor = descriptors["cairo-pentagonal"]
        without_stagger = copy.deepcopy(descriptor)
        without_stagger["row_offset_x"] = 0.0

        generated = _generate_polygon_data(descriptor, fill_count=1)
        unstaggered = _generate_polygon_data(without_stagger, fill_count=1)

        self.assertNotEqual(generated, unstaggered)
