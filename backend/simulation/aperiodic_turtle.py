"""Generator for the Turtle aperiodic monotile.

The Turtle and the Hat are two members of the same continuum of aperiodic
monotiles ``Tile(a, b)`` described in Smith, Myers, Kaplan and
Goodman-Strauss, "An aperiodic monotile" (arXiv:2303.10798). Every member is
a 14-edge polygon (two edges are collinear, so it reads as a 13-edge outline)
whose edges take one of two lengths ``a`` or ``b``. The Hat is ``Tile(1,
sqrt(3))`` and the Turtle is ``Tile(sqrt(3), 1)`` -- the same shape with the
two edge lengths exchanged.

Crucially, the whole family shares one combinatorial tiling: as ``(a, b)``
varies continuously the tiles deform but adjacency is invariant. That lets us
build the Turtle exactly from the already-verified Hat tiling
(:mod:`backend.simulation.aperiodic_hat`) instead of re-deriving the metatile
geometry:

1. Build the Hat patch at the requested depth.
2. Classify every tile edge as an ``a`` edge or a ``b`` edge by its length.
3. Re-integrate vertex positions over the patch's shared-edge graph, scaling
   each ``a`` edge by ``sqrt(3)`` and each ``b`` edge by ``1/sqrt(3)``. This
   maps ``Tile(1, sqrt(3))`` to ``Tile(sqrt(3), 1)``.

The re-integration is path independent because each edge class closes
independently around every cell (the "balance" property of the family), so the
Turtle vertex assigned to a shared Hat vertex is well defined. The walk itself
is the shared :func:`edge_scaled_vertex_map` helper, which deforms any tiling by
rescaling edges per length class; this module only supplies the Hat-specific
classification. Because the deformation only rescales by edge class -- a
rotation/reflection invariant -- it commutes with the Hat's orientation and
chirality structure, so those tokens and the Hat's neighbour graph carry over
unchanged.
"""

from __future__ import annotations

import math

from backend.simulation.aperiodic_family_manifest import TURTLE_KIND, TURTLE_TILE_FAMILY
from backend.simulation.aperiodic_hat import _OUTPUT_SCALE, build_hat_patch
from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    AperiodicPatchCell,
    edge_scaled_vertex_map,
    patch_from_cells,
    polygon_centroid,
)
from backend.simulation.aperiodic_support import Vec as _Vec

_SQRT3 = math.sqrt(3.0)

# Hat edge lengths after the Hat module's output scale. The Hat is Tile(1,
# sqrt(3)); its "a" (short) edges appear at the unit length and once doubled on
# the single collinear long edge, while its "b" edges appear at the sqrt(3)
# length.
_A_SHORT = 2.0 * _OUTPUT_SCALE
_A_LONG = 4.0 * _OUTPUT_SCALE
_B_LENGTH = 2.0 * _SQRT3 * _OUTPUT_SCALE

# Per-class scale factors taking Tile(1, sqrt(3)) (Hat) to Tile(sqrt(3), 1)
# (Turtle): a edges grow by sqrt(3), b edges shrink by 1/sqrt(3).
_A_SCALE = _SQRT3
_B_SCALE = 1.0 / _SQRT3

# Vertex-identity rounding for the shared-edge graph. The smallest Hat feature
# is well above 0.1, so rounding to seven places coalesces shared endpoints
# without merging distinct vertices.
_VERTEX_KEY_PRECISION = 7
_OUTPUT_PRECISION = 9

_Point = tuple[float, float]


def _edge_scale(start: _Point, end: _Point) -> float:
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    tolerance = 1e-3 * max(1.0, length)
    if abs(length - _A_SHORT) <= tolerance or abs(length - _A_LONG) <= tolerance:
        return _A_SCALE
    if abs(length - _B_LENGTH) <= tolerance:
        return _B_SCALE
    raise ValueError(
        f"Hat edge length {length:.6f} is neither an a edge ({_A_SHORT:.6f}/{_A_LONG:.6f}) "
        f"nor a b edge ({_B_LENGTH:.6f}); cannot map it onto the Turtle continuum."
    )


def _retag_id(hat_id: str) -> str:
    # Hat ids are "hat:<index>"; keep the index so neighbour references stay 1:1.
    _, _, index = hat_id.partition(":")
    return f"turtle:{index}"


def build_turtle_patch(patch_depth: int) -> AperiodicPatch:
    """Build an :class:`AperiodicPatch` for the Turtle monotile.

    The Turtle is realised as the Tile(sqrt(3), 1) deformation of the verified
    Hat tiling, so it shares the Hat's adjacency, orientation and chirality
    structure at every depth.
    """
    hat_patch = build_hat_patch(patch_depth)
    to_turtle = edge_scaled_vertex_map(hat_patch, _edge_scale, key_precision=_VERTEX_KEY_PRECISION)

    cells: list[AperiodicPatchCell] = []
    for cell in hat_patch.cells:
        deformed = [to_turtle(vertex) for vertex in cell.vertices]
        vertices = tuple(
            (round(point[0], _OUTPUT_PRECISION), round(point[1], _OUTPUT_PRECISION))
            for point in deformed
        )
        centroid = polygon_centroid(tuple(_Vec(x, y) for x, y in vertices))
        cells.append(
            AperiodicPatchCell(
                id=_retag_id(cell.id),
                kind=TURTLE_KIND,
                center=(round(centroid.x, 6), round(centroid.y, 6)),
                vertices=vertices,
                neighbors=tuple(_retag_id(neighbor) for neighbor in cell.neighbors),
                tile_family=TURTLE_TILE_FAMILY,
                orientation_token=cell.orientation_token,
                chirality_token=cell.chirality_token,
                decoration_tokens=cell.decoration_tokens,
            )
        )
    return patch_from_cells(hat_patch.patch_depth, cells)
