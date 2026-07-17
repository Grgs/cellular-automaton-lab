import sys
import unittest
from pathlib import Path

try:
    from backend.rules import RuleRegistry
    from backend.simulation.engine import SimulationEngine
    from backend.simulation.seeding import hamming, iter_trajectory, population
    from backend.simulation.seeding.comparison import _build_seeded_board
    from backend.simulation.topology import empty_board
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.rules import RuleRegistry
    from backend.simulation.engine import SimulationEngine
    from backend.simulation.seeding import hamming, iter_trajectory, population
    from backend.simulation.seeding.comparison import _build_seeded_board
    from backend.simulation.topology import empty_board


class TrajectoryTests(unittest.TestCase):
    def test_fuses_sparse_states_deltas_and_metrics(self) -> None:
        board = empty_board("square", 3, 3)
        cell_id = board.topology.cells[4].id
        board.set_state_for(cell_id, 1)

        frames = list(
            iter_trajectory(
                board,
                RuleRegistry().get("conway"),
                max_steps=2,
                include_sparse=True,
                include_deltas=True,
            )
        )

        self.assertEqual([frame.generation for frame in frames], [0, 1, 2])
        self.assertEqual([frame.population for frame in frames], [1, 0, 0])
        self.assertEqual([frame.changed_cells for frame in frames], [0, 1, 0])
        self.assertEqual(frames[0].sparse_states, {cell_id: 1})
        self.assertEqual(frames[0].delta, {})
        self.assertEqual(frames[1].sparse_states, {})
        self.assertEqual(frames[1].delta, {cell_id: 0})
        self.assertEqual(frames[1].extinction_step, 1)
        self.assertEqual(frames[2].cycle_start, 1)
        self.assertEqual(frames[2].period, 1)

    def test_cycle_stop_includes_the_first_repeated_frame(self) -> None:
        board = empty_board("square", 3, 3)
        frames = list(
            iter_trajectory(
                board,
                RuleRegistry().get("conway"),
                max_steps=20,
                stop_on_cycle=True,
            )
        )

        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[-1].generation, 1)
        self.assertEqual(frames[-1].cycle_start, 0)
        self.assertEqual(frames[-1].period, 1)

    def test_negative_step_budget_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            list(
                iter_trajectory(
                    empty_board("square", 2, 2),
                    RuleRegistry().get("conway"),
                    max_steps=-1,
                )
            )

    def test_matches_reference_across_topology_families(self) -> None:
        rule = RuleRegistry().get("conway")
        for geometry in (
            "square",
            "hex",
            "trihexagonal-3-6-3-6",
            "penrose-p3-rhombs",
        ):
            with self.subTest(geometry=geometry):
                board = _build_seeded_board(
                    geometry,
                    bits="011001100001000",
                    traversal="bfs",
                    grid_size=8,
                    live_state=1,
                    pattern=None,
                ).board
                engine = SimulationEngine()
                reference = []
                current = board
                seen = {tuple(current.cell_states): 0}
                extinction_step = 0 if population(current.cell_states) == 0 else None
                period = None
                for generation in range(9):
                    if generation > 0:
                        previous = current
                        current = engine.step_board(current, rule)
                        changed = hamming(previous.cell_states, current.cell_states)
                        if extinction_step is None and population(current.cell_states) == 0:
                            extinction_step = generation
                        if period is None:
                            state_key = tuple(current.cell_states)
                            repeated_at = seen.get(state_key)
                            if repeated_at is None:
                                seen[state_key] = generation
                            else:
                                period = generation - repeated_at
                    else:
                        changed = 0
                    reference.append(
                        (
                            generation,
                            population(current.cell_states),
                            changed,
                            current.states_by_id(omit_zero=True),
                            extinction_step,
                            period,
                        )
                    )

                measured = [
                    (
                        frame.generation,
                        frame.population,
                        frame.changed_cells,
                        frame.sparse_states,
                        frame.extinction_step,
                        frame.period,
                    )
                    for frame in iter_trajectory(
                        board,
                        rule,
                        max_steps=8,
                        include_sparse=True,
                    )
                ]
                self.assertEqual(measured, reference)


if __name__ == "__main__":
    unittest.main()
