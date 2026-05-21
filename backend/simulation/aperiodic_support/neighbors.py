"""Edge-neighbour detection for both float and exact-Fraction records.

Both modes share the same private overlap-test helpers, kept colocated with
the public builders since they are only consumed here.
"""

from __future__ import annotations

import math
from collections import defaultdict
from fractions import Fraction

from .geometry import canonical_edge, exact_canonical_edge
from .types import (
    COORDINATE_PRECISION,
    ExactNeighborMode,
    ExactPatchRecord,
    NeighborMode,
    PatchRecord,
)


def _edges_overlap_with_positive_length(
    first_left: tuple[float, float],
    first_right: tuple[float, float],
    second_left: tuple[float, float],
    second_right: tuple[float, float],
    *,
    tolerance: float = 1e-7,
) -> bool:
    delta_x = first_right[0] - first_left[0]
    delta_y = first_right[1] - first_left[1]
    if math.isclose(delta_x, 0.0, abs_tol=tolerance) and math.isclose(
        delta_y,
        0.0,
        abs_tol=tolerance,
    ):
        return False

    def _cross(
        origin: tuple[float, float],
        point: tuple[float, float],
    ) -> float:
        return (delta_x * (point[1] - origin[1])) - (delta_y * (point[0] - origin[0]))

    if (
        abs(_cross(first_left, second_left)) > tolerance
        or abs(_cross(first_left, second_right)) > tolerance
    ):
        return False

    axis = 0 if abs(delta_x) >= abs(delta_y) else 1
    first_start, first_end = sorted((first_left[axis], first_right[axis]))
    second_start, second_end = sorted((second_left[axis], second_right[axis]))
    overlap_start = max(first_start, second_start)
    overlap_end = min(first_end, second_end)
    return overlap_end - overlap_start > tolerance


def _exact_edges_overlap_with_positive_length(
    first_left: tuple[Fraction, Fraction],
    first_right: tuple[Fraction, Fraction],
    second_left: tuple[Fraction, Fraction],
    second_right: tuple[Fraction, Fraction],
) -> bool:
    delta_x = first_right[0] - first_left[0]
    delta_y = first_right[1] - first_left[1]
    if delta_x == 0 and delta_y == 0:
        return False

    def _cross(
        origin: tuple[Fraction, Fraction],
        point: tuple[Fraction, Fraction],
    ) -> Fraction:
        return (delta_x * (point[1] - origin[1])) - (delta_y * (point[0] - origin[0]))

    if _cross(first_left, second_left) != 0 or _cross(first_left, second_right) != 0:
        return False

    axis = 0 if delta_x != 0 else 1
    first_start, first_end = sorted((first_left[axis], first_right[axis]))
    second_start, second_end = sorted((second_left[axis], second_right[axis]))
    overlap_start = max(first_start, second_start)
    overlap_end = min(first_end, second_end)
    return overlap_end > overlap_start


def build_exact_neighbors(
    records: list[ExactPatchRecord],
    *,
    neighbor_mode: ExactNeighborMode = "full_edge",
) -> dict[str, tuple[str, ...]]:
    neighbor_sets: dict[str, set[str]] = {record["id"]: set() for record in records}
    if neighbor_mode == "full_edge":
        edge_map: dict[
            tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]],
            list[str],
        ] = defaultdict(list)
        for record in records:
            cell_id = record["id"]
            vertices = record["vertices"]
            for index, left in enumerate(vertices):
                right = vertices[(index + 1) % len(vertices)]
                edge_map[exact_canonical_edge(left, right)].append(cell_id)
        for owners in edge_map.values():
            unique_owners = tuple(sorted(set(owners)))
            if len(unique_owners) != 2:
                continue
            neighbor_left, neighbor_right = unique_owners
            neighbor_sets[neighbor_left].add(neighbor_right)
            neighbor_sets[neighbor_right].add(neighbor_left)
        return {cell_id: tuple(sorted(neighbors)) for cell_id, neighbors in neighbor_sets.items()}

    exact_edges: list[tuple[str, tuple[Fraction, Fraction], tuple[Fraction, Fraction]]] = []
    for record in records:
        vertices = record["vertices"]
        for index, left in enumerate(vertices):
            exact_edges.append((record["id"], left, vertices[(index + 1) % len(vertices)]))

    for index, (left_id, left_start, left_end) in enumerate(exact_edges):
        for right_id, right_start, right_end in exact_edges[index + 1 :]:
            if left_id == right_id:
                continue
            if not _exact_edges_overlap_with_positive_length(
                left_start,
                left_end,
                right_start,
                right_end,
            ):
                continue
            neighbor_sets[left_id].add(right_id)
            neighbor_sets[right_id].add(left_id)

    return {cell_id: tuple(sorted(neighbors)) for cell_id, neighbors in neighbor_sets.items()}


def build_edge_neighbors(
    records: list[PatchRecord],
    *,
    edge_precision: int = COORDINATE_PRECISION,
    neighbor_mode: NeighborMode = "full_edge",
) -> dict[str, tuple[str, ...]]:
    neighbor_sets: dict[str, set[str]] = {record["id"]: set() for record in records}
    if neighbor_mode == "segment_overlap":
        edges: list[tuple[str, tuple[float, float], tuple[float, float]]] = []
        for record in records:
            vertices = record["vertices"]
            for index, left in enumerate(vertices):
                edges.append((record["id"], left, vertices[(index + 1) % len(vertices)]))
        for index, (left_id, left_start, left_end) in enumerate(edges):
            for right_id, right_start, right_end in edges[index + 1 :]:
                if left_id == right_id:
                    continue
                if not _edges_overlap_with_positive_length(
                    left_start,
                    left_end,
                    right_start,
                    right_end,
                ):
                    continue
                neighbor_sets[left_id].add(right_id)
                neighbor_sets[right_id].add(left_id)
        return {cell_id: tuple(sorted(neighbors)) for cell_id, neighbors in neighbor_sets.items()}

    edge_map: dict[tuple[tuple[float, float], tuple[float, float]], list[str]] = defaultdict(list)
    for record in records:
        cell_id = record["id"]
        vertices = record["vertices"]
        for index, left in enumerate(vertices):
            right = vertices[(index + 1) % len(vertices)]
            edge_map[canonical_edge(left, right, precision=edge_precision)].append(cell_id)
    for owners in edge_map.values():
        unique_owners = tuple(sorted(set(owners)))
        if len(unique_owners) != 2:
            continue
        neighbor_left, neighbor_right = unique_owners
        neighbor_sets[neighbor_left].add(neighbor_right)
        neighbor_sets[neighbor_right].add(neighbor_left)
    return {cell_id: tuple(sorted(neighbors)) for cell_id, neighbors in neighbor_sets.items()}
