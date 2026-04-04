from __future__ import annotations

import math
from collections import defaultdict

from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    PatchRecord,
    Vec,
    id_from_anchor,
    patch_from_records,
    polygon_centroid,
    rounded_point,
)


SILVER_RATIO = 1 + math.sqrt(2)

_AB_DIRECTIONS = tuple(
    Vec(math.cos(index * math.pi / 4), math.sin(index * math.pi / 4))
    for index in range(8)
)
_AB_RHOMB_VERTICES = ((), (1,), (1, 1), (0, 1))
_AB_TRIANGLE_VERTICES = ((), (1,), (1, 0, 1))
_AB_SUBSTITUTIONS = {
    "rhomb": (
        ("rhomb", (), 0),
        ("rhomb", (1, 1, 1, -1), 0),
        ("rhomb", (1, 1, 1), 6),
        ("RSquare", (1, 1, 0, -1), 3),
        ("RSquare", (1, 1, 1), 7),
        ("LSquare", (0, 1), 0),
        ("LSquare", (2, 1, 1, -1), 4),
    ),
    "RSquare": (
        ("rhomb", (0,), 0),
        ("rhomb", (1, 1, 0, -1), 2),
        ("LSquare", (0, 1), 0),
        ("RSquare", (1, 1, 0, -1), 3),
        ("RSquare", (1, 2, 1), 5),
    ),
    "LSquare": (
        ("rhomb", (0, 1), 7),
        ("rhomb", (1, 1), 1),
        ("LSquare", (0, 1, 0, -1), 3),
        ("RSquare", (0, 1), 0),
        ("LSquare", (1, 2), 5),
    ),
}


def _ab_vector(coefficients: tuple[int, ...], orientation: int, length: float) -> Vec:
    point = Vec(0.0, 0.0)
    for index, coefficient in enumerate(coefficients):
        if coefficient == 0:
            continue
        direction = _AB_DIRECTIONS[(orientation + index) % 8]
        point = point + (direction * (coefficient * length))
    return point


def _ab_vertices(name: str, anchor: Vec, orientation: int, length: float) -> tuple[Vec, ...]:
    base_shape = _AB_RHOMB_VERTICES if name == "rhomb" else _AB_TRIANGLE_VERTICES
    return tuple(anchor + _ab_vector(tuple(vertex), orientation, length) for vertex in base_shape)


def _inflate_ammann_tile(
    name: str,
    anchor: Vec,
    orientation: int,
    length: float,
    depth: int,
    leaves: list[tuple[str, tuple[Vec, ...], Vec, int]],
) -> None:
    if depth == 0:
        vertices = _ab_vertices(name, anchor, orientation, length)
        leaves.append((name, vertices, anchor, orientation))
        return

    child_length = length / SILVER_RATIO
    for child_name, origin, child_orientation in _AB_SUBSTITUTIONS[name]:
        child_anchor = anchor + _ab_vector(tuple(origin), orientation, child_length)
        _inflate_ammann_tile(
            child_name,
            child_anchor,
            (orientation + child_orientation) % 8,
            child_length,
            depth - 1,
            leaves,
        )


def _merge_ammann_triangles(
    leaves: list[tuple[str, tuple[Vec, ...], Vec, int]]
) -> list[PatchRecord]:
    records: list[PatchRecord] = []
    triangle_pairs: dict[tuple[tuple[float, float], tuple[float, float]], list[tuple[str, tuple[Vec, ...], Vec, int]]] = defaultdict(list)
    for name, vertices, anchor, orientation in leaves:
        if name == "rhomb":
            rounded_vertices = tuple(rounded_point(vertex) for vertex in vertices)
            center = rounded_point(polygon_centroid(vertices))
            records.append(
                {
                    "id": id_from_anchor("abr", anchor, orientation * 45),
                    "kind": "rhomb",
                    "center": center,
                    "vertices": rounded_vertices,
                }
            )
            continue
        hypotenuse = (
            rounded_point(vertices[0]),
            rounded_point(vertices[2]),
        )
        edge_key = hypotenuse if hypotenuse[0] <= hypotenuse[1] else (hypotenuse[1], hypotenuse[0])
        triangle_pairs[edge_key].append((name, vertices, anchor, orientation))

    for edge_key, pair in triangle_pairs.items():
        if len(pair) != 2:
            continue
        unique_vertices = {
            rounded_point(vertex)
            for _, vertices, _, _ in pair
            for vertex in vertices
        }
        center_x = sum(vertex[0] for vertex in unique_vertices) / len(unique_vertices)
        center_y = sum(vertex[1] for vertex in unique_vertices) / len(unique_vertices)
        polygon_vertices = sorted(
            unique_vertices,
            key=lambda point: math.atan2(point[1] - center_y, point[0] - center_x),
        )
        rounded_vertices = tuple(polygon_vertices)
        center = rounded_point(
            polygon_centroid(tuple(Vec(x_value, y_value) for x_value, y_value in rounded_vertices))
        )
        records.append(
            {
                "id": f"abs:{edge_key[0][0]}:{edge_key[0][1]}:{edge_key[1][0]}:{edge_key[1][1]}",
                "kind": "square",
                "center": center,
                "vertices": rounded_vertices,
            }
        )
    return records


def build_ammann_beenker_patch(patch_depth: int) -> AperiodicPatch:
    root_length = SILVER_RATIO ** int(patch_depth)
    leaves: list[tuple[str, tuple[Vec, ...], Vec, int]] = []
    for orientation in range(8):
        _inflate_ammann_tile("rhomb", Vec(0.0, 0.0), orientation, root_length, int(patch_depth), leaves)
    patch = patch_from_records(patch_depth, _merge_ammann_triangles(leaves))
    if any(not cell.neighbors for cell in patch.cells):
        return AperiodicPatch(
            patch_depth=patch.patch_depth,
            width=patch.width,
            height=patch.height,
            cells=tuple(cell for cell in patch.cells if cell.neighbors),
        )
    return patch
