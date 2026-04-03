import sys
import unittest
from pathlib import Path

try:
    from backend.simulation.periodic_face_tilings import PERIODIC_FACE_TILING_GEOMETRIES
    from backend.simulation.topology import (
        LatticeCell,
        LatticeTopology,
        HAT_MONOTILE_GEOMETRY,
        PENROSE_GEOMETRY,
        PINWHEEL_GEOMETRY,
        SHIELD_GEOMETRY,
        SPHINX_GEOMETRY,
        SPECTRE_GEOMETRY,
        SQUARE_TRIANGLE_GEOMETRY,
        TAYLOR_SOCOLAR_GEOMETRY,
        CHAIR_GEOMETRY,
        ROBINSON_TRIANGLES_GEOMETRY,
        TUEBINGEN_TRIANGLE_GEOMETRY,
        PENROSE_VERTEX_GEOMETRY,
        build_topology,
    )
    from backend.simulation.topology_validation import recommended_validation_options, validate_topology
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.simulation.periodic_face_tilings import PERIODIC_FACE_TILING_GEOMETRIES
    from backend.simulation.topology import (
        LatticeCell,
        LatticeTopology,
        HAT_MONOTILE_GEOMETRY,
        PENROSE_GEOMETRY,
        PINWHEEL_GEOMETRY,
        SHIELD_GEOMETRY,
        SPHINX_GEOMETRY,
        SPECTRE_GEOMETRY,
        SQUARE_TRIANGLE_GEOMETRY,
        TAYLOR_SOCOLAR_GEOMETRY,
        CHAIR_GEOMETRY,
        ROBINSON_TRIANGLES_GEOMETRY,
        TUEBINGEN_TRIANGLE_GEOMETRY,
        PENROSE_VERTEX_GEOMETRY,
        build_topology,
    )
    from backend.simulation.topology_validation import recommended_validation_options, validate_topology


def _polygon_cell(
    cell_id: str,
    vertices: tuple[tuple[float, float], ...],
    *,
    neighbors: tuple[str, ...] = (),
    kind: str = "square",
) -> LatticeCell:
    return LatticeCell(
        id=cell_id,
        kind=kind,
        neighbors=neighbors,
        vertices=vertices,
    )


def _square_cell(
    cell_id: str,
    x: int,
    y: int,
    *,
    neighbors: tuple[str, ...] = (),
) -> LatticeCell:
    return _polygon_cell(
        cell_id,
        (
            (float(x), float(y)),
            (float(x + 1), float(y)),
            (float(x + 1), float(y + 1)),
            (float(x), float(y + 1)),
        ),
        neighbors=neighbors,
    )


def _topology(*cells: LatticeCell, revision: str = "fixture-v1") -> LatticeTopology:
    return LatticeTopology(
        geometry="fixture",
        width=1,
        height=1,
        topology_revision=revision,
        cells=cells,
    )


class TopologyValidationTests(unittest.TestCase):
    def test_periodic_face_tilings_pass_geometry_and_graph_validation(self) -> None:
        for geometry in PERIODIC_FACE_TILING_GEOMETRIES:
            with self.subTest(geometry=geometry):
                topology = build_topology(geometry, 3, 3)
                validation = validate_topology(topology, **recommended_validation_options(geometry))
                self.assertTrue(validation.is_valid, "\n".join(validation.summary_lines()))

    def test_penrose_modes_pass_geometry_and_graph_validation(self) -> None:
        for geometry in (PENROSE_GEOMETRY, PENROSE_VERTEX_GEOMETRY):
            with self.subTest(geometry=geometry):
                topology = build_topology(geometry, 0, 0, patch_depth=3)
                validation = validate_topology(topology, **recommended_validation_options(geometry))
                self.assertTrue(validation.is_valid, "\n".join(validation.summary_lines()))

    def test_spectre_patch_passes_geometry_and_graph_validation(self) -> None:
        topology = build_topology(SPECTRE_GEOMETRY, 0, 0, patch_depth=3)
        validation = validate_topology(topology, **recommended_validation_options(SPECTRE_GEOMETRY))

        self.assertTrue(validation.is_valid, "\n".join(validation.summary_lines()))

    def test_taylor_socolar_patch_passes_geometry_and_graph_validation(self) -> None:
        topology = build_topology(TAYLOR_SOCOLAR_GEOMETRY, 0, 0, patch_depth=3)
        validation = validate_topology(topology, **recommended_validation_options(TAYLOR_SOCOLAR_GEOMETRY))

        self.assertTrue(validation.is_valid, "\n".join(validation.summary_lines()))

    def test_sphinx_patch_passes_geometry_and_graph_validation(self) -> None:
        topology = build_topology(SPHINX_GEOMETRY, 0, 0, patch_depth=3)
        validation = validate_topology(topology, **recommended_validation_options(SPHINX_GEOMETRY))

        self.assertTrue(validation.is_valid, "\n".join(validation.summary_lines()))

    def test_chair_patch_passes_geometry_and_graph_validation(self) -> None:
        topology = build_topology(CHAIR_GEOMETRY, 0, 0, patch_depth=3)
        validation = validate_topology(topology, **recommended_validation_options(CHAIR_GEOMETRY))

        self.assertTrue(validation.is_valid, "\n".join(validation.summary_lines()))

    def test_robinson_triangles_patch_passes_geometry_and_graph_validation(self) -> None:
        topology = build_topology(ROBINSON_TRIANGLES_GEOMETRY, 0, 0, patch_depth=3)
        validation = validate_topology(topology, **recommended_validation_options(ROBINSON_TRIANGLES_GEOMETRY))

        self.assertTrue(validation.is_valid, "\n".join(validation.summary_lines()))

    def test_new_aperiodic_wave_patches_pass_geometry_and_graph_validation(self) -> None:
        for geometry in (
            HAT_MONOTILE_GEOMETRY,
            TUEBINGEN_TRIANGLE_GEOMETRY,
            SQUARE_TRIANGLE_GEOMETRY,
            SHIELD_GEOMETRY,
            PINWHEEL_GEOMETRY,
        ):
            with self.subTest(geometry=geometry):
                topology = build_topology(geometry, 0, 0, patch_depth=3)
                validation = validate_topology(topology, **recommended_validation_options(geometry))
                self.assertTrue(validation.is_valid, "\n".join(validation.summary_lines()))

    def test_snub_square_regression_is_covered_by_shared_validator(self) -> None:
        topology = build_topology("archimedean-3-3-4-3-4", 3, 3)
        validation = validate_topology(
            topology,
            **recommended_validation_options("archimedean-3-3-4-3-4"),
        )

        self.assertTrue(validation.is_valid, "\n".join(validation.summary_lines()))
        self.assertEqual(validation.hole_count, 0)
        self.assertFalse(validation.edge_multiplicity_issues)

    def test_kagome_uses_strict_exact_surface_policy(self) -> None:
        options = recommended_validation_options("trihexagonal-3-6-3-6")

        self.assertEqual(
            options,
            {
                "check_surface": True,
                "check_overlaps": True,
                "check_edge_multiplicity": True,
            },
        )

    def test_validator_flags_asymmetric_neighbor_links(self) -> None:
        topology = LatticeTopology(
            geometry="fixture",
            width=1,
            height=1,
            topology_revision="fixture-v1",
            cells=(
                LatticeCell(
                    id="a",
                    kind="square",
                    neighbors=("b",),
                    vertices=((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),
                ),
                LatticeCell(
                    id="b",
                    kind="square",
                    neighbors=(),
                    vertices=((1.0, 0.0), (2.0, 0.0), (2.0, 1.0), (1.0, 1.0)),
                ),
            ),
        )

        validation = validate_topology(topology)

        self.assertFalse(validation.is_valid)
        self.assertIn(("a", "b"), validation.asymmetric_neighbor_links)

    def test_validator_flags_neighbor_links_that_do_not_share_geometry(self) -> None:
        topology = LatticeTopology(
            geometry="fixture",
            width=1,
            height=1,
            topology_revision="fixture-v2",
            cells=(
                LatticeCell(
                    id="a",
                    kind="square",
                    neighbors=("b",),
                    vertices=((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),
                ),
                LatticeCell(
                    id="b",
                    kind="square",
                    neighbors=("a",),
                    vertices=((1.1, 0.0), (2.1, 0.0), (2.1, 1.0), (1.1, 1.0)),
                ),
            ),
        )

        validation = validate_topology(topology)

        self.assertFalse(validation.is_valid)
        self.assertEqual(validation.surface_component_count, 2)

    def test_validator_flags_invalid_polygon_shapes(self) -> None:
        topology = _topology(
            _polygon_cell(
                "bowtie",
                ((0.0, 0.0), (1.0, 1.0), (0.0, 1.0), (1.0, 0.0)),
            ),
            revision="fixture-invalid-polygon",
        )

        validation = validate_topology(topology)

        self.assertFalse(validation.is_valid)
        self.assertTrue(any(issue.cell_id == "bowtie" for issue in validation.polygon_issues))

    def test_validator_flags_zero_area_polygons(self) -> None:
        topology = _topology(
            _polygon_cell(
                "line",
                ((0.0, 0.0), (1.0, 0.0), (2.0, 0.0)),
            ),
            revision="fixture-zero-area",
        )

        validation = validate_topology(topology)

        self.assertFalse(validation.is_valid)
        self.assertIn(("line", "non-positive area"), {(issue.cell_id, issue.reason) for issue in validation.polygon_issues})

    def test_validator_flags_overlapping_polygons(self) -> None:
        topology = _topology(
            _polygon_cell(
                "a",
                ((0.0, 0.0), (1.2, 0.0), (1.2, 1.0), (0.0, 1.0)),
            ),
            _polygon_cell(
                "b",
                ((0.8, 0.0), (1.8, 0.0), (1.8, 1.0), (0.8, 1.0)),
            ),
            revision="fixture-overlap",
        )

        validation = validate_topology(topology)

        self.assertFalse(validation.is_valid)
        self.assertEqual(validation.overlapping_pairs, (("a", "b"),))

    def test_validator_flags_missing_neighbor_references(self) -> None:
        topology = _topology(
            _square_cell("a", 0, 0, neighbors=("b",)),
            _square_cell("b", 1, 0, neighbors=("a",)),
            revision="fixture-missing-neighbor",
        )
        object.__setattr__(topology, "_index_by_id", {"a": 0})

        validation = validate_topology(topology)

        self.assertFalse(validation.is_valid)
        self.assertEqual(validation.missing_neighbor_cells, (("a", "b"),))

    def test_validator_flags_duplicate_neighbor_ids(self) -> None:
        topology = _topology(
            _square_cell("a", 0, 0, neighbors=("b", "b")),
            _square_cell("b", 1, 0, neighbors=("a",)),
            revision="fixture-duplicate-neighbors",
        )

        validation = validate_topology(topology)

        self.assertFalse(validation.is_valid)
        self.assertEqual(validation.duplicate_neighbor_cells, ("a",))

    def test_validator_flags_disconnected_graph_components(self) -> None:
        topology = _topology(
            _square_cell("a", 0, 0, neighbors=("b",)),
            _square_cell("b", 1, 0, neighbors=("a",)),
            _square_cell("c", 4, 0),
            revision="fixture-disconnected",
        )

        validation = validate_topology(topology)

        self.assertFalse(validation.is_valid)
        self.assertEqual(validation.disconnected_components, (("a", "b"), ("c",)))

    def test_validator_flags_edge_multiplicity_issues(self) -> None:
        topology = _topology(
            _square_cell("a", 0, 0),
            _square_cell("b", 1, 0),
            _polygon_cell(
                "c",
                ((1.0, 0.0), (1.0, 1.0), (2.0, 0.5)),
                kind="triangle",
            ),
            revision="fixture-edge-multiplicity",
        )

        validation = validate_topology(topology, check_overlaps=False)

        self.assertFalse(validation.is_valid)
        self.assertEqual(len(validation.edge_multiplicity_issues), 1)
        self.assertEqual(validation.edge_multiplicity_issues[0].multiplicity, 3)
        self.assertEqual(validation.edge_multiplicity_issues[0].owners, ("a", "b", "c"))

    def test_validator_flags_surface_holes(self) -> None:
        neighbor_map = {
            "c00": ("c10", "c01"),
            "c10": ("c00", "c20"),
            "c20": ("c10", "c21"),
            "c01": ("c00", "c02"),
            "c21": ("c20", "c22"),
            "c02": ("c01", "c12"),
            "c12": ("c02", "c22"),
            "c22": ("c12", "c21"),
        }
        topology = _topology(
            *(
                _square_cell(cell_id, int(cell_id[1]), int(cell_id[2]), neighbors=neighbors)
                for cell_id, neighbors in neighbor_map.items()
            ),
            revision="fixture-hole",
        )

        validation = validate_topology(topology)

        self.assertFalse(validation.is_valid)
        self.assertEqual(validation.surface_component_count, 1)
        self.assertEqual(validation.hole_count, 1)


if __name__ == "__main__":
    unittest.main()
