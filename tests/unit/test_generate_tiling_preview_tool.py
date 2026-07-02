from __future__ import annotations

import copy
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools._common import write_text_lf
from tools.generate_tiling_preview import (
    _APERIODIC_DEFAULT_DEPTHS,
    _aperiodic_polygon_data,
    _generate_polygon_data,
    _load_descriptors,
    _tiled_vertices,
    main,
    write_preview_entry,
)


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

    def test_dodecagonal_preview_uses_representative_depth_and_palette_tokens(self) -> None:
        self.assertEqual(_APERIODIC_DEFAULT_DEPTHS["dodecagonal-square-triangle"], 1)

        polygon_data, cell_count, color_count = _aperiodic_polygon_data(
            "dodecagonal-square-triangle",
            _APERIODIC_DEFAULT_DEPTHS["dodecagonal-square-triangle"],
        )

        self.assertEqual(cell_count, 5)
        self.assertEqual(color_count, 4)
        self.assertIn("toneCream:", polygon_data)
        self.assertIn("toneClay:", polygon_data)
        self.assertIn("toneFlax:", polygon_data)
        self.assertIn("toneSand:", polygon_data)

    def test_periodic_polygon_data_can_emit_palette_tokens(self) -> None:
        descriptors = _load_descriptors()
        descriptor = descriptors["archimedean-4-8-8"]

        generated = _generate_polygon_data(
            descriptor,
            fill_count=2,
            geometry="archimedean-4-8-8",
        )

        self.assertIn("toneCream:", generated)
        self.assertIn("toneTan:", generated)

    def test_write_text_lf_emits_lf_even_for_crlf_or_native_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.ts"
            write_text_lf(path, "line one\nline two\n")
            self.assertEqual(path.read_bytes().count(b"\r"), 0)

    def test_write_preview_entry_appends_without_introducing_crlf(self) -> None:
        # Regression: Path.write_text rewrites \n to \r\n on Windows, which
        # flipped the whole generated file to CRLF and tripped the Prettier
        # pre-commit hook. The writer must keep the file on LF.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tiling-preview-data.ts"
            write_text_lf(
                path,
                "export const POLYGON_PREVIEW_DATA: Readonly<Record<string, string>> = {\n};\n",
            )
            write_preview_entry("widget-monotile", "toneSand:0,0 1,0 1,1", output_path=path)
            self.assertEqual(path.read_bytes().count(b"\r"), 0)
            self.assertIn('"widget-monotile":', path.read_text(encoding="utf-8"))

    def test_periodic_mode_points_aperiodic_geometry_to_aperiodic_flag(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = main(["--geometry", "spectre"])
        self.assertEqual(exit_code, 1)
        message = stderr.getvalue()
        self.assertIn("--aperiodic", message)
        self.assertIn("spectre", message)
