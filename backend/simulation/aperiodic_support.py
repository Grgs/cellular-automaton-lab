from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Literal, NotRequired, TypedDict


COORDINATE_PRECISION = 6

Affine = tuple[float, float, float, float, float, float]
AFFINE_IDENTITY: Affine = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0)
AFFINE_REFLECT_X: Affine = (-1.0, 0.0, 0.0, 0.0, 1.0, 0.0)


@dataclass(frozen=True)
class AperiodicPatchCell:
    id: str
    kind: str
    center: tuple[float, float]
    vertices: tuple[tuple[float, float], ...]
    neighbors: tuple[str, ...]
    tile_family: str | None = None
    orientation_token: str | None = None
    chirality_token: str | None = None
    decoration_tokens: tuple[str, ...] | None = None


@dataclass(frozen=True)
class AperiodicPatch:
    patch_depth: int
    width: int
    height: int
    cells: tuple[AperiodicPatchCell, ...]


@dataclass(frozen=True)
class Vec:
    x: float
    y: float

    def __add__(self, other: "Vec") -> "Vec":
        return Vec(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec") -> "Vec":
        return Vec(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vec":
        return Vec(self.x * scalar, self.y * scalar)


class PatchRecord(TypedDict):
    id: str
    kind: str
    center: tuple[float, float]
    vertices: tuple[tuple[float, float], ...]
    tile_family: NotRequired[str | None]
    orientation_token: NotRequired[str | None]
    chirality_token: NotRequired[str | None]
    decoration_tokens: NotRequired[tuple[str, ...] | None]


class ExactPatchRecord(TypedDict):
    id: str
    kind: str
    vertices: tuple[tuple[Fraction, Fraction], ...]
    tile_family: NotRequired[str | None]
    orientation_token: NotRequired[str | None]
    chirality_token: NotRequired[str | None]
    decoration_tokens: NotRequired[tuple[str, ...] | None]


ExactNeighborMode = Literal["full_edge", "segment_overlap"]
NeighborMode = Literal["full_edge", "segment_overlap"]


def rounded_point(point: Vec | tuple[float, float]) -> tuple[float, float]:
    x_value, y_value = point if isinstance(point, tuple) else (point.x, point.y)
    return (
        round(float(x_value), COORDINATE_PRECISION),
        round(float(y_value), COORDINATE_PRECISION),
    )


def canonical_edge(
    point_a: tuple[float, float],
    point_b: tuple[float, float],
    *,
    precision: int = COORDINATE_PRECISION,
) -> tuple[tuple[float, float], tuple[float, float]]:
    left = (
        round(float(point_a[0]), precision),
        round(float(point_a[1]), precision),
    )
    right = (
        round(float(point_b[0]), precision),
        round(float(point_b[1]), precision),
    )
    return (left, right) if left <= right else (right, left)


def exact_canonical_edge(
    point_a: tuple[Fraction, Fraction],
    point_b: tuple[Fraction, Fraction],
) -> tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]]:
    return (point_a, point_b) if point_a <= point_b else (point_b, point_a)


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

    if abs(_cross(first_left, second_left)) > tolerance or abs(
        _cross(first_left, second_right)
    ) > tolerance:
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
        return {
            cell_id: tuple(sorted(neighbors))
            for cell_id, neighbors in neighbor_sets.items()
        }

    exact_edges: list[
        tuple[str, tuple[Fraction, Fraction], tuple[Fraction, Fraction]]
    ] = []
    for record in records:
        vertices = record["vertices"]
        for index, left in enumerate(vertices):
            exact_edges.append(
                (record["id"], left, vertices[(index + 1) % len(vertices)])
            )

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

    return {
        cell_id: tuple(sorted(neighbors))
        for cell_id, neighbors in neighbor_sets.items()
    }


def compatibility_extent(values: list[float]) -> int:
    if not values:
        return 1
    return max(1, int(math.ceil(max(values) - min(values))))


def polygon_centroid(vertices: Iterable[Vec]) -> Vec:
    points = list(vertices)
    if not points:
        return Vec(0.0, 0.0)
    area_twice = 0.0
    centroid_x = 0.0
    centroid_y = 0.0
    for index, point in enumerate(points):
        next_point = points[(index + 1) % len(points)]
        cross = (point.x * next_point.y) - (next_point.x * point.y)
        area_twice += cross
        centroid_x += (point.x + next_point.x) * cross
        centroid_y += (point.y + next_point.y) * cross
    if math.isclose(area_twice, 0.0):
        return Vec(
            sum(point.x for point in points) / len(points),
            sum(point.y for point in points) / len(points),
        )
    scale = 1 / (3 * area_twice)
    return Vec(centroid_x * scale, centroid_y * scale)


def encode_float(value: float) -> str:
    scaled = int(round(value * 1_000_000))
    if scaled < 0:
        return f"n{abs(scaled)}"
    if scaled > 0:
        return f"p{scaled}"
    return "0"


def affine_multiply(left: Affine, right: Affine) -> Affine:
    return (
        (left[0] * right[0]) + (left[1] * right[3]),
        (left[0] * right[1]) + (left[1] * right[4]),
        (left[0] * right[2]) + (left[1] * right[5]) + left[2],
        (left[3] * right[0]) + (left[4] * right[3]),
        (left[3] * right[1]) + (left[4] * right[4]),
        (left[3] * right[2]) + (left[4] * right[5]) + left[5],
    )


def affine_apply(transform: Affine, point: Vec) -> Vec:
    return Vec(
        (transform[0] * point.x) + (transform[1] * point.y) + transform[2],
        (transform[3] * point.x) + (transform[4] * point.y) + transform[5],
    )


def affine_inverse(transform: Affine) -> Affine:
    determinant = (transform[0] * transform[4]) - (transform[1] * transform[3])
    if math.isclose(determinant, 0.0):
        raise ValueError("Cannot invert singular affine transform.")
    inverse_determinant = 1.0 / determinant
    a = transform[4] * inverse_determinant
    b = -transform[1] * inverse_determinant
    d = -transform[3] * inverse_determinant
    e = transform[0] * inverse_determinant
    c = -((a * transform[2]) + (b * transform[5]))
    f = -((d * transform[2]) + (e * transform[5]))
    return (a, b, c, d, e, f)


def translation(tx: float, ty: float) -> Affine:
    return (1.0, 0.0, float(tx), 0.0, 1.0, float(ty))


def translation_to(source: Vec, target: Vec) -> Affine:
    return translation(target.x - source.x, target.y - source.y)


def rotation(radians: float) -> Affine:
    cosine = math.cos(radians)
    sine = math.sin(radians)
    return (cosine, -sine, 0.0, sine, cosine, 0.0)


def scale(factor: float) -> Affine:
    return (float(factor), 0.0, 0.0, 0.0, float(factor), 0.0)


def id_from_anchor(prefix: str, anchor: Vec, orientation: int) -> str:
    return f"{prefix}:{orientation % 360}:{encode_float(anchor.x)}:{encode_float(anchor.y)}"


def id_from_transform(prefix: str, transform: Affine) -> str:
    return prefix + ":" + ":".join(encode_float(value) for value in transform)


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
        return {
            cell_id: tuple(sorted(neighbors))
            for cell_id, neighbors in neighbor_sets.items()
        }

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
    return {
        cell_id: tuple(sorted(neighbors))
        for cell_id, neighbors in neighbor_sets.items()
    }


def patch_from_records(
    patch_depth: int,
    records: list[PatchRecord],
    *,
    edge_precision: int = COORDINATE_PRECISION,
    neighbor_mode: NeighborMode = "full_edge",
) -> AperiodicPatch:
    neighbors_by_id = build_edge_neighbors(
        records,
        edge_precision=edge_precision,
        neighbor_mode=neighbor_mode,
    )
    cells = tuple(
        AperiodicPatchCell(
            id=record["id"],
            kind=record["kind"],
            center=record["center"],
            vertices=record["vertices"],
            neighbors=neighbors_by_id[record["id"]],
            tile_family=record.get("tile_family"),
            orientation_token=record.get("orientation_token"),
            chirality_token=record.get("chirality_token"),
            decoration_tokens=record.get("decoration_tokens"),
        )
        for record in sorted(records, key=lambda item: item["id"])
    )
    all_x = [vertex[0] for cell in cells for vertex in cell.vertices]
    all_y = [vertex[1] for cell in cells for vertex in cell.vertices]
    return AperiodicPatch(
        patch_depth=int(patch_depth),
        width=compatibility_extent(all_x),
        height=compatibility_extent(all_y),
        cells=cells,
    )


def patch_from_exact_records(
    patch_depth: int,
    records: list[ExactPatchRecord],
    *,
    float_scale: float = 1.0,
    vertex_precision: int | None = COORDINATE_PRECISION,
    neighbor_mode: ExactNeighborMode = "full_edge",
) -> AperiodicPatch:
    neighbors_by_id = build_exact_neighbors(records, neighbor_mode=neighbor_mode)

    float_records: list[PatchRecord] = []
    for record in records:
        raw_vertices = tuple(
            (
                float(vertex[0]) * float_scale,
                float(vertex[1]) * float_scale,
            )
            for vertex in record["vertices"]
        )
        if vertex_precision is None:
            float_vertices = raw_vertices
        else:
            float_vertices = tuple(
                (
                    round(vertex[0], vertex_precision),
                    round(vertex[1], vertex_precision),
                )
                for vertex in raw_vertices
            )
        centroid = polygon_centroid(
            tuple(Vec(vertex[0], vertex[1]) for vertex in float_vertices)
        )
        float_records.append(
            {
                "id": record["id"],
                "kind": record["kind"],
                "center": rounded_point(centroid),
                "vertices": float_vertices,
                "tile_family": record.get("tile_family"),
                "orientation_token": record.get("orientation_token"),
                "chirality_token": record.get("chirality_token"),
                "decoration_tokens": record.get("decoration_tokens"),
            }
        )

    cells = tuple(
        AperiodicPatchCell(
            id=record["id"],
            kind=record["kind"],
            center=record["center"],
            vertices=record["vertices"],
            neighbors=neighbors_by_id[record["id"]],
            tile_family=record.get("tile_family"),
            orientation_token=record.get("orientation_token"),
            chirality_token=record.get("chirality_token"),
            decoration_tokens=record.get("decoration_tokens"),
        )
        for record in sorted(float_records, key=lambda item: item["id"])
    )
    all_x = [vertex[0] for cell in cells for vertex in cell.vertices]
    all_y = [vertex[1] for cell in cells for vertex in cell.vertices]
    return AperiodicPatch(
        patch_depth=int(patch_depth),
        width=compatibility_extent(all_x),
        height=compatibility_extent(all_y),
        cells=cells,
    )


def patch_from_cells(
    patch_depth: int,
    cells: Iterable[AperiodicPatchCell],
) -> AperiodicPatch:
    resolved_cells = tuple(cells)
    all_x = [vertex[0] for cell in resolved_cells for vertex in cell.vertices]
    all_y = [vertex[1] for cell in resolved_cells for vertex in cell.vertices]
    return AperiodicPatch(
        patch_depth=int(patch_depth),
        width=compatibility_extent(all_x),
        height=compatibility_extent(all_y),
        cells=resolved_cells,
    )
