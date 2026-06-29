"""P-pentomino rep-4 substitution tiling.

The P-pentomino (a 2x2 square block plus one unit cell on top) is the *unique*
rep-4 pentomino: four half-scale copies exactly tile a double-scale copy. Every
other pentomino (L, Y, F, T, N, W, Z) fails rep-4, verified by exhaustive exact
cover of the doubled tile. Iterating the dissection is a self-similar
(limit-periodic) substitution tiling, the pentomino member of the rep-4
polyomino series alongside the L-tromino ``chair`` and the ``l-tetromino``.

Geometry is exact on the integer lattice. The canonical tile occupies the unit
cells {(0,0), (1,0), (0,1), (1,1), (0,2)} with outline ``_BASE_POLYGON``. The
rep-4 dissection (``_CANONICAL_CHILDREN``) was found by exhaustive exact cover
of the doubled tile and re-derived in the geometric (polygon) convention so the
affine recursion reproduces it exactly; the unit tests assert area conservation,
congruence to the prototile, and a gap/overlap-free cover.

The rendered representative patch starts from two P-pentomino supertiles that
form a compact 5-by-2 rectangle, then applies the same substitution to each
root, so the default view fills the canvas instead of a lone pentomino.

Unlike the L-tetromino (whose substitution closes over the four-element Klein
group), the P-pentomino is chiral, so its substitution closes over the full
eight-element dihedral group D4 -- every rotation and reflection appears.
"""

from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    P_PENTOMINO_KIND,
    P_PENTOMINO_TILE_FAMILY,
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

# Outline of the canonical P-pentomino (cells {(0,0),(1,0),(0,1),(1,1),(0,2)}).
_BASE_POLYGON: tuple[Vec, ...] = (
    Vec(0.0, 0.0),
    Vec(2.0, 0.0),
    Vec(2.0, 2.0),
    Vec(1.0, 2.0),
    Vec(1.0, 3.0),
    Vec(0.0, 3.0),
)

# A 2x2 integer matrix (a, b, c, d): (x, y) -> (a*x + b*y, c*x + d*y).
Matrix = tuple[int, int, int, int]

# All eight dihedral (D4) orientations the substitution closes over, keyed by a
# stable orientation token. 0-3 are rotations, 4-7 are reflections.
_ORIENTATIONS: dict[int, Matrix] = {
    0: (1, 0, 0, 1),  # identity
    1: (0, -1, 1, 0),  # 90 degree rotation
    2: (-1, 0, 0, -1),  # 180 degree rotation
    3: (0, 1, -1, 0),  # 270 degree rotation
    4: (-1, 0, 0, 1),  # reflection across the y axis
    5: (1, 0, 0, -1),  # reflection across the x axis
    6: (0, 1, 1, 0),  # reflection across y = x
    7: (0, -1, -1, 0),  # reflection across y = -x
}
_ORIENTATION_TOKEN: dict[Matrix, int] = {matrix: token for token, matrix in _ORIENTATIONS.items()}

# Two canonical P-pentomino supertiles arranged as a 5x2 horizontal rectangle.
# Each root is substituted independently by the same rep-4 rule.
_DEFAULT_ROOT_SEEDS: tuple[tuple[str, Matrix, float, float], ...] = (
    ("root0", _ORIENTATIONS[1], 5.0, 0.0),
    ("root1", _ORIENTATIONS[3], 0.0, 2.0),
)

# Canonical rep-4 children as (matrix, translation) in the doubled-tile frame.
# Each child is matrix @ base_polygon + translation; halving the arrangement
# tiles the unit parent. Derived in the geometric (polygon) convention and
# verified exhaustively (see tools scratchpad / tests).
_CANONICAL_CHILDREN: tuple[tuple[Matrix, tuple[int, int]], ...] = (
    ((1, 0, 0, -1), (0, 3)),
    ((1, 0, 0, -1), (0, 6)),
    ((0, -1, 1, 0), (4, 0)),
    ((0, -1, -1, 0), (4, 4)),
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
        f"p-pentomino:{path}:o{token}:s{encode_float(scale)}:"
        f"{encode_float(offset_x)}:{encode_float(offset_y)}"
    )


def _tile_record(
    path: str, matrix: Matrix, scale: float, offset_x: float, offset_y: float
) -> PatchRecord:
    token = _ORIENTATION_TOKEN[matrix]
    polygon = _tile_polygon(matrix, scale, offset_x, offset_y)
    return {
        "id": _tile_id(path, token, scale, offset_x, offset_y),
        "kind": P_PENTOMINO_KIND,
        "tile_family": P_PENTOMINO_TILE_FAMILY,
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


def collect_p_pentomino_records(patch_depth: int) -> list[PatchRecord]:
    resolved_depth = max(0, int(patch_depth))
    records: list[PatchRecord] = []
    for path, matrix, offset_x, offset_y in _DEFAULT_ROOT_SEEDS:
        _collect_records(resolved_depth, matrix, 1.0, offset_x, offset_y, path, records)
    return records


def _collect_canonical_p_pentomino_records(patch_depth: int) -> list[PatchRecord]:
    resolved_depth = max(0, int(patch_depth))
    records: list[PatchRecord] = []
    _collect_records(resolved_depth, _ORIENTATIONS[0], 1.0, 0.0, 0.0, "root", records)
    return records


def build_p_pentomino_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    records = collect_p_pentomino_records(resolved_depth)
    return patch_from_records(
        resolved_depth,
        records,
        neighbor_mode="segment_overlap",
    )
