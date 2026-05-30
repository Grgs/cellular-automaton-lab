import sys
import unittest
from pathlib import Path

try:
    from backend.simulation.rule_context_frames import TopologyFrame, topology_frame_for
    from backend.simulation.seeding import (
        bfs_ring_order,
        compare_seed,
        normalize_bits,
        paint_bits,
        row_major_order,
    )
    from backend.simulation.seeding.metrics import (
        classify,
        first_extinction_step,
        hamming,
        population,
    )
    from backend.simulation.topology import empty_board
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.simulation.rule_context_frames import TopologyFrame, topology_frame_for
    from backend.simulation.seeding import (
        bfs_ring_order,
        compare_seed,
        normalize_bits,
        paint_bits,
        row_major_order,
    )
    from backend.simulation.seeding.metrics import (
        classify,
        first_extinction_step,
        hamming,
        population,
    )
    from backend.simulation.topology import empty_board


def _square_frame(size: int = 6) -> TopologyFrame:
    board = empty_board("square", size, size)
    return topology_frame_for(board.topology)


class TraversalTests(unittest.TestCase):
    def test_bfs_order_is_complete_and_unique(self) -> None:
        frame = _square_frame()
        order = bfs_ring_order(frame)
        self.assertEqual(len(order), frame.cell_count)
        self.assertEqual(len(set(order)), frame.cell_count)
        self.assertEqual(set(order), {cell.id for cell in frame.cells})

    def test_bfs_order_is_deterministic(self) -> None:
        frame = _square_frame()
        self.assertEqual(bfs_ring_order(frame), bfs_ring_order(frame))

    def test_bfs_starts_at_centre_cell(self) -> None:
        frame = _square_frame()
        first_id = bfs_ring_order(frame)[0]
        centre_cell = min(frame.cells, key=lambda cell: cell.shell_rank)
        self.assertEqual(frame.cell_for(first_id).shell_rank, centre_cell.shell_rank)

    def test_row_major_order_is_complete(self) -> None:
        frame = _square_frame()
        order = row_major_order(frame)
        self.assertEqual(set(order), {cell.id for cell in frame.cells})

    def test_normalize_bits_strips_separators(self) -> None:
        self.assertEqual(normalize_bits("01100 11000 01000"), "011001100001000")
        self.assertEqual(normalize_bits("0,1,1,x,0"), "0110")

    def test_paint_bits_preserves_live_count(self) -> None:
        frame = _square_frame()
        order = bfs_ring_order(frame)
        painted = paint_bits(order, "10101")
        self.assertEqual(len(painted), 3)
        self.assertTrue(all(state == 1 for state in painted.values()))

    def test_paint_bits_count_matches_across_topologies(self) -> None:
        seed = "11010 01011"
        expected = normalize_bits(seed).count("1")
        for geometry in ("square", "hex", "triangle"):
            board = empty_board(geometry, 8, 8)
            frame = topology_frame_for(board.topology)
            painted = paint_bits(bfs_ring_order(frame), seed)
            self.assertEqual(len(painted), expected, geometry)


class CompareSeedTests(unittest.TestCase):
    def test_compare_seed_returns_one_result_per_geometry(self) -> None:
        geometries = ("square", "hex", "triangle")
        comparison = compare_seed(
            seed="01100 11000 01000",
            geometries=geometries,
            steps=20,
        )
        self.assertEqual(tuple(result.geometry for result in comparison.results), geometries)
        for result in comparison.results:
            self.assertIsNone(result.note)
            self.assertEqual(len(result.population), result.steps_run + 1)
            self.assertNotEqual(result.classification, "error")

    def test_compare_seed_is_deterministic(self) -> None:
        first = compare_seed(seed="01100 11000 01000", geometries=("square", "hex"), steps=15)
        second = compare_seed(seed="01100 11000 01000", geometries=("square", "hex"), steps=15)
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_seed_truncated_note_when_seed_exceeds_cells(self) -> None:
        long_seed = "1" * 500
        comparison = compare_seed(
            seed=long_seed,
            geometries=("square",),
            steps=1,
            grid_size=4,
        )
        result = comparison.results[0]
        self.assertEqual(result.note, "seed-truncated")
        self.assertEqual(result.seed_cells, result.cell_count)

    def test_unknown_traversal_rejected(self) -> None:
        with self.assertRaises(ValueError):
            compare_seed(seed="111", geometries=("square",), traversal="spiral")

    def test_include_states_returns_reconstructable_begin_and_end(self) -> None:
        comparison = compare_seed(
            seed="0111110", geometries=("square",), steps=8, include_states=True
        )
        result = comparison.results[0]
        self.assertIsNotNone(result.topology_spec)
        assert result.topology_spec is not None
        self.assertEqual(result.topology_spec["tiling_family"], "square")
        self.assertGreater(result.topology_spec["width"], 0)
        self.assertGreater(result.topology_spec["height"], 0)
        self.assertIsNotNone(result.initial_cells_by_id)
        assert result.initial_cells_by_id is not None
        self.assertEqual(len(result.initial_cells_by_id), result.seed_cells)
        self.assertIsNotNone(result.final_cells_by_id)

    def test_states_omitted_by_default(self) -> None:
        result = compare_seed(seed="111", geometries=("square",), steps=3).results[0]
        self.assertIsNone(result.topology_spec)
        self.assertNotIn("topology_spec", result.to_dict())


class MetricsTests(unittest.TestCase):
    def test_population_counts_non_zero_states(self) -> None:
        self.assertEqual(population([0, 1, 2, 0, 3]), 3)

    def test_hamming_counts_changed_cells(self) -> None:
        self.assertEqual(hamming([0, 1, 0], [1, 1, 2]), 2)

    def test_first_extinction_step(self) -> None:
        self.assertEqual(first_extinction_step([3, 2, 0, 0]), 2)
        self.assertIsNone(first_extinction_step([3, 2, 1]))

    def test_classify_labels(self) -> None:
        self.assertEqual(classify([5, 5, 5], 1), "still-life")
        self.assertEqual(classify([5, 4, 5, 4], 2), "oscillator-p2")
        self.assertEqual(classify([3, 1, 0], None), "extinct")
        self.assertEqual(classify([3, 2, 2], None), "unsettled")


if __name__ == "__main__":
    unittest.main()
