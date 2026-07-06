"""Gate 0 for the "edit everywhere" arc: is wall frame 0 an editable seed?

The wall's boards are filmstrips of one tiling-agnostic seed projected onto each
geometry through a traversal. Editing a board at generation 0 only makes sense if
frame 0 can be pulled back to the shared seed: the painted cell must map to a bit
index so the edit re-runs the whole wall.

These tests prove, against the real seeding engine, that the pull-back exists and
round-trips for every supported geometry, and pin the one behaviour that shapes
the PR E UX: a *named-shape* seed (geometric placement, e.g. the featured demo's
r-pentomino) converts to an editable bit-string per geometry, but that bit-string
does not reproduce the same shape on a different geometry -- so entering edit mode
on a shape demo re-runs every board from the traversal projection.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

try:
    from backend.simulation.rule_context_frames import TopologyFrame, topology_frame_for
    from backend.simulation.seeding.comparison import (
        board_size_for,
        compare_seed,
        run_seed_filmstrip,
    )
    from backend.simulation.seeding.shapes import NAMED_PATTERNS, place_pattern
    from backend.simulation.seeding.traversal import TRAVERSALS, paint_bits
    from backend.simulation.topology import empty_board
    from backend.simulation.topology_catalog import SUPPORTED_GEOMETRIES
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from backend.simulation.rule_context_frames import TopologyFrame, topology_frame_for
    from backend.simulation.seeding.comparison import (
        board_size_for,
        compare_seed,
        run_seed_filmstrip,
    )
    from backend.simulation.seeding.shapes import NAMED_PATTERNS, place_pattern
    from backend.simulation.seeding.traversal import TRAVERSALS, paint_bits
    from backend.simulation.topology import empty_board
    from backend.simulation.topology_catalog import SUPPORTED_GEOMETRIES

TRAVERSAL = "bfs"
GRID_SIZE = 12
# A seed with live and dead bits, short enough to fit every geometry's cell count.
BIT_SEED = "0110100011"

# Representative geometries spanning the render families, for the (more expensive)
# engine cross-checks; the structural checks below run over every geometry.
REPRESENTATIVE_GEOMETRIES = (
    "square",
    "hex",
    "triangle",
    "trihexagonal-3-6-3-6",
    "penrose-p3-rhombs",
    "hat-monotile",
    "spectre",
)


def _order_and_frame(geometry: str) -> tuple[list[str], TopologyFrame]:
    width, height, patch_depth = board_size_for(geometry, GRID_SIZE)
    frame = topology_frame_for(empty_board(geometry, width, height, patch_depth).topology)
    return TRAVERSALS[TRAVERSAL](frame), frame


def _reconstruct_bits(order: list[str], live_cells: set[str]) -> str:
    """Pull a set of live cells back to the shortest seed that reproduces them."""
    index_of = {cell_id: i for i, cell_id in enumerate(order)}
    live_indices = sorted(index_of[cell_id] for cell_id in live_cells)
    if not live_indices:
        return ""
    live_set = set(live_indices)
    return "".join("1" if i in live_set else "0" for i in range(live_indices[-1] + 1))


class SeedPullbackTests(unittest.TestCase):
    def test_traversal_order_is_a_full_permutation_for_every_geometry(self) -> None:
        # The pull-back is a bijection bit-index <-> cell only if the traversal
        # enumerates every cell exactly once.
        for geometry in SUPPORTED_GEOMETRIES:
            with self.subTest(geometry=geometry):
                order, frame = _order_and_frame(geometry)
                self.assertEqual(len(order), frame.cell_count)
                self.assertEqual(len(set(order)), frame.cell_count)

    def test_bitstring_frame0_round_trips_for_every_geometry(self) -> None:
        # frame 0 (bit seed) -> live cells -> reconstructed seed -> live cells is
        # the identity, so any gen-0 paint maps back to a bit the wall re-runs.
        for geometry in SUPPORTED_GEOMETRIES:
            with self.subTest(geometry=geometry):
                order, _ = _order_and_frame(geometry)
                projected = set(paint_bits(order, BIT_SEED))
                reconstructed = _reconstruct_bits(order, projected)
                self.assertEqual(set(paint_bits(order, reconstructed)), projected)

    def test_engine_frame0_matches_paint_bits(self) -> None:
        # The public engine's frame 0 equals the pull-back's forward projection,
        # so the frontend can trust paint_bits(order, bits) == what it renders.
        for geometry in REPRESENTATIVE_GEOMETRIES:
            with self.subTest(geometry=geometry):
                order, _ = _order_and_frame(geometry)
                comparison = compare_seed(
                    seed=BIT_SEED,
                    rule_name="conway",
                    geometries=(geometry,),
                    traversal=TRAVERSAL,
                    steps=0,
                    grid_size=GRID_SIZE,
                    include_states=True,
                )
                frame0 = set(comparison.results[0].initial_cells_by_id or {})
                self.assertEqual(frame0, set(paint_bits(order, BIT_SEED)))

    def test_named_shape_frame0_converts_to_an_editable_bitstring(self) -> None:
        # A geometric shape seed has no bit-string, but its frame 0 on a given
        # geometry pulls back to a seed that reproduces it there -- the "convert
        # to an editable seed on first paint" policy.
        for geometry in REPRESENTATIVE_GEOMETRIES:
            with self.subTest(geometry=geometry):
                order, frame = _order_and_frame(geometry)
                shape_cells = set(place_pattern(frame, NAMED_PATTERNS["r-pentomino"]))
                self.assertTrue(shape_cells)
                shape_bits = _reconstruct_bits(order, shape_cells)
                self.assertEqual(set(paint_bits(order, shape_bits)), shape_cells)

    def test_filmstrip_payload_carries_the_pullback_order(self) -> None:
        # The wall's edit mode pulls a painted frame-0 cell back to a seed bit
        # via the filmstrip payload's seed_order; it must equal the traversal's
        # ordering and be consistent with frame 0 for both seeding policies.
        filmstrip = run_seed_filmstrip(
            seed=BIT_SEED,
            rule_name="conway",
            geometries=("square", "trihexagonal-3-6-3-6"),
            traversal=TRAVERSAL,
            frame_count=2,
            grid_size=GRID_SIZE,
        )
        for tiling in filmstrip.tilings:
            with self.subTest(geometry=tiling.geometry):
                order, _ = _order_and_frame(tiling.geometry)
                self.assertEqual(tiling.seed_order, order)
                self.assertEqual(
                    set(tiling.frames[0]),
                    set(paint_bits(tiling.seed_order, BIT_SEED)),
                )
                self.assertEqual(tiling.to_dict()["seed_order"], order)

        # Shape-seeded runs carry the same order (the pull-back target for the
        # convert-on-first-paint policy).
        shaped = run_seed_filmstrip(
            seed="",
            rule_name="conway",
            geometries=("square",),
            traversal=TRAVERSAL,
            frame_count=2,
            grid_size=GRID_SIZE,
            pattern="r-pentomino",
        )
        order, _ = _order_and_frame("square")
        self.assertEqual(shaped.tilings[0].seed_order, order)

    def test_named_shape_bitstring_diverges_across_geometries(self) -> None:
        # PR E UX gate: converting a shape seed on one geometry and applying the
        # bit-string to another does NOT reproduce that geometry's own geometric
        # placement (live-cell count is preserved, cells are not). This is why
        # entering edit mode on a shape demo visibly re-runs every board.
        order_square, frame_square = _order_and_frame("square")
        order_other, frame_other = _order_and_frame("trihexagonal-3-6-3-6")
        square_shape = set(place_pattern(frame_square, NAMED_PATTERNS["r-pentomino"]))
        square_bits = _reconstruct_bits(order_square, square_shape)
        other_from_square_bits = set(paint_bits(order_other, square_bits))
        other_own_shape = set(place_pattern(frame_other, NAMED_PATTERNS["r-pentomino"]))

        self.assertEqual(len(other_from_square_bits), square_bits.count("1"))
        self.assertNotEqual(other_from_square_bits, other_own_shape)


if __name__ == "__main__":
    unittest.main()
