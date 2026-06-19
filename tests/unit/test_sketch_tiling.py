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
UNIFORM_2_10_PATH = ROOT_DIR / "tools" / "sketch_examples" / "uniform_2_10.py"


class SketchTilingTests(unittest.TestCase):
    def test_edges_outside_logical_patch_are_boundary_edges(self) -> None:
        from tools.sketch_tiling import _is_interior_edge

        bounds = (0.0, 0.0, 10.0, 10.0)

        self.assertFalse(_is_interior_edge(((-2.0, 3.0), (-2.0, 4.0)), bounds))
        self.assertFalse(_is_interior_edge(((12.0, 3.0), (12.0, 4.0)), bounds))
        self.assertTrue(_is_interior_edge(((2.0, 3.0), (2.0, 4.0)), bounds))

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

    def test_uniform_2_10_sketch_has_only_its_two_catalog_vertex_types(self) -> None:
        from tools.sketch_tiling import load_sketch, sketch

        report = sketch(load_sketch(UNIFORM_2_10_PATH), patch_size=3)

        self.assertEqual(
            set(report.interior_vertex_kinds),
            {
                ("hexagon", "hexagon", "triangle", "triangle"),
                ("triangle",) * 6,
            },
        )
        self.assertEqual(report.overlaps, ())
        self.assertEqual(report.unmatched_edges, ())
        self.assertEqual(report.t_junctions, ())
        self.assertEqual(report.invalid_interior_vertices, ())
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

    def test_emit_reference_spec_loads_and_matches_handwritten_spec(self) -> None:
        """The generated reference-spec module loads as a Python module and
        produces a SPECS dict whose counts match the hand-written one in the
        backend catalog. (The hand-written spec also informs the verifier so
        if the verifier passes for that geometry, the generated spec is
        guaranteed to as well.)"""
        import importlib.util
        import tempfile

        from tools.sketch_tiling import emit_reference_spec, load_sketch, sketch

        input_data = load_sketch(EXAMPLE_PATH)
        report = sketch(input_data, patch_size=3)
        source = emit_reference_spec(input_data, report, patch_size=3)

        # Module must be syntactically valid Python.
        with tempfile.NamedTemporaryFile(
            "w", suffix=".py", delete=False, encoding="utf-8"
        ) as handle:
            handle.write(source)
            spec_path = Path(handle.name)
        try:
            spec_module_spec = importlib.util.spec_from_file_location("generated_spec", spec_path)
            assert spec_module_spec is not None and spec_module_spec.loader is not None
            module = importlib.util.module_from_spec(spec_module_spec)
            spec_module_spec.loader.exec_module(module)
        finally:
            spec_path.unlink()

        # Compare key fields against the existing hand-written spec for
        # the same geometry.
        from backend.simulation.reference_specs.periodic.triangular_square_2uniform import (
            SPECS as REFERENCE_SPECS,
        )

        generated = module.SPECS["triangular-square-2uniform"]
        expected = REFERENCE_SPECS["triangular-square-2uniform"]
        self.assertEqual(generated.geometry, expected.geometry)
        gen_depth = generated.depth_expectations[3]
        exp_depth = expected.depth_expectations[3]
        self.assertEqual(gen_depth.exact_total_cells, exp_depth.exact_total_cells)
        self.assertEqual(
            set(gen_depth.expected_kind_counts or ()),
            set(exp_depth.expected_kind_counts or ()),
        )
        self.assertEqual(
            set(gen_depth.expected_adjacency_pairs or ()),
            set(exp_depth.expected_adjacency_pairs or ()),
        )
        self.assertEqual(
            set(gen_depth.expected_degree_histogram or ()),
            set(exp_depth.expected_degree_histogram or ()),
        )
        gen_periodic = generated.periodic_descriptor
        exp_periodic = expected.periodic_descriptor
        assert gen_periodic is not None and exp_periodic is not None
        self.assertEqual(
            dict(gen_periodic.expected_interior_vertex_configuration_frequencies),
            dict(exp_periodic.expected_interior_vertex_configuration_frequencies),
        )


class SketchTilingLatticeSkewTests(unittest.TestCase):
    """``LATTICE_SKEW_X`` plumbs through to the same builder the catalog uses,
    so a skewed-parallelogram tiling like Stein-14 can be iterated against the
    sketch validator before any catalog wiring exists."""

    STEIN14_SKETCH = ROOT_DIR / "tools" / "sketch_examples" / "stein_14_pentagonal.py"

    def test_lattice_skew_x_is_read_from_sketch_module(self) -> None:
        from tools.sketch_tiling import load_sketch

        input_data = load_sketch(self.STEIN14_SKETCH)
        self.assertAlmostEqual(input_data.lattice_skew_x or 0.0, -153.02078259, places=6)
        self.assertEqual(input_data.row_offset_x, 0.0)

    def test_lattice_skew_x_drives_cumulative_skew_per_row(self) -> None:
        from tools.sketch_tiling import load_sketch, sketch

        input_data = load_sketch(self.STEIN14_SKETCH)
        report = sketch(input_data, patch_size=2)
        # 6 face templates x 2x2 patch = 24 cells.
        self.assertEqual(len(report.cells), 24)
        # Pick the t0 cells at logical (0, 0) and (0, 1) and confirm their
        # centres differ by the skew vector (not by 0 as the brick semantic
        # would imply for an even row).
        by_id = {cell.id: cell for cell in report.cells}
        c00 = by_id["p:t0:0:0"]
        c01 = by_id["p:t0:0:1"]
        delta_x = c01.center[0] - c00.center[0]
        delta_y = c01.center[1] - c00.center[1]
        self.assertAlmostEqual(delta_x, input_data.lattice_skew_x or 0.0, places=4)
        self.assertAlmostEqual(delta_y, input_data.cell_height, places=4)

    def test_emit_descriptor_includes_lattice_skew_x_when_set(self) -> None:
        from tools.sketch_tiling import emit_descriptor_json, load_sketch

        input_data = load_sketch(self.STEIN14_SKETCH)
        descriptor = emit_descriptor_json(input_data)
        self.assertEqual(descriptor["geometry"], "stein-14-pentagonal")
        self.assertAlmostEqual(descriptor["lattice_skew_x"], -153.02078259, places=6)
        self.assertNotIn("row_offset_x", descriptor)
        self.assertNotIn("label", descriptor)
        self.assertEqual(descriptor["min_dimension"], 1)

    def test_emit_descriptor_omits_lattice_skew_x_when_not_set(self) -> None:
        """The triangle+square 2-uniform example doesn't use the skew lattice;
        its descriptor must not get a stray ``lattice_skew_x`` field."""
        from tools.sketch_tiling import emit_descriptor_json, load_sketch

        input_data = load_sketch(EXAMPLE_PATH)
        descriptor = emit_descriptor_json(input_data)
        self.assertNotIn("lattice_skew_x", descriptor)

    def test_setting_both_offset_modes_raises(self) -> None:
        """Sketches must pick one lattice semantic. Setting both should error
        at load time so the failure is loud and immediate."""
        import tempfile

        from tools.sketch_tiling import load_sketch

        with tempfile.NamedTemporaryFile(
            "w", suffix=".py", delete=False, encoding="utf-8"
        ) as handle:
            handle.write(
                "CELL_WIDTH = 100.0\n"
                "CELL_HEIGHT = 100.0\n"
                "ROW_OFFSET_X = 50.0\n"
                "LATTICE_SKEW_X = -25.0\n"
                "FACES = []\n"
            )
            sketch_path = Path(handle.name)
        try:
            with self.assertRaisesRegex(RuntimeError, "mutually exclusive"):
                load_sketch(sketch_path)
        finally:
            sketch_path.unlink()


class SketchHelpersTests(unittest.TestCase):
    def test_equilateral_triangle_is_equilateral(self) -> None:
        from tools.sketch_helpers import equilateral_triangle

        verts = equilateral_triangle((0, 0), (1, 0), side="above")
        side_lengths = [
            math.hypot(verts[i][0] - verts[(i + 1) % 3][0], verts[i][1] - verts[(i + 1) % 3][1])
            for i in range(3)
        ]
        for length in side_lengths:
            self.assertAlmostEqual(length, 1.0, places=5)

    def test_equilateral_triangle_above_below_are_mirrors(self) -> None:
        from tools.sketch_helpers import equilateral_triangle

        above = equilateral_triangle((0, 0), (1, 0), side="above")
        below = equilateral_triangle((0, 0), (1, 0), side="below")
        # Apex y-coordinates are equal magnitude, opposite sign
        # (above has apex at +sqrt(3)/2, below at -sqrt(3)/2)
        self.assertAlmostEqual(above[2][1], -below[1][1], places=5)

    def test_square_returns_four_ccw_vertices(self) -> None:
        from tools.sketch_helpers import square

        verts = square((0, 0), 1)
        self.assertEqual(len(verts), 4)
        self.assertEqual(verts[0], (0, 0))
        self.assertEqual(verts[2], (1, 1))

    def test_regular_hexagon_has_six_vertices_with_correct_edge_length(self) -> None:
        from tools.sketch_helpers import regular_hexagon

        verts = regular_hexagon((0, 0), 1.0, orientation="flat-top")
        self.assertEqual(len(verts), 6)
        for i in range(6):
            length = math.hypot(
                verts[i][0] - verts[(i + 1) % 6][0],
                verts[i][1] - verts[(i + 1) % 6][1],
            )
            self.assertAlmostEqual(length, 1.0, places=5)

    def test_square_with_mid_edge_vertices_returns_eight_vertices(self) -> None:
        from tools.sketch_helpers import square_with_mid_edge_vertices

        verts = square_with_mid_edge_vertices(
            (0, 0), 50, bottom=True, right=True, top=True, left=True
        )
        self.assertEqual(len(verts), 8)
        # Midpoints are present
        self.assertIn((25.0, 0), verts)
        self.assertIn((50, 25.0), verts)
        self.assertIn((25.0, 50), verts)
        self.assertIn((0, 25.0), verts)


class TopologyValidationPrecisionFixTests(unittest.TestCase):
    """Regression test for the 2-uniform precision-bug class: a tiny float
    drift between a JSON-stored coordinate (rounded to 6 decimals) and a
    math-derived coordinate (52 * sqrt(3) unrounded) should NOT trigger a
    false-positive polygon overlap when the geometry is periodic-face."""

    def test_periodic_face_geometry_snaps_to_grid(self) -> None:
        from backend.simulation.topology_types import LatticeCell, LatticeTopology
        from backend.simulation.topology_validation import topology_polygons

        y_unrounded = 52 * math.sqrt(3)  # 90.06664199358161
        y_rounded = 90.066642  # what JSON storage gives

        cell1 = LatticeCell(
            id="t1",
            kind="triangle",
            neighbors=(),
            vertices=(
                (0.0, y_rounded),
                (52.0, y_rounded),
                (26.0, y_rounded - 26 * math.sqrt(3)),
            ),
            center=(26.0, y_rounded - 9.0),
        )
        cell2 = LatticeCell(
            id="s1",
            kind="square",
            neighbors=(),
            vertices=(
                (0.0, y_unrounded),
                (52.0, y_unrounded),
                (52.0, y_unrounded + 52),
                (0.0, y_unrounded + 52),
            ),
            center=(26.0, y_unrounded + 26),
        )
        # Periodic-face geometry: snap-to-grid applies, no spurious overlap.
        periodic_topology = LatticeTopology(
            geometry="triangular-square-2uniform",
            width=1,
            height=1,
            cells=(cell1, cell2),
            topology_revision="test",
            patch_depth=None,
        )
        polys = topology_polygons(periodic_topology)
        self.assertAlmostEqual(polys["t1"].intersection(polys["s1"]).area, 0.0, places=10)

    def test_aperiodic_geometry_skips_snap(self) -> None:
        """For aperiodic substitution families, irrational vertex
        coordinates intentionally use full float precision. The snap-to-grid
        should NOT apply (it would create surface-union holes that don't
        exist in the unsnapped representation)."""
        from backend.simulation.topology_types import LatticeCell, LatticeTopology
        from backend.simulation.topology_validation import topology_polygons

        # An odd coordinate that would shift under 6-decimal rounding.
        cell = LatticeCell(
            id="p1",
            kind="prototile",
            neighbors=(),
            vertices=((0.0, 0.0), (1.2345678901234, 0.0), (0.5, 0.8765432109876)),
            center=(0.5, 0.3),
        )
        aperiodic_topology = LatticeTopology(
            geometry="spectre",
            width=1,
            height=1,
            cells=(cell,),
            topology_revision="test",
            patch_depth=None,
        )
        polys = topology_polygons(aperiodic_topology)
        # Vertices preserved at full precision
        coords = list(polys["p1"].exterior.coords)
        self.assertAlmostEqual(coords[1][0], 1.2345678901234, places=12)


if __name__ == "__main__":
    unittest.main()
