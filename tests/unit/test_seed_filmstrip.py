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
        # The friendly catalog label rides along so the client can name the
        # board without re-deriving it from the geometry key.
        self.assertEqual(tiling.label, "Square")
        self.assertEqual(tiling.to_dict()["label"], "Square")

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


class FeaturedDemoLivenessTests(unittest.TestCase):
    """Pin the one-click featured demo so it stays alive across its loop window.

    The wall's first-visit autoplay loops the sub-window
    ``[loop_start, frames - 1]`` (see ``FEATURED_COMPARE_DEMO`` /
    ``FEATURED_COMPARE_DEMO_LOOP_START`` in
    ``frontend/compare/compare-options.ts``). "Alive in one click" is only true
    if every board still has live cells across that window, so this asserts it
    against the real engine rather than trusting a comment. Keep these constants
    in sync with the frontend demo; changing the demo means re-checking liveness
    here.
    """

    # Mirror of FEATURED_COMPARE_DEMO in frontend/compare/compare-options.ts.
    DEMO_RULE = "penrose-greenberg-hastings"
    DEMO_PATTERN = "r-pentomino"
    DEMO_TRAVERSAL = "bfs"
    DEMO_GRID_SIZE = 22
    DEMO_FRAMES = 12
    DEMO_GEOMETRIES = (
        "square",
        "trihexagonal-3-6-3-6",
        "penrose-p3-rhombs",
        "hat-monotile",
    )
    DEMO_LOOP_START = 4  # FEATURED_COMPARE_DEMO_LOOP_START

    def test_every_board_stays_alive_across_the_loop_window(self) -> None:
        filmstrip = run_seed_filmstrip(
            seed="",
            rule_name=self.DEMO_RULE,
            geometries=self.DEMO_GEOMETRIES,
            traversal=self.DEMO_TRAVERSAL,
            frame_count=self.DEMO_FRAMES,
            grid_size=self.DEMO_GRID_SIZE,
            pattern=self.DEMO_PATTERN,
        )
        self.assertEqual({t.geometry for t in filmstrip.tilings}, set(self.DEMO_GEOMETRIES))
        for tiling in filmstrip.tilings:
            window = tiling.frames[self.DEMO_LOOP_START :]
            live_counts = [len(frame) for frame in window]
            with self.subTest(geometry=tiling.geometry):
                self.assertIsNone(
                    tiling.extinction_step,
                    f"{tiling.geometry} goes extinct at step {tiling.extinction_step}",
                )
                self.assertTrue(
                    all(count > 0 for count in live_counts),
                    f"{tiling.geometry} has a dead frame in the loop window: {live_counts}",
                )


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
