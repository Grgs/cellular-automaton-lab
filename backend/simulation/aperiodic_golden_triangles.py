from __future__ import annotations

import math

from backend.simulation.aperiodic_support import (
    PatchRecord,
    Vec,
    polygon_centroid,
    rounded_point,
)

PHI = (1 + math.sqrt(5)) / 2


def triangle_chirality(
    vertices: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
) -> str:
    (ax, ay), (bx, by), (cx, cy) = vertices
    area_twice = ((bx - ax) * (cy - ay)) - ((cx - ax) * (by - ay))
    return "left" if area_twice >= 0 else "right"


def triangle_orientation_token(
    vertices: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
) -> str:
    edges: list[tuple[float, tuple[float, float], tuple[float, float]]] = []
    for index, start in enumerate(vertices):
        end = vertices[(index + 1) % len(vertices)]
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        edges.append((dx * dx + dy * dy, start, end))
    _, start, end = max(edges, key=lambda item: item[0])
    angle = math.degrees(math.atan2(end[1] - start[1], end[0] - start[0]))
    return str(int(round(angle)) % 360)


def triangle_record(
    *,
    cell_id: str,
    kind: str,
    vertices: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
    tile_family: str,
    orientation_token: str | None = None,
    chirality_token: str | None = None,
) -> PatchRecord:
    rounded_vertices = [rounded_point(vertex) for vertex in vertices]
    triangle_vertices: tuple[
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
    ] = (rounded_vertices[0], rounded_vertices[1], rounded_vertices[2])
    centroid = polygon_centroid(tuple(Vec(x, y) for x, y in triangle_vertices))
    return {
        "id": cell_id,
        "kind": kind,
        "center": rounded_point(centroid),
        "vertices": triangle_vertices,
        "tile_family": tile_family,
        "orientation_token": (
            orientation_token
            if orientation_token is not None
            else triangle_orientation_token(triangle_vertices)
        ),
        "chirality_token": (
            chirality_token
            if chirality_token is not None
            else triangle_chirality(triangle_vertices)
        ),
    }
