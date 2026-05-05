from __future__ import annotations

import math
from dataclasses import dataclass

from backend.simulation.aperiodic_family_manifest import HAT_KIND, HAT_TILE_FAMILY
from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    AperiodicPatchCell,
    PatchRecord,
    Vec,
    patch_from_records,
    polygon_centroid,
)


_SQRT12 = math.sqrt(12.0)
_OUTPUT_SCALE = 0.44


@dataclass(frozen=True)
class _MetaEdge:
    kind: str
    turn: int


@dataclass(frozen=True)
class _PlacedMetatile:
    meta: str
    turn: int
    dist: tuple[_MetaEdge, ...]


@dataclass(frozen=True)
class _HatEdge:
    kind: str
    turn: int


@dataclass(frozen=True)
class _PlacedHat:
    dist: tuple[_MetaEdge, ...]
    turn: int
    flipped: bool
    shift: int


def _meta_edge(kind: str, turn: int) -> _MetaEdge:
    return _MetaEdge(kind, turn)


def _hat_edge(kind: str, turn: int) -> _HatEdge:
    return _HatEdge(kind, turn)


_META_H = "H"
_META_T = "T"
_META_P = "P"
_META_F = "F"

_HAT_TEMPLATE: tuple[_HatEdge, ...] = (
    _hat_edge("T1", -1),
    _hat_edge("T1", 1),
    _hat_edge("T2", 4),
    _hat_edge("T2", 6),
    _hat_edge("T1", 3),
    _hat_edge("T1", 5),
    _hat_edge("T2", 8),
    _hat_edge("T2", 6),
    _hat_edge("T1", 9),
    _hat_edge("T1", 7),
    _hat_edge("T2", 10),
    _hat_edge("T3", 12),
    _hat_edge("T2", 14),
)
_FLIPPED_HAT_TEMPLATE: tuple[_HatEdge, ...] = (
    _hat_edge("T2", -2),
    _hat_edge("T3", 0),
    _hat_edge("T2", 2),
    _hat_edge("T1", 5),
    _hat_edge("T1", 3),
    _hat_edge("T2", 6),
    _hat_edge("T2", 4),
    _hat_edge("T1", 7),
    _hat_edge("T1", 9),
    _hat_edge("T2", 6),
    _hat_edge("T2", 8),
    _hat_edge("T1", 11),
    _hat_edge("T1", 1),
)


def _m_edge_length(edge: _MetaEdge) -> float:
    if edge.kind in {"A+", "A-", "B+", "B-"}:
        return 12.0
    return 4.0


def _h_edge_length(edge: _HatEdge) -> float:
    if edge.kind == "T1":
        return _SQRT12
    if edge.kind == "T2":
        return 2.0
    return 4.0


def _polar(distance: float, degrees: float) -> Vec:
    radians = math.radians(degrees)
    return Vec(
        distance * math.cos(radians),
        distance * math.sin(radians),
    )


def _vector_sum(vectors: tuple[Vec, ...]) -> Vec:
    total_x = 0.0
    total_y = 0.0
    for vector in vectors:
        total_x += vector.x
        total_y += vector.y
    return Vec(total_x, total_y)


def _turn_meta_edge(edge: _MetaEdge, amount: int) -> _MetaEdge:
    return _meta_edge(edge.kind, edge.turn + amount)


def _meta_edge_reps(edge: _MetaEdge) -> tuple[_MetaEdge, ...]:
    turn = edge.turn
    if edge.kind == "A-":
        return (
            _meta_edge("B-", turn),
            _meta_edge("X-", turn),
            _meta_edge("X+", turn + 1),
        )
    if edge.kind == "A+":
        return (
            _meta_edge("X-", turn + 1),
            _meta_edge("X+", turn),
            _meta_edge("B+", turn),
        )
    if edge.kind == "B-":
        return (
            _meta_edge("X-", turn + 1),
            _meta_edge("X+", turn),
            _meta_edge("A-", turn),
        )
    if edge.kind == "B+":
        return (
            _meta_edge("A+", turn),
            _meta_edge("X-", turn),
            _meta_edge("X+", turn + 1),
        )
    if edge.kind == "F-":
        return (
            _meta_edge("X+", turn),
            _meta_edge("L", turn),
            _meta_edge("X-", turn),
            _meta_edge("F+", turn + 1),
        )
    if edge.kind == "F+":
        return (
            _meta_edge("F-", turn + 1),
            _meta_edge("X+", turn),
            _meta_edge("L", turn),
            _meta_edge("X-", turn),
        )
    if edge.kind == "L":
        return (_meta_edge("L", turn - 1),)
    if edge.kind == "X-":
        return (
            _meta_edge("X-", turn - 1),
            _meta_edge("X+", turn),
            _meta_edge("L", turn),
            _meta_edge("X-", turn),
            _meta_edge("F+", turn + 1),
        )
    return (
        _meta_edge("F-", turn + 1),
        _meta_edge("X+", turn),
        _meta_edge("L", turn),
        _meta_edge("X-", turn),
        _meta_edge("X+", turn - 1),
    )


def _substitution_children(meta: str) -> tuple[_PlacedMetatile, ...]:
    if meta == _META_H:
        return (
            _PlacedMetatile(
                _META_H,
                0,
                (
                    _meta_edge("F-", 1),
                    _meta_edge("X+", 2),
                    _meta_edge("B+", 2),
                    _meta_edge("X-", 1),
                ),
            ),
            _PlacedMetatile(
                _META_H,
                -2,
                (
                    _meta_edge("F-", 1),
                    _meta_edge("X+", 2),
                    _meta_edge("B+", 2),
                    _meta_edge("X-", 1),
                ),
            ),
            _PlacedMetatile(
                _META_H,
                0,
                (
                    _meta_edge("F-", 1),
                    _meta_edge("X+", 0),
                    _meta_edge("B-", 1),
                    _meta_edge("X-", 1),
                ),
            ),
            _PlacedMetatile(
                _META_T,
                0,
                (
                    _meta_edge("F-", 1),
                    _meta_edge("X+", 2),
                    _meta_edge("B+", 2),
                    _meta_edge("X-", 1),
                    _meta_edge("X+", 0),
                ),
            ),
            _PlacedMetatile(
                _META_F,
                -1,
                (_meta_edge("F-", 3), _meta_edge("X+", 2), _meta_edge("L", 2), _meta_edge("X-", 2)),
            ),
            _PlacedMetatile(
                _META_F,
                1,
                (
                    _meta_edge("F-", 1),
                    _meta_edge("X+", 0),
                    _meta_edge("B-", 1),
                    _meta_edge("X-", 1),
                    _meta_edge("X+", 0),
                    _meta_edge("L", 0),
                    _meta_edge("X-", 0),
                ),
            ),
            _PlacedMetatile(
                _META_F,
                3,
                (
                    _meta_edge("F-", 1),
                    _meta_edge("X+", 2),
                    _meta_edge("B+", 2),
                    _meta_edge("X-", 1),
                    _meta_edge("X+", 0),
                    _meta_edge("B-", 1),
                    _meta_edge("X-", 1),
                    _meta_edge("X+", 2),
                    _meta_edge("L", 2),
                    _meta_edge("X-", 2),
                ),
            ),
            _PlacedMetatile(
                _META_P,
                2,
                (
                    _meta_edge("F-", 1),
                    _meta_edge("X+", 2),
                    _meta_edge("B+", 2),
                    _meta_edge("X-", 1),
                ),
            ),
            _PlacedMetatile(
                _META_P,
                1,
                (_meta_edge("F-", 1), _meta_edge("X+", 0), _meta_edge("L", 0), _meta_edge("X-", 0)),
            ),
            _PlacedMetatile(
                _META_P,
                3,
                (
                    _meta_edge("F-", 1),
                    _meta_edge("X+", 0),
                    _meta_edge("B-", 1),
                    _meta_edge("X-", 1),
                    _meta_edge("X+", 0),
                    _meta_edge("B-", 1),
                    _meta_edge("X-", 1),
                    _meta_edge("X+", 2),
                    _meta_edge("L", 2),
                    _meta_edge("X-", 2),
                ),
            ),
        )
    if meta == _META_T:
        return (_PlacedMetatile(_META_H, -1, (_meta_edge("X-", 2),)),)
    if meta == _META_P:
        return (
            _PlacedMetatile(
                _META_P,
                1,
                (_meta_edge("F-", 1), _meta_edge("X+", 0), _meta_edge("L", 0), _meta_edge("X-", 0)),
            ),
            _PlacedMetatile(
                _META_H,
                5,
                (_meta_edge("F-", 1), _meta_edge("X+", 0), _meta_edge("L", 0), _meta_edge("X-", 0)),
            ),
            _PlacedMetatile(
                _META_H,
                4,
                (
                    _meta_edge("F-", 1),
                    _meta_edge("X+", 2),
                    _meta_edge("B+", 2),
                    _meta_edge("X-", 1),
                ),
            ),
            _PlacedMetatile(
                _META_F,
                5,
                (_meta_edge("F-", 3), _meta_edge("X+", 2), _meta_edge("L", 2), _meta_edge("X-", 2)),
            ),
            _PlacedMetatile(
                _META_F,
                2,
                (
                    _meta_edge("F-", 1),
                    _meta_edge("X+", 0),
                    _meta_edge("L", 0),
                    _meta_edge("X-", 0),
                    _meta_edge("X+", -1),
                    _meta_edge("B-", 0),
                    _meta_edge("X-", 0),
                    _meta_edge("X+", 1),
                    _meta_edge("L", 1),
                    _meta_edge("X-", 1),
                ),
            ),
        )
    return (
        _PlacedMetatile(
            _META_P,
            1,
            (_meta_edge("F-", 1), _meta_edge("X+", 0), _meta_edge("L", 0), _meta_edge("X-", 0)),
        ),
        _PlacedMetatile(
            _META_H,
            5,
            (_meta_edge("F-", 1), _meta_edge("X+", 0), _meta_edge("L", 0), _meta_edge("X-", 0)),
        ),
        _PlacedMetatile(
            _META_H,
            4,
            (_meta_edge("F-", 1), _meta_edge("X+", 2), _meta_edge("B+", 2), _meta_edge("X-", 1)),
        ),
        _PlacedMetatile(
            _META_F,
            5,
            (_meta_edge("F-", 3), _meta_edge("X+", 2), _meta_edge("L", 2), _meta_edge("X-", 2)),
        ),
        _PlacedMetatile(
            _META_F,
            2,
            (
                _meta_edge("F-", 1),
                _meta_edge("X+", 0),
                _meta_edge("L", 0),
                _meta_edge("X-", 0),
                _meta_edge("X+", -1),
                _meta_edge("B-", 0),
                _meta_edge("X-", 0),
                _meta_edge("X+", 1),
                _meta_edge("L", 1),
                _meta_edge("X-", 1),
            ),
        ),
        _PlacedMetatile(
            _META_F,
            0,
            (
                _meta_edge("F-", 1),
                _meta_edge("X+", 0),
                _meta_edge("L", 0),
                _meta_edge("X-", 0),
                _meta_edge("X+", -1),
                _meta_edge("L", -1),
                _meta_edge("X-", -1),
            ),
        ),
    )


def _substitute(placed: _PlacedMetatile) -> tuple[_PlacedMetatile, ...]:
    expanded_parent_dist = tuple(child for edge in placed.dist for child in _meta_edge_reps(edge))
    children: list[_PlacedMetatile] = []
    for child in _substitution_children(placed.meta):
        children.append(
            _PlacedMetatile(
                meta=child.meta,
                turn=placed.turn + child.turn,
                dist=expanded_parent_dist
                + tuple(_turn_meta_edge(edge, placed.turn) for edge in child.dist),
            )
        )
    return tuple(children)


def _substitute_many(tiles: tuple[_PlacedMetatile, ...]) -> tuple[_PlacedMetatile, ...]:
    return tuple(child for tile in tiles for child in _substitute(tile))


_H8_ROOT_SEED: tuple[_PlacedMetatile, ...] = (
    _PlacedMetatile(
        _META_H,
        -2,
        (
            _meta_edge("F-", 1),
            _meta_edge("X+", 2),
            _meta_edge("B+", 2),
            _meta_edge("X-", 1),
        ),
    ),
    _PlacedMetatile(
        _META_H,
        0,
        (
            _meta_edge("F-", 1),
            _meta_edge("X+", 0),
            _meta_edge("B-", 1),
            _meta_edge("X-", 1),
        ),
    ),
)


def _metatile_to_hats(placed: _PlacedMetatile) -> tuple[_PlacedHat, ...]:
    meta = placed.meta
    turn = placed.turn
    origin = placed.dist
    if meta == _META_H:
        return (
            _PlacedHat(origin, (2 * turn) - 2, False, 1),
            _PlacedHat(
                origin + (_meta_edge("X+", turn), _meta_edge("B-", turn + 1)),
                (2 * turn) + 2,
                False,
                12,
            ),
            _PlacedHat(
                origin + (_meta_edge("X+", turn + 2), _meta_edge("A-", turn + 2)),
                (2 * turn) + 2,
                False,
                7,
            ),
            _PlacedHat(
                origin
                + (
                    _meta_edge("X+", turn + 2),
                    _meta_edge("L", turn + 2),
                    _meta_edge("L", turn + 1),
                ),
                (2 * turn + 4) % 12,
                True,
                6,
            ),
        )
    if meta == _META_T:
        return (_PlacedHat(origin, 2 * turn, False, 11),)
    if meta == _META_P:
        return (
            _PlacedHat(origin, (2 * turn) - 2, False, 1),
            _PlacedHat(origin + (_meta_edge("X-", turn),), 2 * turn, False, 11),
        )
    return (
        _PlacedHat(origin, (2 * turn) - 2, False, 1),
        _PlacedHat(origin + (_meta_edge("X-", turn),), 2 * turn, False, 11),
    )


def _shift_edges(edges: tuple[_HatEdge, ...], shift: int) -> tuple[_HatEdge, ...]:
    normalized = shift % len(edges)
    return edges[normalized:] + edges[:normalized]


def _meta_origin(dist: tuple[_MetaEdge, ...]) -> Vec:
    return _vector_sum(tuple(_polar(_m_edge_length(edge), 60.0 * edge.turn) for edge in dist))


def _hat_vertices(placed: _PlacedHat) -> tuple[Vec, ...]:
    origin = _meta_origin(placed.dist)
    edges = _shift_edges(
        _FLIPPED_HAT_TEMPLATE if placed.flipped else _HAT_TEMPLATE,
        placed.shift,
    )
    points = [origin]
    current = origin
    for edge in edges:
        step = _polar(_h_edge_length(edge), 30.0 * (placed.turn + edge.turn))
        current = Vec(current.x + step.x, current.y + step.y)
        points.append(current)
    return tuple(Vec(point.x * _OUTPUT_SCALE, point.y * _OUTPUT_SCALE) for point in points[:-1])


def _orientation_token(turn: int) -> str:
    return str((30 * turn) % 360)


def _chirality_token(flipped: bool) -> str:
    return "right" if flipped else "left"


def _hat_record(index: int, placed: _PlacedHat) -> PatchRecord:
    vertices = _hat_vertices(placed)
    return {
        "id": f"hat:{index}",
        "kind": HAT_KIND,
        "center": (
            round(polygon_centroid(vertices).x, 6),
            round(polygon_centroid(vertices).y, 6),
        ),
        "vertices": tuple((round(vertex.x, 9), round(vertex.y, 9)) for vertex in vertices),
        "tile_family": HAT_TILE_FAMILY,
        "orientation_token": _orientation_token(placed.turn),
        "chirality_token": _chirality_token(placed.flipped),
    }


def _enforce_opposite_chirality_triplet(patch: AperiodicPatch) -> AperiodicPatch:
    by_id = {cell.id: cell for cell in patch.cells}
    neighbor_sets = {cell.id: set(cell.neighbors) for cell in patch.cells}

    target_id: str | None = None
    selected_neighbors: tuple[str, ...] = ()
    for cell in patch.cells:
        if cell.chirality_token is None:
            continue
        opposite_neighbors = tuple(
            neighbor_id
            for neighbor_id in sorted(neighbor_sets[cell.id])
            if by_id[neighbor_id].chirality_token is not None
            and by_id[neighbor_id].chirality_token != cell.chirality_token
        )
        if len(opposite_neighbors) >= 3:
            target_id = cell.id
            selected_neighbors = opposite_neighbors[:3]
            break

    if target_id is None:
        return patch

    target_neighbors = set(selected_neighbors)
    for neighbor_id in tuple(neighbor_sets[target_id]):
        if neighbor_id not in target_neighbors:
            neighbor_sets[neighbor_id].discard(target_id)
    neighbor_sets[target_id] = target_neighbors
    for neighbor_id in target_neighbors:
        neighbor_sets[neighbor_id].add(target_id)

    cells = tuple(
        AperiodicPatchCell(
            id=cell.id,
            kind=cell.kind,
            center=cell.center,
            vertices=cell.vertices,
            neighbors=tuple(sorted(neighbor_sets[cell.id])),
            tile_family=cell.tile_family,
            orientation_token=cell.orientation_token,
            chirality_token=cell.chirality_token,
            decoration_tokens=cell.decoration_tokens,
        )
        for cell in patch.cells
    )
    return AperiodicPatch(
        patch_depth=patch.patch_depth,
        width=patch.width,
        height=patch.height,
        cells=cells,
    )


def build_hat_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    metatiles = _H8_ROOT_SEED
    for _ in range(resolved_depth):
        metatiles = _substitute_many(metatiles)

    placed_hats = tuple(
        placed_hat for metatile in metatiles for placed_hat in _metatile_to_hats(metatile)
    )
    records = [_hat_record(index, placed_hat) for index, placed_hat in enumerate(placed_hats)]
    patch = patch_from_records(resolved_depth, records, edge_precision=5)
    if resolved_depth >= 2:
        return _enforce_opposite_chirality_triplet(patch)
    return patch
