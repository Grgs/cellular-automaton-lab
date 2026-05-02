import sys
import unittest
from pathlib import Path

try:
    from backend.simulation.topology import (
        ARCHIMEDEAN_488_GEOMETRY,
        CHAIR_GEOMETRY,
        DELTOIDAL_HEXAGONAL_GEOMETRY,
        DELTOIDAL_TRIHEXAGONAL_GEOMETRY,
        DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
        FLORET_PENTAGONAL_GEOMETRY,
        HAT_MONOTILE_GEOMETRY,
        KAGOME_GEOMETRY,
        PENROSE_GEOMETRY,
        PENROSE_VERTEX_GEOMETRY,
        PINWHEEL_GEOMETRY,
        PRISMATIC_PENTAGONAL_GEOMETRY,
        RHOMBILLE_GEOMETRY,
        ROBINSON_TRIANGLES_GEOMETRY,
        SHIELD_GEOMETRY,
        SNUB_SQUARE_DUAL_GEOMETRY,
        SPECTRE_GEOMETRY,
        SPHINX_GEOMETRY,
        TAYLOR_SOCOLAR_GEOMETRY,
        TETRAKIS_SQUARE_GEOMETRY,
        TRIAKIS_TRIANGULAR_GEOMETRY,
        TUEBINGEN_TRIANGLE_GEOMETRY,
        build_topology,
        empty_board,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.simulation.topology import (
        ARCHIMEDEAN_488_GEOMETRY,
        CHAIR_GEOMETRY,
        DELTOIDAL_HEXAGONAL_GEOMETRY,
        DELTOIDAL_TRIHEXAGONAL_GEOMETRY,
        DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
        FLORET_PENTAGONAL_GEOMETRY,
        HAT_MONOTILE_GEOMETRY,
        KAGOME_GEOMETRY,
        PENROSE_GEOMETRY,
        PENROSE_VERTEX_GEOMETRY,
        PINWHEEL_GEOMETRY,
        PRISMATIC_PENTAGONAL_GEOMETRY,
        RHOMBILLE_GEOMETRY,
        ROBINSON_TRIANGLES_GEOMETRY,
        SHIELD_GEOMETRY,
        SNUB_SQUARE_DUAL_GEOMETRY,
        SPECTRE_GEOMETRY,
        SPHINX_GEOMETRY,
        TAYLOR_SOCOLAR_GEOMETRY,
        TETRAKIS_SQUARE_GEOMETRY,
        TRIAKIS_TRIANGULAR_GEOMETRY,
        TUEBINGEN_TRIANGLE_GEOMETRY,
        build_topology,
        empty_board,
    )


class SimulationTopologyTests(unittest.TestCase):
    def test_neighbor_index_cache_matches_neighbor_id_ordering(self) -> None:
        cases = [
            ("square", 4, 3),
            ("hex", 4, 3),
            ("triangle", 5, 4),
            (ARCHIMEDEAN_488_GEOMETRY, 3, 3),
            (KAGOME_GEOMETRY, 4, 3),
            (RHOMBILLE_GEOMETRY, 3, 3),
            (DELTOIDAL_HEXAGONAL_GEOMETRY, 3, 3),
            (TETRAKIS_SQUARE_GEOMETRY, 3, 3),
            (TRIAKIS_TRIANGULAR_GEOMETRY, 3, 3),
            (DELTOIDAL_TRIHEXAGONAL_GEOMETRY, 3, 3),
            (PRISMATIC_PENTAGONAL_GEOMETRY, 3, 3),
            (FLORET_PENTAGONAL_GEOMETRY, 3, 3),
            (SNUB_SQUARE_DUAL_GEOMETRY, 3, 3),
            (CHAIR_GEOMETRY, 0, 0),
            (HAT_MONOTILE_GEOMETRY, 0, 0),
            (PINWHEEL_GEOMETRY, 0, 0),
            (ROBINSON_TRIANGLES_GEOMETRY, 0, 0),
            (SHIELD_GEOMETRY, 0, 0),
            (SPECTRE_GEOMETRY, 0, 0),
            (SPHINX_GEOMETRY, 0, 0),
            (DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY, 0, 0),
            (TAYLOR_SOCOLAR_GEOMETRY, 0, 0),
            (TUEBINGEN_TRIANGLE_GEOMETRY, 0, 0),
            (PENROSE_GEOMETRY, 0, 0),
            (PENROSE_VERTEX_GEOMETRY, 0, 0),
        ]

        for geometry, width, height in cases:
            with self.subTest(geometry=geometry):
                topology = build_topology(
                    geometry,
                    width,
                    height,
                    patch_depth=3
                    if geometry
                    in {
                        CHAIR_GEOMETRY,
                        HAT_MONOTILE_GEOMETRY,
                        PINWHEEL_GEOMETRY,
                        ROBINSON_TRIANGLES_GEOMETRY,
                        SHIELD_GEOMETRY,
                        SPECTRE_GEOMETRY,
                        SPHINX_GEOMETRY,
                        DODECAGONAL_SQUARE_TRIANGLE_GEOMETRY,
                        TAYLOR_SOCOLAR_GEOMETRY,
                        TUEBINGEN_TRIANGLE_GEOMETRY,
                        PENROSE_GEOMETRY,
                        PENROSE_VERTEX_GEOMETRY,
                    }
                    else None,
                )
                for index, cell in enumerate(topology.cells):
                    expected = tuple(
                        -1 if neighbor_id is None else topology.index_for(neighbor_id)
                        for neighbor_id in cell.neighbors
                    )
                    self.assertEqual(topology.neighbor_indexes_for(index), expected)

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


if __name__ == "__main__":
    unittest.main()
