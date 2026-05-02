from collections import Counter
import sys
import unittest
from pathlib import Path

try:
    from backend.rules.conway import ConwayLifeRule
    from backend.rules.life_b2s23 import LifeB2S23Rule
    from backend.rules.penrose_greenberg_hastings import PenroseGreenbergHastingsRule
    from backend.simulation.engine import SimulationEngine
    from backend.simulation.aperiodic_family_manifest import (
        SHIELD_SHIELD_KIND,
        SHIELD_SQUARE_KIND,
        SHIELD_TRIANGLE_KIND,
    )
    from backend.simulation.penrose import build_penrose_patch
    from backend.simulation.topology import (
        CHAIR_GEOMETRY,
        DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
        HAT_MONOTILE_GEOMETRY,
        PENROSE_GEOMETRY,
        PENROSE_VERTEX_GEOMETRY,
        PINWHEEL_GEOMETRY,
        ROBINSON_TRIANGLES_GEOMETRY,
        SHIELD_GEOMETRY,
        SPECTRE_GEOMETRY,
        SPHINX_GEOMETRY,
        TAYLOR_SOCOLAR_GEOMETRY,
        TUEBINGEN_TRIANGLE_GEOMETRY,
        build_topology,
        empty_board,
    )
    from backend.simulation.topology_validation import validate_topology
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.rules.conway import ConwayLifeRule
    from backend.rules.life_b2s23 import LifeB2S23Rule
    from backend.rules.penrose_greenberg_hastings import PenroseGreenbergHastingsRule
    from backend.simulation.engine import SimulationEngine
    from backend.simulation.aperiodic_family_manifest import (
        SHIELD_SHIELD_KIND,
        SHIELD_SQUARE_KIND,
        SHIELD_TRIANGLE_KIND,
    )
    from backend.simulation.penrose import build_penrose_patch
    from backend.simulation.topology import (
        CHAIR_GEOMETRY,
        DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
        HAT_MONOTILE_GEOMETRY,
        PENROSE_GEOMETRY,
        PENROSE_VERTEX_GEOMETRY,
        PINWHEEL_GEOMETRY,
        ROBINSON_TRIANGLES_GEOMETRY,
        SHIELD_GEOMETRY,
        SPECTRE_GEOMETRY,
        SPHINX_GEOMETRY,
        TAYLOR_SOCOLAR_GEOMETRY,
        TUEBINGEN_TRIANGLE_GEOMETRY,
        build_topology,
        empty_board,
    )
    from backend.simulation.topology_validation import validate_topology


class SimulationTopologyAperiodicTests(unittest.TestCase):
    def test_penrose_topology_is_deterministic_and_contains_geometry_metadata(self) -> None:
        left = build_topology(PENROSE_GEOMETRY, 0, 0, patch_depth=3)
        right = build_topology(PENROSE_GEOMETRY, 0, 0, patch_depth=3)

        self.assertEqual(left.cell_count, right.cell_count)
        self.assertEqual([cell.id for cell in left.cells], [cell.id for cell in right.cells])
        self.assertTrue(all(cell.kind in {"thick-rhomb", "thin-rhomb"} for cell in left.cells))
        self.assertTrue(all(cell.center is not None for cell in left.cells))
        self.assertTrue(
            all(cell.vertices is not None and len(cell.vertices) == 4 for cell in left.cells)
        )
        self.assertGreater(left.cell_count, 25)

    def test_penrose_topology_neighbors_are_symmetric_and_depth_grows_monotonically(self) -> None:
        shallow = build_topology(PENROSE_GEOMETRY, 0, 0, patch_depth=1)
        deep = build_topology(PENROSE_GEOMETRY, 0, 0, patch_depth=4)

        self.assertGreater(deep.cell_count, shallow.cell_count)
        for cell in deep.cells:
            self.assertEqual(len(cell.neighbors), len(set(cell.neighbors)))
            self.assertLessEqual(len(cell.neighbors), 4)
            for neighbor_id in cell.neighbors:
                assert neighbor_id is not None
                self.assertIn(cell.id, deep.get_cell(neighbor_id).neighbors)

    def test_spectre_topology_is_deterministic_and_depth_grows_monotonically(self) -> None:
        shallow = build_topology(SPECTRE_GEOMETRY, 0, 0, patch_depth=1)
        deep = build_topology(SPECTRE_GEOMETRY, 0, 0, patch_depth=3)
        repeated = build_topology(SPECTRE_GEOMETRY, 0, 0, patch_depth=3)

        self.assertEqual([cell.id for cell in deep.cells], [cell.id for cell in repeated.cells])
        self.assertGreater(deep.cell_count, shallow.cell_count)
        self.assertTrue(all(cell.kind == "spectre" for cell in deep.cells))
        self.assertTrue(all(cell.center is not None for cell in deep.cells))
        self.assertTrue(
            all(cell.vertices is not None and len(cell.vertices) == 14 for cell in deep.cells)
        )
        for cell in deep.cells:
            self.assertEqual(len(cell.neighbors), len(set(cell.neighbors)))
            for neighbor_id in cell.neighbors:
                assert neighbor_id is not None
                self.assertIn(cell.id, deep.get_cell(neighbor_id).neighbors)

    def test_taylor_socolar_topology_is_deterministic_and_depth_grows_monotonically(self) -> None:
        shallow = build_topology(TAYLOR_SOCOLAR_GEOMETRY, 0, 0, patch_depth=1)
        deep = build_topology(TAYLOR_SOCOLAR_GEOMETRY, 0, 0, patch_depth=3)
        repeated = build_topology(TAYLOR_SOCOLAR_GEOMETRY, 0, 0, patch_depth=3)

        self.assertEqual([cell.id for cell in deep.cells], [cell.id for cell in repeated.cells])
        self.assertGreater(deep.cell_count, shallow.cell_count)
        self.assertTrue(all(cell.kind == "taylor-half-hex" for cell in deep.cells))
        self.assertTrue(all(cell.center is not None for cell in deep.cells))
        self.assertTrue(
            all(cell.vertices is not None and len(cell.vertices) == 4 for cell in deep.cells)
        )
        for cell in deep.cells:
            self.assertEqual(len(cell.neighbors), len(set(cell.neighbors)))
            for neighbor_id in cell.neighbors:
                assert neighbor_id is not None
                self.assertIn(cell.id, deep.get_cell(neighbor_id).neighbors)

    def test_sphinx_topology_is_deterministic_and_depth_grows_monotonically(self) -> None:
        shallow = build_topology(SPHINX_GEOMETRY, 0, 0, patch_depth=1)
        deep = build_topology(SPHINX_GEOMETRY, 0, 0, patch_depth=3)
        repeated = build_topology(SPHINX_GEOMETRY, 0, 0, patch_depth=3)

        self.assertEqual([cell.id for cell in deep.cells], [cell.id for cell in repeated.cells])
        self.assertGreater(deep.cell_count, shallow.cell_count)
        self.assertTrue(all(cell.kind == "sphinx" for cell in deep.cells))
        self.assertTrue(all(cell.center is not None for cell in deep.cells))
        self.assertTrue(
            all(cell.vertices is not None and len(cell.vertices) == 8 for cell in deep.cells)
        )
        for cell in deep.cells:
            self.assertEqual(len(cell.neighbors), len(set(cell.neighbors)))
            for neighbor_id in cell.neighbors:
                assert neighbor_id is not None
                self.assertIn(cell.id, deep.get_cell(neighbor_id).neighbors)

    def test_chair_topology_is_deterministic_and_depth_grows_monotonically(self) -> None:
        seed = build_topology(CHAIR_GEOMETRY, 0, 0, patch_depth=0)
        shallow = build_topology(CHAIR_GEOMETRY, 0, 0, patch_depth=1)
        medium = build_topology(CHAIR_GEOMETRY, 0, 0, patch_depth=2)
        deep = build_topology(CHAIR_GEOMETRY, 0, 0, patch_depth=3)
        repeated = build_topology(CHAIR_GEOMETRY, 0, 0, patch_depth=3)

        self.assertEqual(seed.cell_count, 1)
        self.assertEqual(shallow.cell_count, 4)
        self.assertEqual(medium.cell_count, 16)
        self.assertEqual(deep.cell_count, 64)
        self.assertEqual([cell.id for cell in deep.cells], [cell.id for cell in repeated.cells])
        self.assertGreater(deep.cell_count, shallow.cell_count)
        self.assertTrue(all(cell.kind == "chair" for cell in deep.cells))
        self.assertTrue(all(cell.center is not None for cell in deep.cells))
        self.assertTrue(
            all(cell.vertices is not None and len(cell.vertices) == 8 for cell in deep.cells)
        )
        self.assertTrue(all(cell.orientation_token is not None for cell in deep.cells))
        self.assertEqual(
            Counter(cell.orientation_token for cell in deep.cells),
            Counter({"0": 20, "1": 16, "2": 12, "3": 16}),
        )
        for cell in deep.cells:
            self.assertEqual(len(cell.neighbors), len(set(cell.neighbors)))
            for neighbor_id in cell.neighbors:
                assert neighbor_id is not None
                self.assertIn(cell.id, deep.get_cell(neighbor_id).neighbors)

    def test_robinson_triangles_topology_is_deterministic_and_depth_grows_monotonically(
        self,
    ) -> None:
        shallow = build_topology(ROBINSON_TRIANGLES_GEOMETRY, 0, 0, patch_depth=1)
        deep = build_topology(ROBINSON_TRIANGLES_GEOMETRY, 0, 0, patch_depth=3)
        repeated = build_topology(ROBINSON_TRIANGLES_GEOMETRY, 0, 0, patch_depth=3)

        self.assertEqual([cell.id for cell in deep.cells], [cell.id for cell in repeated.cells])
        self.assertGreater(deep.cell_count, shallow.cell_count)
        self.assertEqual({cell.kind for cell in deep.cells}, {"robinson-thick", "robinson-thin"})
        self.assertTrue(all(cell.center is not None for cell in deep.cells))
        self.assertTrue(
            all(cell.vertices is not None and len(cell.vertices) == 3 for cell in deep.cells)
        )
        for cell in deep.cells:
            self.assertEqual(len(cell.neighbors), len(set(cell.neighbors)))
            for neighbor_id in cell.neighbors:
                assert neighbor_id is not None
                self.assertIn(cell.id, deep.get_cell(neighbor_id).neighbors)

    def test_new_aperiodic_wave_topologies_are_deterministic_and_emit_metadata(self) -> None:
        cases = (
            (HAT_MONOTILE_GEOMETRY, {"hat"}, 2),
            (TUEBINGEN_TRIANGLE_GEOMETRY, {"tuebingen-thick", "tuebingen-thin"}, 3),
            (
                DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
                {"dodecagonal-square-triangle-square", "dodecagonal-square-triangle-triangle"},
                3,
            ),
            (SHIELD_GEOMETRY, {"shield-shield", "shield-square", "shield-triangle"}, 3),
            (PINWHEEL_GEOMETRY, {"pinwheel-triangle"}, 3),
        )

        for geometry, expected_kinds, depth in cases:
            with self.subTest(geometry=geometry):
                shallow = build_topology(geometry, 0, 0, patch_depth=1)
                deep = build_topology(geometry, 0, 0, patch_depth=depth)
                repeated = build_topology(geometry, 0, 0, patch_depth=depth)

                self.assertEqual(
                    [cell.id for cell in deep.cells], [cell.id for cell in repeated.cells]
                )
                self.assertGreater(deep.cell_count, shallow.cell_count)
                self.assertEqual({cell.kind for cell in deep.cells}, expected_kinds)
                self.assertTrue(all(cell.center is not None for cell in deep.cells))
                self.assertTrue(all(cell.vertices for cell in deep.cells))
                self.assertTrue(all(cell.tile_family is not None for cell in deep.cells))
                if geometry in {
                    HAT_MONOTILE_GEOMETRY,
                    TUEBINGEN_TRIANGLE_GEOMETRY,
                    PINWHEEL_GEOMETRY,
                }:
                    self.assertTrue(all(cell.orientation_token is not None for cell in deep.cells))
                if geometry == DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY:
                    self.assertTrue(all(cell.orientation_token is not None for cell in deep.cells))
                if geometry in {
                    HAT_MONOTILE_GEOMETRY,
                    TUEBINGEN_TRIANGLE_GEOMETRY,
                    PINWHEEL_GEOMETRY,
                    DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
                }:
                    self.assertTrue(
                        all(
                            cell.chirality_token is not None
                            for cell in deep.cells
                            if cell.kind != "dodecagonal-square-triangle-square"
                        )
                    )
                if geometry == SHIELD_GEOMETRY:
                    self.assertTrue(all(cell.orientation_token is not None for cell in deep.cells))
                    self.assertGreaterEqual(
                        len(
                            {
                                cell.orientation_token
                                for cell in deep.cells
                                if cell.orientation_token is not None
                            }
                        ),
                        8,
                    )
                for cell in deep.cells:
                    self.assertEqual(len(cell.neighbors), len(set(cell.neighbors)))
                    for neighbor_id in cell.neighbors:
                        assert neighbor_id is not None
                        self.assertIn(cell.id, deep.get_cell(neighbor_id).neighbors)

    def test_dodecagonal_square_triangle_scales_to_arbitrary_depth(self) -> None:
        depth_seven = build_topology(DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY, 0, 0, patch_depth=7)
        depth_eleven = build_topology(DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY, 0, 0, patch_depth=11)
        repeated_depth_eleven = build_topology(
            DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY, 0, 0, patch_depth=11
        )
        depth_forty = build_topology(DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY, 0, 0, patch_depth=40)
        repeated_depth_forty = build_topology(
            DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY, 0, 0, patch_depth=40
        )
        depth_one_hundred = build_topology(
            DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY, 0, 0, patch_depth=100
        )
        validation = validate_topology(depth_eleven)

        self.assertEqual(depth_eleven.patch_depth, 11)
        self.assertGreater(depth_eleven.cell_count, depth_seven.cell_count)
        self.assertTrue(validation.is_valid, validation.summary_lines())
        self.assertEqual(
            [cell.id for cell in depth_eleven.cells],
            [cell.id for cell in repeated_depth_eleven.cells],
        )
        self.assertEqual(depth_forty.patch_depth, 40)
        self.assertGreater(depth_forty.cell_count, depth_eleven.cell_count)
        self.assertEqual(
            [cell.id for cell in depth_forty.cells],
            [cell.id for cell in repeated_depth_forty.cells],
        )
        # The new decorated 3.12.12 generator has no intrinsic depth cap; deeper
        # patches just keep growing.
        self.assertEqual(depth_one_hundred.patch_depth, 100)
        self.assertGreater(depth_one_hundred.cell_count, depth_forty.cell_count)
        self.assertTrue(all(cell.orientation_token is not None for cell in depth_eleven.cells))
        self.assertTrue(
            all(
                cell.chirality_token is not None
                for cell in depth_eleven.cells
                if cell.kind != "dodecagonal-square-triangle-square"
            )
        )

    def test_dodecagonal_square_triangle_runtime_emits_decorated_supercell_ids(
        self,
    ) -> None:
        topology = build_topology(DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY, 0, 0, patch_depth=3)

        self.assertTrue(all(cell.id.startswith("dst:dec:") for cell in topology.cells))

    def test_shield_topology_uses_exact_symbolic_substitution_depth(self) -> None:
        depth_zero = build_topology(SHIELD_GEOMETRY, 0, 0, patch_depth=0)
        depth_one = build_topology(SHIELD_GEOMETRY, 0, 0, patch_depth=1)
        depth_three = build_topology(SHIELD_GEOMETRY, 0, 0, patch_depth=3)
        repeated_depth_three = build_topology(SHIELD_GEOMETRY, 0, 0, patch_depth=3)

        self.assertEqual(depth_zero.cell_count, 1)
        self.assertEqual(depth_one.cell_count, 13)
        self.assertEqual(depth_three.cell_count, 151)
        self.assertEqual(
            [cell.id for cell in depth_three.cells],
            [cell.id for cell in repeated_depth_three.cells],
        )
        self.assertEqual(
            {cell.kind for cell in depth_zero.cells},
            {SHIELD_SHIELD_KIND},
        )
        self.assertEqual(
            {cell.kind for cell in depth_one.cells},
            {SHIELD_SQUARE_KIND, SHIELD_TRIANGLE_KIND},
        )
        self.assertGreaterEqual(
            len(
                {
                    cell.orientation_token
                    for cell in depth_three.cells
                    if cell.orientation_token is not None
                }
            ),
            12,
        )
        self.assertGreaterEqual(
            len(
                {
                    cell.chirality_token
                    for cell in depth_three.cells
                    if cell.chirality_token is not None
                }
            ),
            2,
        )

    def test_penrose_vertex_topology_is_symmetric_duplicate_free_and_larger_than_edge_neighbors(
        self,
    ) -> None:
        edge = build_topology(PENROSE_GEOMETRY, 0, 0, patch_depth=3)
        vertex = build_topology(PENROSE_VERTEX_GEOMETRY, 0, 0, patch_depth=3)

        self.assertEqual([cell.id for cell in edge.cells], [cell.id for cell in vertex.cells])
        self.assertEqual(edge.width, vertex.width)
        self.assertEqual(edge.height, vertex.height)

        interior_candidates = []
        for edge_cell in edge.cells:
            vertex_cell = vertex.get_cell(edge_cell.id)
            self.assertEqual(len(vertex_cell.neighbors), len(set(vertex_cell.neighbors)))
            self.assertGreaterEqual(len(vertex_cell.neighbors), len(edge_cell.neighbors))
            for neighbor_id in vertex_cell.neighbors:
                assert neighbor_id is not None
                self.assertIn(vertex_cell.id, vertex.get_cell(neighbor_id).neighbors)
            if len(edge_cell.neighbors) >= 4 and len(vertex_cell.neighbors) > len(
                edge_cell.neighbors
            ):
                interior_candidates.append((edge_cell, vertex_cell))

        self.assertTrue(interior_candidates)

    def test_penrose_vertex_life_steps_with_b3_s23_over_vertex_neighbors(self) -> None:
        engine = SimulationEngine()
        rule = ConwayLifeRule()
        board = empty_board(PENROSE_VERTEX_GEOMETRY, 0, 0, patch_depth=2)

        target = next(cell for cell in board.topology.cells if len(cell.neighbors) >= 5)
        for neighbor_id in target.neighbors[:3]:
            assert neighbor_id is not None
            board.set_state_for(neighbor_id, 1)

        next_board = engine.step_board(board, rule)
        self.assertEqual(next_board.state_for(target.id), 1)

    def test_penrose_board_steps_with_penrose_life_rule(self) -> None:
        engine = SimulationEngine()
        rule = LifeB2S23Rule()
        board = empty_board(PENROSE_GEOMETRY, 0, 0, patch_depth=2)

        target = next(
            cell
            for cell in board.topology.cells
            if cell.kind == "thin-rhomb" and len(cell.neighbors) >= 3
        )
        for neighbor_id in target.neighbors[:2]:
            assert neighbor_id is not None
            board.set_state_for(neighbor_id, 1)

        next_board = engine.step_board(board, rule)
        self.assertEqual(next_board.state_for(target.id), 1)

    def test_penrose_board_steps_with_greenberg_hastings_rule(self) -> None:
        engine = SimulationEngine()
        rule = PenroseGreenbergHastingsRule()
        board = empty_board(PENROSE_GEOMETRY, 0, 0, patch_depth=2)

        target = next(cell for cell in board.topology.cells if len(cell.neighbors) >= 2)
        excited_neighbor_id = target.neighbors[0]
        other_neighbor_id = target.neighbors[1]
        assert excited_neighbor_id is not None
        assert other_neighbor_id is not None

        board.set_state_for(excited_neighbor_id, rule.EXCITED)
        board.set_state_for(other_neighbor_id, rule.REFRACTORY)

        next_board = engine.step_board(board, rule)
        self.assertEqual(next_board.state_for(target.id), rule.EXCITED)
        self.assertEqual(next_board.state_for(excited_neighbor_id), rule.TRAILING)
        self.assertEqual(next_board.state_for(other_neighbor_id), rule.RESTING)

    def test_penrose_greenberg_hastings_cycles_through_trail_and_refractory(self) -> None:
        engine = SimulationEngine()
        rule = PenroseGreenbergHastingsRule()
        board = empty_board(PENROSE_GEOMETRY, 0, 0, patch_depth=1)

        seed = board.topology.cells[0].id
        board.set_state_for(seed, rule.EXCITED)

        trailing = engine.step_board(board, rule)
        refractory = engine.step_board(trailing, rule)
        resting = engine.step_board(refractory, rule)

        self.assertEqual(trailing.state_for(seed), rule.TRAILING)
        self.assertEqual(refractory.state_for(seed), rule.REFRACTORY)
        self.assertEqual(resting.state_for(seed), rule.RESTING)

    def test_build_penrose_patch_rejects_unsupported_adjacency_mode(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported Penrose adjacency mode"):
            build_penrose_patch(2, adjacency_mode="diagonal")


if __name__ == "__main__":
    unittest.main()
