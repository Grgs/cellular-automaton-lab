from __future__ import annotations

import math
from dataclasses import dataclass

from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    PatchRecord,
    Vec,
    id_from_anchor,
    patch_from_records,
    polygon_centroid,
    rounded_point,
)


PHI = (1 + math.sqrt(5)) / 2


@dataclass(frozen=True)
class _LeafTile:
    kind: str
    vertices: tuple[Vec, ...]
    center: Vec
    anchor: Vec
    orientation: int


def _logo_forward(point: Vec, heading_degrees: float, distance: float) -> Vec:
    radians = math.radians(heading_degrees)
    return Vec(
        point.x + (distance * math.sin(radians)),
        point.y + (distance * math.cos(radians)),
    )


def _kite_vertices(anchor: Vec, heading: float, length: float) -> tuple[Vec, ...]:
    short_length = length / PHI
    vertices = [anchor]
    current = anchor
    current_heading = heading - 36
    current = _logo_forward(current, current_heading, length)
    vertices.append(current)
    current_heading += 108
    current = _logo_forward(current, current_heading, short_length)
    vertices.append(current)
    current_heading += 36
    current = _logo_forward(current, current_heading, short_length)
    vertices.append(current)
    return tuple(vertices)


def _dart_vertices(anchor: Vec, heading: float, length: float) -> tuple[Vec, ...]:
    short_length = length / PHI
    vertices = [anchor]
    current = anchor
    current_heading = heading - 36
    current = _logo_forward(current, current_heading, length)
    vertices.append(current)
    current_heading += 144
    current = _logo_forward(current, current_heading, short_length)
    vertices.append(current)
    current_heading -= 36
    current = _logo_forward(current, current_heading, short_length)
    vertices.append(current)
    return tuple(vertices)


def _inflate_p2_kite(
    anchor: Vec,
    heading: float,
    length: float,
    depth: int,
    tiles: list[_LeafTile],
) -> tuple[Vec, float]:
    if depth == 0:
        vertices = _kite_vertices(anchor, heading, length)
        tiles.append(
            _LeafTile(
                kind="kite",
                vertices=vertices,
                center=polygon_centroid(vertices),
                anchor=anchor,
                orientation=int(round(heading)),
            )
        )
        return anchor, heading

    short_length = length / PHI
    current_anchor = anchor
    current_heading = heading - 36
    current_anchor, current_heading = _inflate_p2_dart(current_anchor, current_heading, short_length, depth - 1, tiles)
    current_anchor = _logo_forward(current_anchor, current_heading, length)
    current_heading += 144
    current_anchor, current_heading = _inflate_p2_kite(current_anchor, current_heading, short_length, depth - 1, tiles)
    current_heading -= 18
    current_anchor = _logo_forward(current_anchor, current_heading, length * (2 * math.cos(3 * math.pi / 10)))
    current_heading += 162
    current_anchor, current_heading = _inflate_p2_kite(current_anchor, current_heading, short_length, depth - 1, tiles)
    current_heading -= 36
    current_anchor = _logo_forward(current_anchor, current_heading, length)
    current_heading += 180
    current_anchor, current_heading = _inflate_p2_dart(current_anchor, current_heading, short_length, depth - 1, tiles)
    current_heading -= 36
    return current_anchor, current_heading


def _inflate_p2_dart(
    anchor: Vec,
    heading: float,
    length: float,
    depth: int,
    tiles: list[_LeafTile],
) -> tuple[Vec, float]:
    if depth == 0:
        vertices = _dart_vertices(anchor, heading, length)
        tiles.append(
            _LeafTile(
                kind="dart",
                vertices=vertices,
                center=polygon_centroid(vertices),
                anchor=anchor,
                orientation=int(round(heading)),
            )
        )
        return anchor, heading

    short_length = length / PHI
    current_anchor = anchor
    current_heading = heading
    current_anchor, current_heading = _inflate_p2_kite(current_anchor, current_heading, short_length, depth - 1, tiles)
    current_heading -= 36
    current_anchor = _logo_forward(current_anchor, current_heading, length)
    current_heading += 180
    current_anchor, current_heading = _inflate_p2_dart(current_anchor, current_heading, short_length, depth - 1, tiles)
    current_heading -= 54
    current_anchor = _logo_forward(current_anchor, current_heading, length * (2 * math.cos(3 * math.pi / 10)))
    current_heading += 126
    current_anchor, current_heading = _inflate_p2_dart(current_anchor, current_heading, short_length, depth - 1, tiles)
    current_anchor = _logo_forward(current_anchor, current_heading, length)
    current_heading += 144
    return current_anchor, current_heading


def build_penrose_p2_patch(patch_depth: int) -> AperiodicPatch:
    root_length = PHI ** int(patch_depth)
    tiles: list[_LeafTile] = []
    anchor = Vec(0.0, 0.0)
    heading = 0.0
    for _ in range(5):
        anchor, heading = _inflate_p2_kite(anchor, heading, root_length, int(patch_depth), tiles)
        heading -= 72

    records: list[PatchRecord] = []
    for tile in tiles:
        rounded_vertices = tuple(rounded_point(vertex) for vertex in tile.vertices)
        center = rounded_point(tile.center)
        records.append(
            {
                "id": id_from_anchor("p2k" if tile.kind == "kite" else "p2d", tile.anchor, tile.orientation),
                "kind": tile.kind,
                "center": center,
                "vertices": rounded_vertices,
            }
        )
    return patch_from_records(patch_depth, records)
