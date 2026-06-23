from __future__ import annotations

import math
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.simulation.aperiodic_hat import build_hat_patch
from backend.simulation.aperiodic_turtle import build_turtle_patch

# Canonical turtle outline, taken independently from christianp/aperiodic-monotile
# (turtle-monotile.svg). Each entry is a relative edge step; the closing edge
# back to the origin is implied. This is the literature reference the generated
# tile is checked against, not a value derived from our own construction.
_SQRT3 = math.sqrt(3.0)
_HALF_SQRT3 = _SQRT3 / 2.0
_CANONICAL_TURTLE_STEPS = (
    (1.0, 0.0),
    (0.5, _HALF_SQRT3),
    (1.5, -_HALF_SQRT3),
    (3.0, _SQRT3),
    (0.0, _SQRT3),
    (-1.0, 0.0),
    (-0.5, _HALF_SQRT3),
    (-1.5, -_HALF_SQRT3),
    (-1.5, _HALF_SQRT3),
    (-0.5, -_HALF_SQRT3),
    (0.5, -_HALF_SQRT3),
    (-1.5, -_HALF_SQRT3),
)

# Hat / Turtle share one combinatorial tiling, so cell counts match at every
# depth (8, 50, 338, 2312 for depths 0..3).
_EXPECTED_CELL_COUNTS = {0: 8, 1: 50, 2: 338, 3: 2312}


def _canonical_turtle_outline() -> tuple[tuple[float, float], ...]:
    points = [(0.0, 0.0)]
    x = y = 0.0
    for dx, dy in _CANONICAL_TURTLE_STEPS:
        x += dx
        y += dy
        points.append((x, y))
    # The path does not return to the origin before the implied closing edge,
    # so every accumulated point is a real vertex.
    return tuple(points)


def _edge_length_signature(polygon: tuple[tuple[float, float], ...]) -> Counter[float]:
    count = len(polygon)
    edges = [
        math.hypot(
            polygon[(index + 1) % count][0] - polygon[index][0],
            polygon[(index + 1) % count][1] - polygon[index][1],
        )
        for index in range(count)
    ]
    shortest = min(edges)
    return Counter(round(length / shortest, 3) for length in edges)


def _turn_signature(polygon: tuple[tuple[float, float], ...]) -> Counter[int]:
    count = len(polygon)
    turns: list[int] = []
    for index in range(count):
        previous = polygon[(index - 1) % count]
        current = polygon[index]
        following = polygon[(index + 1) % count]
        incoming = math.atan2(current[1] - previous[1], current[0] - previous[0])
        outgoing = math.atan2(following[1] - current[1], following[0] - current[0])
        angle = math.degrees(outgoing - incoming)
        turns.append(round(((angle + 180.0) % 360.0) - 180.0))
    return Counter(turns)


class TurtleMonotileTests(unittest.TestCase):
    def test_cell_counts_match_hat_continuum(self) -> None:
        for depth, expected in _EXPECTED_CELL_COUNTS.items():
            patch = build_turtle_patch(depth)
            self.assertEqual(len(patch.cells), expected, f"depth {depth}")

    def test_single_tile_is_congruent_to_canonical_turtle(self) -> None:
        # Every cell is a congruent copy of the turtle prototile, so checking
        # one against the independent canonical outline is sufficient.
        patch = build_turtle_patch(1)
        tile = patch.cells[0].vertices
        canonical = _canonical_turtle_outline()
        self.assertEqual(len(tile), len(canonical))
        self.assertEqual(
            _edge_length_signature(tile),
            _edge_length_signature(canonical),
            "turtle edge-length multiset must match the canonical turtle",
        )
        self.assertEqual(
            _turn_signature(tile),
            _turn_signature(canonical),
            "turtle turn-angle multiset must match the canonical turtle",
        )

    def test_edge_lengths_use_two_values_in_sqrt3_ratio(self) -> None:
        # Turtle = Tile(sqrt(3), 1): exactly two edge lengths whose ratio is
        # sqrt(3), plus one doubled (collinear) long edge.
        tile = build_turtle_patch(1).cells[0].vertices
        signature = _edge_length_signature(tile)
        self.assertEqual(set(signature), {1.0, round(_SQRT3, 3), round(2 * _SQRT3, 3)})

    def test_adjacency_matches_hat(self) -> None:
        # The deformation preserves the hat's combinatorial structure, so the
        # neighbour graph is identical once ids are mapped hat:<n> -> turtle:<n>.
        hat = build_hat_patch(2)
        turtle = build_turtle_patch(2)
        hat_graph = {
            cell.id.split(":")[1]: {n.split(":")[1] for n in cell.neighbors} for cell in hat.cells
        }
        turtle_graph = {
            cell.id.split(":")[1]: {n.split(":")[1] for n in cell.neighbors}
            for cell in turtle.cells
        }
        self.assertEqual(turtle_graph, hat_graph)

    def test_both_chiralities_present(self) -> None:
        tokens = {cell.chirality_token for cell in build_turtle_patch(1).cells}
        self.assertEqual(tokens, {"left", "right"})


if __name__ == "__main__":
    unittest.main()
