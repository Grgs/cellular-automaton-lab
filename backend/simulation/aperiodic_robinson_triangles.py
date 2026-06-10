"""Robinson Triangles family.

Built directly from the canonical Robinson half-tile substitution
(``aperiodic_penrose_canonical``). The 5-kite sun seed contributes 10 acute
halves; substitution preserves the canonical [[2,1],[1,1]] half-tile growth, so
depth-d cell counts follow the Bielefeld Robinson-triangle reference exactly:
10, 30, 80, 210, 550, ... at depths 0..4.
"""

from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    ROBINSON_THICK_KIND,
    ROBINSON_THIN_KIND,
    ROBINSON_TILE_FAMILY,
)
from backend.simulation.aperiodic_golden_triangles import triangle_record
from backend.simulation.aperiodic_penrose_canonical import (
    ACUTE_HALF,
    PHI,
    acute_polygon,
    build_p2_sun_seed,
    obtuse_polygon,
    substitute_all,
)
from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    PatchRecord,
    Vec,
    encode_float,
    patch_from_records,
    polygon_centroid,
)


def _robinson_cell_id(kind: str, vertices: tuple[tuple[float, float], ...]) -> str:
    """Deterministic id from cell kind + centroid coordinates."""
    centroid = polygon_centroid(tuple(Vec(v[0], v[1]) for v in vertices))
    prefix = "rt" if kind == ROBINSON_THICK_KIND else "rn"
    return f"{prefix}:{encode_float(centroid.x)}:{encode_float(centroid.y)}"


def build_robinson_triangles_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    seed = build_p2_sun_seed(PHI**resolved_depth)
    halves = substitute_all(seed, resolved_depth)

    records: list[PatchRecord] = []
    for half in halves:
        if half.kind == ACUTE_HALF:
            kind = ROBINSON_THICK_KIND
            vertices = acute_polygon(half)
        else:
            kind = ROBINSON_THIN_KIND
            vertices = obtuse_polygon(half)
        cell_id = _robinson_cell_id(kind, vertices)
        records.append(
            triangle_record(
                cell_id=cell_id,
                kind=kind,
                vertices=vertices,
                tile_family=ROBINSON_TILE_FAMILY,
            )
        )
    return patch_from_records(resolved_depth, records, neighbor_mode="segment_overlap")
