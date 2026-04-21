from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import math
from typing import TypedDict

import fitz


SOURCE_PATCH_PDF = Path(__file__).with_name("bielefeld-patch.pdf")
MAX_PATCH_DEPTH = 7
SEED_CELL_INDEX = 3557
VERTEX_SNAP_TOLERANCE = 0.005
EDGE_PRECISION = 6

TILE_FAMILY = "dodecagonal-square-triangle"
SQUARE_KIND = "dodecagonal-square-triangle-square"
TRIANGLE_KIND = "dodecagonal-square-triangle-triangle"

RED_FILL = (0.541, 0.141, 0.133)
YELLOW_FILL = (1.0, 0.8, 0.4)
BLUE_FILL = (0.42, 0.451, 0.639)


class PatchCell(TypedDict):
    id: str
    kind: str
    center: tuple[float, float]
    vertices: tuple[tuple[float, float], ...]
    neighbors: tuple[str, ...]
    tile_family: str | None
    orientation_token: str | None
    chirality_token: str | None
    decoration_tokens: tuple[str, ...] | None


class AperiodicPatch(TypedDict):
    patch_depth: int
    width: int
    height: int
    cells: tuple[PatchCell, ...]


@dataclass(frozen=True)
class _SourceCell:
    index: int
    kind: str
    chirality: str | None
    vertices: tuple[tuple[float, float], ...]
    neighbors: tuple[int, ...]


def _edge_angle(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360.0


def _ordered_vertices(points: list[tuple[float, float]]) -> tuple[tuple[float, float], ...]:
    cx = sum(x for x, _ in points) / len(points)
    cy = sum(y for _, y in points) / len(points)
    cyclic = sorted(points, key=lambda point: math.atan2(point[1] - cy, point[0] - cx))
    return _rotate_vertices(tuple(cyclic))


def _rotate_vertices(
    vertices: tuple[tuple[float, float], ...],
) -> tuple[tuple[float, float], ...]:
    rotations: list[tuple[float, tuple[tuple[float, float], ...]]] = []
    for offset in range(len(vertices)):
        rotated = vertices[offset:] + vertices[:offset]
        angle = _edge_angle(rotated[0], rotated[1])
        rotations.append((round(angle, 6), tuple(rotated)))
    return min(rotations, key=lambda item: item[0])[1]


def _polygon_center(vertices: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    count = len(vertices)
    return (
        sum(x for x, _ in vertices) / count,
        sum(y for _, y in vertices) / count,
    )


def _extract_fill_vertices(drawing: dict) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for item in drawing["items"]:
        if item[0] == "l":
            points.append((item[1].x, item[1].y))
            points.append((item[2].x, item[2].y))
        elif item[0] == "re":
            rect = item[1]
            points.extend(
                (
                    (rect.x0, rect.y0),
                    (rect.x0, rect.y1),
                    (rect.x1, rect.y1),
                    (rect.x1, rect.y0),
                )
            )

    deduped: list[tuple[float, float]] = []
    seen: set[tuple[float, float]] = set()
    for point in points:
        if point in seen:
            continue
        seen.add(point)
        deduped.append(point)
    return deduped


def _classify_cell(fill: tuple[float, float, float], vertex_count: int) -> tuple[str, str | None]:
    if vertex_count == 4:
        return SQUARE_KIND, None
    if fill == RED_FILL:
        return TRIANGLE_KIND, "red"
    if fill == YELLOW_FILL:
        return TRIANGLE_KIND, "yellow"
    if fill == BLUE_FILL:
        return TRIANGLE_KIND, "blue"
    raise ValueError(f"unexpected triangle fill {fill}")


def _normalize_vertices(
    vertices: tuple[tuple[float, float], ...],
    *,
    origin: tuple[float, float],
    unit_scale: float,
) -> tuple[tuple[float, float], ...]:
    normalized = tuple(
        ((x - origin[0]) / unit_scale, (origin[1] - y) / unit_scale)
        for x, y in vertices
    )
    return _rotate_vertices(normalized)


def _orientation_token(vertices: tuple[tuple[float, float], ...]) -> str:
    angle = _edge_angle(vertices[0], vertices[1])
    snapped = int(round(angle / 30.0) * 30) % 360
    return str(snapped)


def _canonical_edge(
    left: tuple[float, float],
    right: tuple[float, float],
) -> tuple[tuple[float, float], tuple[float, float]]:
    rounded_left = (round(left[0], EDGE_PRECISION), round(left[1], EDGE_PRECISION))
    rounded_right = (round(right[0], EDGE_PRECISION), round(right[1], EDGE_PRECISION))
    return (
        (rounded_left, rounded_right)
        if rounded_left <= rounded_right
        else (rounded_right, rounded_left)
    )


def _cluster_points(
    points: set[tuple[float, float]],
) -> dict[tuple[float, float], tuple[float, float]]:
    clusters: list[list[tuple[float, float]]] = []
    point_cluster: dict[tuple[float, float], int] = {}
    for point in sorted(points):
        best_cluster_index: int | None = None
        best_distance: float | None = None
        for cluster_index, cluster_points in enumerate(clusters):
            center = _polygon_center(tuple(cluster_points))
            distance = math.dist(point, center)
            if distance > VERTEX_SNAP_TOLERANCE:
                continue
            if best_distance is None or distance < best_distance:
                best_cluster_index = cluster_index
                best_distance = distance
        if best_cluster_index is None:
            clusters.append([point])
            point_cluster[point] = len(clusters) - 1
            continue
        clusters[best_cluster_index].append(point)
        point_cluster[point] = best_cluster_index

    cluster_centers = tuple(_polygon_center(tuple(cluster)) for cluster in clusters)
    return {
        point: cluster_centers[cluster_index]
        for point, cluster_index in point_cluster.items()
    }


def _rebuild_neighbors(
    cells: dict[int, _SourceCell],
) -> dict[int, tuple[int, ...]]:
    edge_map: defaultdict[
        tuple[tuple[float, float], tuple[float, float]],
        list[int],
    ] = defaultdict(list)
    for index, cell in cells.items():
        for vertex_index, left in enumerate(cell.vertices):
            right = cell.vertices[(vertex_index + 1) % len(cell.vertices)]
            edge_map[_canonical_edge(left, right)].append(index)

    neighbor_map: defaultdict[int, set[int]] = defaultdict(set)
    for owners in edge_map.values():
        unique_owners = tuple(sorted(set(owners)))
        if len(unique_owners) != 2:
            continue
        left, right = unique_owners
        neighbor_map[left].add(right)
        neighbor_map[right].add(left)
    return {
        index: tuple(sorted(neighbor_map[index]))
        for index in cells
    }


@lru_cache(maxsize=1)
def _load_source_patch() -> tuple[dict[int, _SourceCell], tuple[float, float], float]:
    if not SOURCE_PATCH_PDF.exists():
        raise FileNotFoundError(f"missing literature source: {SOURCE_PATCH_PDF}")

    document = fitz.open(SOURCE_PATCH_PDF)
    try:
        page = document[0]
        unique_cells: dict[
            tuple[tuple[tuple[float, float], ...], tuple[float, float, float]],
            tuple[tuple[tuple[float, float], ...], tuple[float, float, float]],
        ] = {}
        for drawing in page.get_drawings():
            if drawing["type"] != "f":
                continue
            raw_vertices = _extract_fill_vertices(drawing)
            if len(raw_vertices) not in (3, 4):
                continue
            fill = tuple(round(channel, 3) for channel in drawing["fill"])
            ordered = _ordered_vertices(raw_vertices)
            unique_cells.setdefault((ordered, fill), (ordered, fill))
    finally:
        document.close()

    snap_map = _cluster_points(
        {
            vertex
            for vertices, _fill in unique_cells.values()
            for vertex in vertices
        }
    )

    snapped_cells: dict[int, _SourceCell] = {}
    for index, (vertices, fill) in enumerate(unique_cells.values()):
        snapped_vertices = _rotate_vertices(tuple(snap_map[vertex] for vertex in vertices))
        kind, chirality = _classify_cell(fill, len(snapped_vertices))
        snapped_cells[index] = _SourceCell(
            index=index,
            kind=kind,
            chirality=chirality,
            vertices=snapped_vertices,
            neighbors=(),
        )

    neighbors_by_index = _rebuild_neighbors(snapped_cells)
    cells = {
        index: _SourceCell(
            index=index,
            kind=cell.kind,
            chirality=cell.chirality,
            vertices=cell.vertices,
            neighbors=neighbors_by_index[index],
        )
        for index, cell in snapped_cells.items()
    }

    seed = cells[SEED_CELL_INDEX]
    seed_center = _polygon_center(seed.vertices)
    seed_scale = math.dist(seed.vertices[0], seed.vertices[1])
    return cells, seed_center, seed_scale


def build_dodecagonal_square_triangle_patch(patch_depth: int) -> AperiodicPatch:
    if patch_depth < 0:
        raise ValueError("patch_depth must be non-negative")
    if patch_depth > MAX_PATCH_DEPTH:
        raise ValueError(
            f"patch_depth {patch_depth} exceeds validated literature crop depth {MAX_PATCH_DEPTH}"
        )

    cells, seed_center, unit_scale = _load_source_patch()

    distances: dict[int, int] = {SEED_CELL_INDEX: 0}
    queue: deque[int] = deque([SEED_CELL_INDEX])
    while queue:
        current = queue.popleft()
        if distances[current] == patch_depth:
            continue
        for neighbor in cells[current].neighbors:
            if neighbor in distances:
                continue
            distances[neighbor] = distances[current] + 1
            queue.append(neighbor)

    selected_indexes = sorted(distances, key=lambda index: (distances[index], index))
    selected_set = set(selected_indexes)

    patch_cells: list[PatchCell] = []
    for index in selected_indexes:
        vertices = _normalize_vertices(
            cells[index].vertices,
            origin=seed_center,
            unit_scale=unit_scale,
        )
        center = _polygon_center(vertices)
        patch_cells.append(
            PatchCell(
                id=f"dst:lit:{index:05d}",
                kind=cells[index].kind,
                center=(round(center[0], 9), round(center[1], 9)),
                vertices=tuple((round(x, 9), round(y, 9)) for x, y in vertices),
                neighbors=tuple(
                    f"dst:lit:{neighbor:05d}"
                    for neighbor in cells[index].neighbors
                    if neighbor in selected_set
                ),
                tile_family=TILE_FAMILY,
                orientation_token=_orientation_token(vertices),
                chirality_token=cells[index].chirality,
                decoration_tokens=None,
            )
        )

    xs = [x for cell in patch_cells for x, _ in cell["vertices"]]
    ys = [y for cell in patch_cells for _, y in cell["vertices"]]
    width = math.ceil(max(xs) - min(xs))
    height = math.ceil(max(ys) - min(ys))
    return AperiodicPatch(
        patch_depth=patch_depth,
        width=width,
        height=height,
        cells=tuple(patch_cells),
    )
