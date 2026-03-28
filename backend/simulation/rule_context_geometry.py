from __future__ import annotations

from math import pi, sqrt
from collections.abc import Iterable

from backend.simulation.topology import LatticeCell, LatticeTopology, parse_regular_cell_id
from backend.simulation.topology_catalog import EDGE_ADJACENCY, get_topology_variant_for_geometry

_CLOCKWISE_START = pi / 2


def normalize_angle(angle: float) -> float:
    while angle <= -pi:
        angle += 2 * pi
    while angle > pi:
        angle -= 2 * pi
    return angle


def clockwise_sort_key(angle: float) -> float:
    return (_CLOCKWISE_START - angle) % (2 * pi)


def triangle_vertices(x: int, y: int) -> tuple[tuple[float, float], ...]:
    side = 1.0
    height = (sqrt(3) * side) / 2.0
    horizontal_pitch = side / 2.0
    left_x = x * horizontal_pitch
    top_y = y * height
    if (x + y) % 2 == 0:
        return (
            (left_x, top_y + height),
            (left_x + (side / 2.0), top_y),
            (left_x + side, top_y + height),
        )
    return (
        (left_x, top_y),
        (left_x + side, top_y),
        (left_x + (side / 2.0), top_y + height),
    )


def hex_center(x: int, y: int) -> tuple[float, float]:
    radius = 0.5
    hex_width = sqrt(3) * radius
    vertical_pitch = 0.75
    return (
        (x * hex_width) + ((y % 2) * (hex_width / 2.0)),
        y * vertical_pitch,
    )


def hex_vertices(x: int, y: int) -> tuple[tuple[float, float], ...]:
    center_x, center_y = hex_center(x, y)
    radius = 0.5
    half_width = (sqrt(3) * radius) / 2.0
    return (
        (center_x, center_y - radius),
        (center_x + half_width, center_y - (radius / 2.0)),
        (center_x + half_width, center_y + (radius / 2.0)),
        (center_x, center_y + radius),
        (center_x - half_width, center_y + (radius / 2.0)),
        (center_x - half_width, center_y - (radius / 2.0)),
    )


def square_vertices(x: int, y: int) -> tuple[tuple[float, float], ...]:
    left = float(x)
    top = float(y)
    return (
        (left, top),
        (left + 1.0, top),
        (left + 1.0, top + 1.0),
        (left, top + 1.0),
    )


def regular_kind(geometry: str, x: int, y: int) -> str:
    if geometry == "hex":
        return "hexagon"
    if geometry == "triangle":
        return "triangle-up" if (x + y) % 2 == 0 else "triangle-down"
    return "square"


def regular_geometry(
    geometry: str,
    x: int,
    y: int,
) -> tuple[str, tuple[float, float], tuple[tuple[float, float], ...] | None]:
    if geometry == "hex":
        center = hex_center(x, y)
        return regular_kind(geometry, x, y), center, hex_vertices(x, y)
    if geometry == "triangle":
        vertices = triangle_vertices(x, y)
        center = (
            sum(vertex[0] for vertex in vertices) / 3.0,
            sum(vertex[1] for vertex in vertices) / 3.0,
        )
        return regular_kind(geometry, x, y), center, vertices

    vertices = square_vertices(x, y)
    center = (x + 0.5, y + 0.5)
    return regular_kind(geometry, x, y), center, vertices


def cell_regular_coordinates(cell: LatticeCell) -> tuple[int, int] | None:
    return parse_regular_cell_id(cell.id)


def cell_geometry(topology: LatticeTopology, cell: LatticeCell) -> tuple[str, tuple[float, float], tuple[tuple[float, float], ...] | None]:
    regular_coordinates = cell_regular_coordinates(cell)
    if cell.center is not None:
        return (
            (
                cell.kind
                if cell.kind != "cell" or regular_coordinates is None
                else regular_kind(topology.geometry, regular_coordinates[0], regular_coordinates[1])
            ),
            cell.center,
            cell.vertices,
        )
    if regular_coordinates is None:
        raise ValueError(f"Cell {cell.id!r} is missing geometry metadata and is not a regular cell id.")
    return regular_geometry(topology.geometry, regular_coordinates[0], regular_coordinates[1])


def board_bounds(
    vertex_sets: Iterable[tuple[tuple[float, float], ...] | None],
    centers: Iterable[tuple[float, float]],
) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for vertices in vertex_sets:
        if not vertices:
            continue
        xs.extend(vertex[0] for vertex in vertices)
        ys.extend(vertex[1] for vertex in vertices)
    if not xs or not ys:
        centers_list = list(centers)
        xs = [center[0] for center in centers_list]
        ys = [center[1] for center in centers_list]
    return (
        min(xs, default=0.0),
        min(ys, default=0.0),
        max(xs, default=0.0),
        max(ys, default=0.0),
    )


def topology_adjacency_mode(topology: LatticeTopology) -> str:
    try:
        return get_topology_variant_for_geometry(topology.geometry).adjacency_mode
    except KeyError:
        return EDGE_ADJACENCY
