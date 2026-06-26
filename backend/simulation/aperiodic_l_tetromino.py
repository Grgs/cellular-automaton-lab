"""L-tetromino rep-4 substitution tiling.

The L-tetromino (four unit squares in an L) is a rep-4 rep-tile: four
half-scale copies exactly tile a double-scale copy. Iterating that dissection
is a self-similar (limit-periodic) substitution tiling, the tetromino analogue
of the shipped ``chair`` (which is the L-*tromino* rep-4 substitution).

Geometry is exact on the integer lattice. The canonical tile occupies the unit
cells {(0,0), (0,1), (0,2), (1,0)} -- a vertical three-bar plus a foot -- with
outline ``_BASE_POLYGON``. The rep-4 dissection (``_CANONICAL_CHILDREN``) was
found by exhaustive exact cover of the doubled tile and is verified by the unit
tests (area conservation, congruence to the prototile, gap/overlap-free cover).

The substitution closes over exactly four orientations -- the Klein four-group
{identity, 180 deg rotation, and the two diagonal reflections} -- and every
tile yields one child of each orientation, so each orientation token is equally
represented at every depth >= 1.
"""

from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    L_TETROMINO_KIND,
    L_TETROMINO_TILE_FAMILY,
)
from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    PatchRecord,
    Vec,
    encode_float,
    patch_from_records,
    polygon_centroid,
    rounded_point,
)

# Outline of the canonical L-tetromino (cells {(0,0),(0,1),(0,2),(1,0)}).
_BASE_POLYGON: tuple[Vec, ...] = (
    Vec(0.0, 0.0),
    Vec(2.0, 0.0),
    Vec(2.0, 1.0),
    Vec(1.0, 1.0),
    Vec(1.0, 3.0),
    Vec(0.0, 3.0),
)

# A 2x2 integer matrix (a, b, c, d): (x, y) -> (a*x + b*y, c*x + d*y).
Matrix = tuple[int, int, int, int]

# The four orientations the substitution closes over (Klein four-group), keyed
# by a stable orientation token.
_ORIENTATIONS: dict[int, Matrix] = {
    0: (1, 0, 0, 1),  # identity
    1: (-1, 0, 0, -1),  # 180 degree rotation
    2: (0, 1, 1, 0),  # reflection across y = x
    3: (0, -1, -1, 0),  # reflection across y = -x
}
_ORIENTATION_TOKEN: dict[Matrix, int] = {matrix: token for token, matrix in _ORIENTATIONS.items()}

# Canonical rep-4 children as (matrix, translation) in the doubled-tile frame.
# Each child is matrix @ base_polygon + translation; halving the arrangement
# tiles the unit parent. Verified exhaustively (see tools scratchpad / tests).
_CANONICAL_CHILDREN: tuple[tuple[Matrix, tuple[int, int]], ...] = (
    ((0, 1, 1, 0), (0, 0)),
    ((1, 0, 0, 1), (0, 2)),
    ((-1, 0, 0, -1), (2, 6)),
    ((0, -1, -1, 0), (4, 2)),
)


def _matrix_multiply(left: Matrix, right: Matrix) -> Matrix:
    a, b, c, d = left
    e, f, g, h = right
    return (a * e + b * g, a * f + b * h, c * e + d * g, c * f + d * h)


def _matrix_apply(matrix: Matrix, x: float, y: float) -> tuple[float, float]:
    a, b, c, d = matrix
    return (a * x + b * y, c * x + d * y)


def _tile_polygon(
    matrix: Matrix, scale: float, offset_x: float, offset_y: float
) -> tuple[Vec, ...]:
    polygon: list[Vec] = []
    for vertex in _BASE_POLYGON:
        rotated_x, rotated_y = _matrix_apply(matrix, vertex.x, vertex.y)
        polygon.append(Vec(offset_x + scale * rotated_x, offset_y + scale * rotated_y))
    return tuple(polygon)


def _tile_id(path: str, token: int, scale: float, offset_x: float, offset_y: float) -> str:
    return (
        f"l-tetromino:{path}:o{token}:s{encode_float(scale)}:"
        f"{encode_float(offset_x)}:{encode_float(offset_y)}"
    )


def _tile_record(
    path: str, matrix: Matrix, scale: float, offset_x: float, offset_y: float
) -> PatchRecord:
    token = _ORIENTATION_TOKEN[matrix]
    polygon = _tile_polygon(matrix, scale, offset_x, offset_y)
    return {
        "id": _tile_id(path, token, scale, offset_x, offset_y),
        "kind": L_TETROMINO_KIND,
        "tile_family": L_TETROMINO_TILE_FAMILY,
        "center": rounded_point(polygon_centroid(polygon)),
        "vertices": tuple(rounded_point(vertex) for vertex in polygon),
        "orientation_token": str(token),
    }


def _collect_records(
    remaining_depth: int,
    matrix: Matrix,
    scale: float,
    offset_x: float,
    offset_y: float,
    path: str,
    records: list[PatchRecord],
) -> None:
    if remaining_depth <= 0:
        records.append(_tile_record(path, matrix, scale, offset_x, offset_y))
        return

    child_scale = scale / 2.0
    for index, (child_matrix, (grid_x, grid_y)) in enumerate(_CANONICAL_CHILDREN):
        composed = _matrix_multiply(matrix, child_matrix)
        shift_x, shift_y = _matrix_apply(matrix, grid_x, grid_y)
        _collect_records(
            remaining_depth - 1,
            composed,
            child_scale,
            offset_x + child_scale * shift_x,
            offset_y + child_scale * shift_y,
            f"{path}.child{index}",
            records,
        )


def collect_l_tetromino_records(patch_depth: int) -> list[PatchRecord]:
    resolved_depth = max(0, int(patch_depth))
    records: list[PatchRecord] = []
    _collect_records(resolved_depth, _ORIENTATIONS[0], 1.0, 0.0, 0.0, "root", records)
    return records


def build_l_tetromino_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    records = collect_l_tetromino_records(resolved_depth)
    return patch_from_records(
        resolved_depth,
        records,
        neighbor_mode="segment_overlap",
    )
