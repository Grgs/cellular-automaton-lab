import sys
import unittest
from pathlib import Path

try:
    from backend.simulation.seeding import run_seed_filmstrip
    from backend.simulation.seeding.comparison import (
        MAX_FILMSTRIP_FRAMES,
        MAX_FILMSTRIP_TILINGS,
    )
    from backend.simulation.seeding.request import (
        parse_filmstrip_request,
        run_filmstrip_request,
    )
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.simulation.seeding import run_seed_filmstrip
    from backend.simulation.seeding.comparison import (
        MAX_FILMSTRIP_FRAMES,
        MAX_FILMSTRIP_TILINGS,
    )
    from backend.simulation.seeding.request import (
        parse_filmstrip_request,
        run_filmstrip_request,
    )


class SeedFilmstripEngineTests(unittest.TestCase):
    def test_all_tilings_share_the_same_frame_count(self) -> None:
        filmstrip = run_seed_filmstrip(
            seed="101",
            rule_name="conway",
            geometries=("square", "hex", "triangle"),
            frame_count=8,
            grid_size=8,
        )
        self.assertEqual(len(filmstrip.tilings), 3)
        for tiling in filmstrip.tilings:
            with self.subTest(tiling=tiling.tiling_family):
                self.assertEqual(len(tiling.frames), 8)

    def test_frame_zero_is_the_seed_and_carries_topology(self) -> None:
        filmstrip = run_seed_filmstrip(
            seed="111",
            rule_name="conway",
            geometries=("square",),
            frame_count=4,
            grid_size=8,
        )
        tiling = filmstrip.tilings[0]
        # Sparse frames: a cell-id -> state map, zero states omitted.
        self.assertEqual(len(tiling.frames[0]), 3)
        self.assertTrue(all(state != 0 for state in tiling.frames[0].values()))
        self.assertTrue(tiling.topology["cells"])
        self.assertEqual(tiling.topology_spec["tiling_family"], "square")

    def test_single_live_cell_goes_extinct_deterministically(self) -> None:
        filmstrip = run_seed_filmstrip(
            seed="1",
            rule_name="conway",
            geometries=("square",),
            frame_count=4,
            grid_size=8,
        )
        tiling = filmstrip.tilings[0]
        self.assertEqual(len(tiling.frames[0]), 1)
        self.assertEqual(tiling.frames[1], {})  # a lone live cell dies under Conway
        self.assertEqual(tiling.extinction_step, 1)

    def test_runs_are_deterministic(self) -> None:
        first = run_seed_filmstrip(
            seed="1101",
            rule_name="conway",
            geometries=("square", "hex"),
            frame_count=6,
            grid_size=8,
        )
        second = run_seed_filmstrip(
            seed="1101",
            rule_name="conway",
            geometries=("square", "hex"),
            frame_count=6,
            grid_size=8,
        )
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_frame_count_is_clamped_to_the_maximum(self) -> None:
        filmstrip = run_seed_filmstrip(
            seed="1",
            rule_name="conway",
            geometries=("square",),
            frame_count=MAX_FILMSTRIP_FRAMES + 50,
            grid_size=6,
        )
        self.assertEqual(len(filmstrip.tilings[0].frames), MAX_FILMSTRIP_FRAMES)

    def test_too_many_tilings_is_rejected(self) -> None:
        too_many = tuple(["square"] * (MAX_FILMSTRIP_TILINGS + 1))
        with self.assertRaises(ValueError):
            run_seed_filmstrip(seed="1", geometries=too_many)

    def test_empty_geometries_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            run_seed_filmstrip(seed="1", geometries=())

    def test_unknown_geometry_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            run_seed_filmstrip(seed="1", geometries=("not-a-real-geometry",))


class FilmstripRequestTests(unittest.TestCase):
    def test_geometries_are_required(self) -> None:
        with self.assertRaises(ValueError):
            parse_filmstrip_request({"seed": "11"})

    def test_too_many_tilings_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_filmstrip_request(
                {"seed": "1", "geometries": ["square"] * (MAX_FILMSTRIP_TILINGS + 1)}
            )

    def test_run_filmstrip_request_returns_serialised_filmstrip(self) -> None:
        payload = run_filmstrip_request(
            {"seed": "11", "rule": "conway", "geometries": ["square", "hex"], "frames": 5}
        )
        self.assertEqual(payload["frame_count"], 5)
        self.assertEqual({t["tiling_family"] for t in payload["tilings"]}, {"square", "hex"})
        self.assertEqual(len(payload["tilings"][0]["frames"]), 5)


if __name__ == "__main__":
    unittest.main()
