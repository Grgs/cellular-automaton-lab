"""Penrose P1 (pentagon / diamond) tiling.

Built on top of the de Bruijn pentagrid construction in
``backend/simulation/penrose.py`` -- the same source that drives P3
(``penrose-p3-rhombs``). The topology mirrors P3 (one cell per pentagrid rhomb,
same neighbour graph) but the rendered cell geometry is rewritten so the patch
visually presents Penrose's published P1 prototile shapes:

* thin rhomb (36-144-36-144) -> ``p1-diamond`` (the rhomb polygon is preserved
  verbatim because the thin Penrose rhomb is geometrically the exact P1
  diamond from Penrose's 1974 paper).
* thick rhomb (72-108-72-108) -> ``p1-pentagon`` (the rhomb polygon is
  replaced by a regular pentagon inscribed in the rhomb -- one vertex of the
  pentagon points along the rhomb's long diagonal toward one of the rhomb's
  72-degree corners. The pentagon is centred at the rhomb centroid and
  diameter is sized to the rhomb's short diagonal so the pentagon fits inside
  the rhomb).

The inscribed pentagons leave thin lens-shaped gaps along each thick-rhomb
boundary; rendered alongside the thin-rhomb diamonds, the result reads as a
classic Penrose pentagonal pattern with diamonds bridging the pentagons.

Cell ids, neighbour edges, and the depth-to-cell-count sequence are inherited
unchanged from the pentagrid (5/10/24/66 at depths 0..3). The trade-off is
documented in ``docs/TILING_KNOWN_DEVIATIONS.md``: this is a rendered-shape
relabelling of the canonical pentagrid output rather than a true 4-prototile
P1 substitution; in particular, the published P1 stars and boats are not
materialised as their own cell kinds.
"""

from __future__ import annotations

import math

from backend.simulation.aperiodic_family_manifest import (
    P1_DIAMOND_KIND,
    P1_PENTAGON_KIND,
    PENROSE_P1_TILE_FAMILY,
)
from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    AperiodicPatchCell,
    Vec,
    polygon_centroid,
    rounded_point,
)
from backend.simulation.penrose import (
    PENROSE_EDGE_ADJACENCY,
    THICK_RHOMB_KIND,
    THIN_RHOMB_KIND,
    build_penrose_patch,
)


_P1_KIND_BY_RHOMB_KIND = {
    THICK_RHOMB_KIND: P1_PENTAGON_KIND,
    THIN_RHOMB_KIND: P1_DIAMOND_KIND,
}

# Inscribed-pentagon size, expressed as a fraction of the maximum
# circumradius that keeps every pentagon vertex strictly inside the rhomb.
# The maximum circumradius equals ``rhomb_side / 2`` (verified geometrically
# by intersecting a regular pentagon centred on the rhomb's diagonals with
# the rhomb's four edges); a value below 1.0 adds visible breathing room
# along each rhomb edge so the inscribed pentagons read as distinct cells.
_PENTAGON_INSCRIBED_FRACTION = 0.94

_PENTAGON_VERTEX_ANGLE_STEP_RADIANS = math.radians(72.0)


def _p1_cell_id(rhomb_cell_id: str) -> str:
    if rhomb_cell_id.startswith("rt:"):
        return "pp:" + rhomb_cell_id[3:]
    if rhomb_cell_id.startswith("rn:"):
        return "pd:" + rhomb_cell_id[3:]
    return f"p1:{rhomb_cell_id}"


def _identify_long_diagonal_apex(
    vertices: tuple[tuple[float, float], ...],
    centroid: tuple[float, float],
) -> tuple[float, float]:
    """Return the rhomb vertex farthest from the centroid (one of the 72-degree
    corners on the long diagonal)."""
    best_vertex = vertices[0]
    best_distance_squared = -1.0
    for vertex in vertices:
        dx = vertex[0] - centroid[0]
        dy = vertex[1] - centroid[1]
        distance_squared = dx * dx + dy * dy
        if distance_squared > best_distance_squared:
            best_distance_squared = distance_squared
            best_vertex = vertex
    return best_vertex


def _inscribed_pentagon(
    thick_rhomb_vertices: tuple[tuple[float, float], ...],
) -> tuple[tuple[float, float], ...]:
    """Return the regular pentagon inscribed in a thick Penrose rhomb.

    The pentagon is centred at the rhomb's centroid, one vertex points along
    the long diagonal toward one of the rhomb's 72-degree corners, and the
    pentagon is sized so its short axis (perpendicular to the orientation
    vertex) fits inside the rhomb's short diagonal -- see
    ``_PENTAGON_INSCRIBED_FRACTION``. The pentagon is emitted in
    counter-clockwise order so downstream consumers can rely on the same
    winding as the source rhomb polygon.
    """
    if len(thick_rhomb_vertices) != 4:
        raise ValueError("Thick rhomb polygon must have exactly four vertices.")
    centroid_vec = polygon_centroid(tuple(Vec(x, y) for x, y in thick_rhomb_vertices))
    centroid_xy = (centroid_vec.x, centroid_vec.y)
    apex = _identify_long_diagonal_apex(thick_rhomb_vertices, centroid_xy)
    direction_x = apex[0] - centroid_xy[0]
    direction_y = apex[1] - centroid_xy[1]
    base_angle = math.atan2(direction_y, direction_x)

    # Compute the rhomb's side length (any of the four rhomb edges -- the
    # sides are all equal). The maximum pentagon circumradius that keeps
    # every pentagon vertex strictly inside the rhomb is ``side_length / 2``:
    # at that radius the four non-leading pentagon vertices touch the four
    # rhomb edges exactly. Multiplying by ``_PENTAGON_INSCRIBED_FRACTION``
    # leaves a margin so the pentagon edges don't graze the rhomb edges.
    first_vertex = thick_rhomb_vertices[0]
    second_vertex = thick_rhomb_vertices[1]
    side_length = math.hypot(
        second_vertex[0] - first_vertex[0],
        second_vertex[1] - first_vertex[1],
    )
    if side_length <= 0.0:
        # Degenerate thick rhomb -- fall back to the original polygon.
        return thick_rhomb_vertices
    circumradius = _PENTAGON_INSCRIBED_FRACTION * 0.5 * side_length

    pentagon_vertices: list[tuple[float, float]] = []
    for index in range(5):
        angle = base_angle + index * _PENTAGON_VERTEX_ANGLE_STEP_RADIANS
        pentagon_vertices.append(
            (
                centroid_xy[0] + circumradius * math.cos(angle),
                centroid_xy[1] + circumradius * math.sin(angle),
            )
        )
    return tuple(rounded_point(vertex) for vertex in pentagon_vertices)


def build_penrose_p1_patch(patch_depth: int) -> AperiodicPatch:
    rhomb_patch = build_penrose_patch(
        patch_depth,
        adjacency_mode=PENROSE_EDGE_ADJACENCY,
    )
    id_remap = {cell.id: _p1_cell_id(cell.id) for cell in rhomb_patch.cells}
    cells_list: list[AperiodicPatchCell] = []
    for cell in rhomb_patch.cells:
        kind = _P1_KIND_BY_RHOMB_KIND[cell.kind]
        if kind == P1_PENTAGON_KIND:
            vertices: tuple[tuple[float, float], ...] = _inscribed_pentagon(cell.vertices)
        else:
            vertices = cell.vertices
        cells_list.append(
            AperiodicPatchCell(
                id=id_remap[cell.id],
                kind=kind,
                center=cell.center,
                vertices=vertices,
                neighbors=tuple(sorted(id_remap[neighbor] for neighbor in cell.neighbors)),
                tile_family=PENROSE_P1_TILE_FAMILY,
            )
        )
    cells = tuple(cells_list)
    return AperiodicPatch(
        patch_depth=rhomb_patch.patch_depth,
        width=rhomb_patch.width,
        height=rhomb_patch.height,
        cells=cells,
    )
