from collections import Counter
import sys
import unittest
from pathlib import Path

try:
    from backend.rules.archlife488 import ArchLife488Rule
    from backend.rules.archlife_extended import (
        ArchLife31212Rule,
        ArchLife33336Rule,
        ArchLife33344Rule,
        ArchLife33434Rule,
        ArchLife3464Rule,
        ArchLife4612Rule,
    )
    from backend.rules.conway import ConwayLifeRule
    from backend.rules.kagome_life import KagomeLifeRule
    from backend.rules.life_b2s23 import LifeB2S23Rule
    from backend.rules.penrose_greenberg_hastings import PenroseGreenbergHastingsRule
    from backend.simulation.engine import SimulationEngine
    from backend.simulation.penrose import build_penrose_patch
    from backend.simulation.topology import (
        ARCHIMEDEAN_488_GEOMETRY,
        DELTOIDAL_TRIHEXAGONAL_GEOMETRY,
        FLORET_PENTAGONAL_GEOMETRY,
        KAGOME_GEOMETRY,
        PENROSE_GEOMETRY,
        PENROSE_VERTEX_GEOMETRY,
        PRISMATIC_PENTAGONAL_GEOMETRY,
        RHOMBILLE_GEOMETRY,
        SNUB_SQUARE_DUAL_GEOMETRY,
        SPECTRE_GEOMETRY,
        TAYLOR_SOCOLAR_GEOMETRY,
        TETRAKIS_SQUARE_GEOMETRY,
        TRIAKIS_TRIANGULAR_GEOMETRY,
        build_topology,
        empty_board,
    )
    from backend.simulation.topology_validation import validate_topology
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.rules.archlife488 import ArchLife488Rule
    from backend.rules.archlife_extended import (
        ArchLife31212Rule,
        ArchLife33336Rule,
        ArchLife33344Rule,
        ArchLife33434Rule,
        ArchLife3464Rule,
        ArchLife4612Rule,
    )
    from backend.rules.conway import ConwayLifeRule
    from backend.rules.kagome_life import KagomeLifeRule
    from backend.rules.life_b2s23 import LifeB2S23Rule
    from backend.rules.penrose_greenberg_hastings import PenroseGreenbergHastingsRule
    from backend.simulation.engine import SimulationEngine
    from backend.simulation.penrose import build_penrose_patch
    from backend.simulation.topology import (
        ARCHIMEDEAN_488_GEOMETRY,
        DELTOIDAL_TRIHEXAGONAL_GEOMETRY,
        FLORET_PENTAGONAL_GEOMETRY,
        KAGOME_GEOMETRY,
        PENROSE_GEOMETRY,
        PENROSE_VERTEX_GEOMETRY,
        PRISMATIC_PENTAGONAL_GEOMETRY,
        RHOMBILLE_GEOMETRY,
        SNUB_SQUARE_DUAL_GEOMETRY,
        SPECTRE_GEOMETRY,
        TAYLOR_SOCOLAR_GEOMETRY,
        TETRAKIS_SQUARE_GEOMETRY,
        TRIAKIS_TRIANGULAR_GEOMETRY,
        build_topology,
        empty_board,
    )
    from backend.simulation.topology_validation import validate_topology


class SimulationTopologyTests(unittest.TestCase):
    def test_neighbor_index_cache_matches_neighbor_id_ordering(self) -> None:
        cases = [
            ("square", 4, 3),
            ("hex", 4, 3),
            ("triangle", 5, 4),
            (ARCHIMEDEAN_488_GEOMETRY, 3, 3),
            (KAGOME_GEOMETRY, 4, 3),
            (RHOMBILLE_GEOMETRY, 3, 3),
            (TETRAKIS_SQUARE_GEOMETRY, 3, 3),
            (TRIAKIS_TRIANGULAR_GEOMETRY, 3, 3),
            (DELTOIDAL_TRIHEXAGONAL_GEOMETRY, 3, 3),
            (PRISMATIC_PENTAGONAL_GEOMETRY, 3, 3),
            (FLORET_PENTAGONAL_GEOMETRY, 3, 3),
            (SNUB_SQUARE_DUAL_GEOMETRY, 3, 3),
            (SPECTRE_GEOMETRY, 0, 0),
            (TAYLOR_SOCOLAR_GEOMETRY, 0, 0),
            (PENROSE_GEOMETRY, 0, 0),
            (PENROSE_VERTEX_GEOMETRY, 0, 0),
        ]

        for geometry, width, height in cases:
            with self.subTest(geometry=geometry):
                topology = build_topology(
                    geometry,
                    width,
                    height,
                    patch_depth=3 if geometry in {SPECTRE_GEOMETRY, TAYLOR_SOCOLAR_GEOMETRY, PENROSE_GEOMETRY, PENROSE_VERTEX_GEOMETRY} else None,
                )
                for index, cell in enumerate(topology.cells):
                    expected = tuple(
                        -1 if neighbor_id is None else topology.index_for(neighbor_id)
                        for neighbor_id in cell.neighbors
                    )
                    self.assertEqual(topology.neighbor_indexes_for(index), expected)

    def test_archimedean_topology_has_deterministic_counts_and_order(self) -> None:
        topology = build_topology(ARCHIMEDEAN_488_GEOMETRY, 5, 5)

        self.assertEqual(topology.cell_count, (5 * 5) + (6 * 6))
        self.assertEqual([cell.id for cell in topology.cells[:5]], [
            'o:0:0',
            'o:1:0',
            'o:2:0',
            'o:3:0',
            'o:4:0',
        ])
        self.assertEqual(topology.cells[24].id, 'o:4:4')
        self.assertEqual(topology.cells[25].id, 's:0:0')
        self.assertEqual(topology.cells[-1].id, 's:5:5')
        self.assertTrue(topology.has_cell('o:3:2'))
        self.assertTrue(topology.has_cell('s:4:1'))
        self.assertEqual(topology.get_cell('o:3:2').kind, 'octagon')
        self.assertEqual(topology.get_cell('s:4:1').kind, 'square')

    def test_archimedean_topology_neighbor_degrees_match_cell_kind_and_boundary(self) -> None:
        topology = build_topology(ARCHIMEDEAN_488_GEOMETRY, 5, 5)

        self.assertEqual(len(topology.get_cell('o:2:2').neighbors), 8)
        self.assertEqual(len(topology.get_cell('o:0:0').neighbors), 6)
        self.assertEqual(len(topology.get_cell('s:2:2').neighbors), 4)
        self.assertEqual(len(topology.get_cell('s:0:0').neighbors), 1)
        self.assertEqual(
            topology.get_cell('s:2:2').neighbors,
            ('o:1:1', 'o:2:1', 'o:2:2', 'o:1:2'),
        )

    def test_archimedean_board_steps_square_and_octagon_births(self) -> None:
        engine = SimulationEngine()
        rule = ArchLife488Rule()

        square_birth_board = empty_board(ARCHIMEDEAN_488_GEOMETRY, 5, 5)
        square_birth_board.set_state_for('o:1:1', 1)
        square_birth_board.set_state_for('o:2:1', 1)
        next_square_board = engine.step_board(square_birth_board, rule)

        self.assertEqual(next_square_board.state_for('s:2:2'), 1)

        octagon_birth_board = empty_board(ARCHIMEDEAN_488_GEOMETRY, 5, 5)
        octagon_birth_board.set_state_for('o:2:1', 1)
        octagon_birth_board.set_state_for('o:3:2', 1)
        octagon_birth_board.set_state_for('s:2:2', 1)
        next_octagon_board = engine.step_board(octagon_birth_board, rule)

        self.assertEqual(next_octagon_board.state_for('o:2:2'), 1)

    def test_kagome_topology_has_deterministic_counts_and_order(self) -> None:
        topology = build_topology(KAGOME_GEOMETRY, 4, 3)

        self.assertEqual(topology.cell_count, 4 * 3 * 3)
        self.assertEqual([cell.id for cell in topology.cells[:4]], [
            'h:0:0',
            'h:1:0',
            'h:2:0',
            'h:3:0',
        ])
        self.assertEqual(topology.cells[12].id, 'tu:0:0')
        self.assertEqual(topology.cells[13].id, 'tu:1:0')
        self.assertEqual(topology.cells[24].id, 'td:0:0')
        self.assertEqual(topology.cells[-1].id, 'td:3:2')
        self.assertEqual(topology.get_cell('h:2:1').kind, 'hexagon')
        self.assertEqual(topology.get_cell('tu:2:1').kind, 'triangle-up')
        self.assertEqual(topology.get_cell('td:2:1').kind, 'triangle-down')

    def test_kagome_topology_neighbor_degrees_match_cell_kind_and_boundary(self) -> None:
        topology = build_topology(KAGOME_GEOMETRY, 5, 5)

        self.assertEqual(len(topology.get_cell('h:2:2').neighbors), 6)
        self.assertEqual(len(topology.get_cell('h:0:0').neighbors), 3)
        self.assertEqual(len(topology.get_cell('tu:2:2').neighbors), 3)
        self.assertEqual(len(topology.get_cell('tu:0:0').neighbors), 1)
        self.assertEqual(len(topology.get_cell('td:0:0').neighbors), 2)
        self.assertTrue(all(
            topology.get_cell(neighbor_id).kind.startswith('triangle')
            for neighbor_id in topology.get_cell('h:2:2').neighbors
            if neighbor_id is not None
        ))
        self.assertTrue(all(
            topology.get_cell(neighbor_id).kind == 'hexagon'
            for neighbor_id in topology.get_cell('tu:2:2').neighbors
            if neighbor_id is not None
        ))

    def test_kagome_board_steps_triangle_and_hexagon_births(self) -> None:
        engine = SimulationEngine()
        rule = KagomeLifeRule()

        triangle_birth_board = empty_board(KAGOME_GEOMETRY, 5, 5)
        triangle_birth_board.set_state_for('h:2:1', 1)
        triangle_birth_board.set_state_for('h:2:2', 1)
        next_triangle_board = engine.step_board(triangle_birth_board, rule)
        self.assertEqual(next_triangle_board.state_for('tu:2:2'), 1)

        hexagon_birth_board = empty_board(KAGOME_GEOMETRY, 5, 5)
        hexagon_birth_board.set_state_for('tu:2:2', 1)
        hexagon_birth_board.set_state_for('td:2:2', 1)
        hexagon_birth_board.set_state_for('tu:2:3', 1)
        next_hexagon_board = engine.step_board(hexagon_birth_board, rule)
        self.assertEqual(next_hexagon_board.state_for('h:2:2'), 1)

    def test_new_archimedean_topologies_are_deterministic_and_slot_annotated(self) -> None:
        cases = {
            "archimedean-3-12-12": {"triangle", "dodecagon"},
            "archimedean-3-4-6-4": {"triangle", "square", "hexagon"},
            "archimedean-4-6-12": {"square", "hexagon", "dodecagon"},
            "archimedean-3-3-4-3-4": {"triangle", "square"},
            "archimedean-3-3-3-4-4": {"triangle", "square"},
            "archimedean-3-3-3-3-6": {"triangle", "hexagon"},
        }

        for geometry, expected_kinds in cases.items():
            with self.subTest(geometry=geometry):
                left = build_topology(geometry, 1, 1)
                right = build_topology(geometry, 1, 1)

                self.assertEqual(left.cell_count, right.cell_count)
                self.assertEqual([cell.id for cell in left.cells], [cell.id for cell in right.cells])
                self.assertEqual({cell.kind for cell in left.cells}, expected_kinds)
                self.assertTrue(all(cell.slot for cell in left.cells))
                self.assertTrue(all(cell.center is not None for cell in left.cells))
                self.assertTrue(all(cell.vertices is not None for cell in left.cells))
                for cell in left.cells:
                    self.assertEqual(len(cell.neighbors), len(set(cell.neighbors)))
                    for neighbor_id in cell.neighbors:
                        assert neighbor_id is not None
                        self.assertIn(cell.id, left.get_cell(neighbor_id).neighbors)

    def test_build_topology_reuses_cached_identity_and_serialized_payload(self) -> None:
        topology = build_topology("archimedean-3-3-3-3-6", 4, 3)
        same_topology = build_topology("archimedean-3-3-3-3-6", 4, 3)
        different_topology = build_topology("archimedean-3-3-3-3-6", 5, 3)

        self.assertIs(topology, same_topology)
        self.assertIsNot(topology, different_topology)
        self.assertIs(topology.to_dict(), topology.to_dict())

    def test_topology_public_facade_preserves_builder_and_board_helpers(self) -> None:
        topology = build_topology("square", 2, 2)
        empty = empty_board("square", 2, 2)

        self.assertEqual(topology.cell_count, 4)
        self.assertEqual(empty.cell_states, [0, 0, 0, 0])
        self.assertEqual(
            build_topology("square", 2, 2).cells[0].id,
            "c:0:0",
        )

    def test_new_periodic_mixed_topologies_are_deterministic_and_single_kind_annotated(self) -> None:
        cases = {
            RHOMBILLE_GEOMETRY: {"rhombus"},
            TETRAKIS_SQUARE_GEOMETRY: {"triangle"},
            TRIAKIS_TRIANGULAR_GEOMETRY: {"triangle"},
            DELTOIDAL_TRIHEXAGONAL_GEOMETRY: {"kite"},
            PRISMATIC_PENTAGONAL_GEOMETRY: {"pentagon"},
            FLORET_PENTAGONAL_GEOMETRY: {"pentagon"},
            SNUB_SQUARE_DUAL_GEOMETRY: {"pentagon"},
        }

        for geometry, expected_kinds in cases.items():
            with self.subTest(geometry=geometry):
                left = build_topology(geometry, 1, 1)
                right = build_topology(geometry, 1, 1)

                self.assertEqual(left.cell_count, right.cell_count)
                self.assertEqual([cell.id for cell in left.cells], [cell.id for cell in right.cells])
                self.assertEqual({cell.kind for cell in left.cells}, expected_kinds)
                self.assertTrue(all(cell.slot for cell in left.cells))
                self.assertTrue(all(cell.center is not None for cell in left.cells))
                self.assertTrue(all(cell.vertices is not None for cell in left.cells))
                for cell in left.cells:
                    self.assertEqual(len(cell.neighbors), len(set(cell.neighbors)))
                    for neighbor_id in cell.neighbors:
                        assert neighbor_id is not None
                        self.assertIn(cell.id, left.get_cell(neighbor_id).neighbors)

    def test_snub_square_unit_cell_has_expected_triangle_square_mix(self) -> None:
        topology = build_topology("archimedean-3-3-4-3-4", 1, 1)

        self.assertEqual(topology.cell_count, 12)
        self.assertEqual(
            Counter(cell.kind for cell in topology.cells),
            Counter({"triangle": 8, "square": 4}),
        )

    def test_snub_square_interior_edges_are_fully_shared(self) -> None:
        topology = build_topology("archimedean-3-3-4-3-4", 3, 3)
        validation = validate_topology(topology)

        self.assertTrue(validation.is_valid, "\n".join(validation.summary_lines()))
        self.assertFalse(validation.edge_multiplicity_issues)
        self.assertEqual(validation.hole_count, 0)

    def test_new_archimedean_rules_step_kind_specific_births(self) -> None:
        engine = SimulationEngine()
        cases = [
            ("archimedean-3-12-12", ArchLife31212Rule(), "triangle", 2),
            ("archimedean-3-4-6-4", ArchLife3464Rule(), "hexagon", 3),
            ("archimedean-4-6-12", ArchLife4612Rule(), "dodecagon", 4),
            ("archimedean-3-3-4-3-4", ArchLife33434Rule(), "square", 3),
            ("archimedean-3-3-3-4-4", ArchLife33344Rule(), "square", 2),
            ("archimedean-3-3-3-3-6", ArchLife33336Rule(), "hexagon", 4),
        ]

        for geometry, rule, kind, live_neighbor_count in cases:
            with self.subTest(geometry=geometry):
                board = empty_board(geometry, 1, 1)
                target = next(cell for cell in board.topology.cells if cell.kind == kind and len(cell.neighbors) >= live_neighbor_count)
                for neighbor_id in target.neighbors[:live_neighbor_count]:
                    assert neighbor_id is not None
                    board.set_state_for(neighbor_id, 1)

                next_board = engine.step_board(board, rule)
                self.assertEqual(next_board.state_for(target.id), 1)

    def test_penrose_topology_is_deterministic_and_contains_geometry_metadata(self) -> None:
        left = build_topology(PENROSE_GEOMETRY, 0, 0, patch_depth=3)
        right = build_topology(PENROSE_GEOMETRY, 0, 0, patch_depth=3)

        self.assertEqual(left.cell_count, right.cell_count)
        self.assertEqual([cell.id for cell in left.cells], [cell.id for cell in right.cells])
        self.assertTrue(all(cell.kind in {'thick-rhomb', 'thin-rhomb'} for cell in left.cells))
        self.assertTrue(all(cell.center is not None for cell in left.cells))
        self.assertTrue(all(cell.vertices is not None and len(cell.vertices) == 4 for cell in left.cells))
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
        self.assertTrue(all(cell.vertices is not None and len(cell.vertices) == 14 for cell in deep.cells))
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
        self.assertTrue(all(cell.vertices is not None and len(cell.vertices) == 4 for cell in deep.cells))
        for cell in deep.cells:
            self.assertEqual(len(cell.neighbors), len(set(cell.neighbors)))
            for neighbor_id in cell.neighbors:
                assert neighbor_id is not None
                self.assertIn(cell.id, deep.get_cell(neighbor_id).neighbors)

    def test_penrose_vertex_topology_is_symmetric_duplicate_free_and_larger_than_edge_neighbors(self) -> None:
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
            if len(edge_cell.neighbors) >= 4 and len(vertex_cell.neighbors) > len(edge_cell.neighbors):
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

        target = next(cell for cell in board.topology.cells if cell.kind == 'thin-rhomb' and len(cell.neighbors) >= 3)
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
