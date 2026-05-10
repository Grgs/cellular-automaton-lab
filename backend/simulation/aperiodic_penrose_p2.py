"""Penrose P2 (kite-dart) tiling.

Built from the canonical Robinson half-tile substitution
(``aperiodic_penrose_canonical``) starting from the 5-kite sun seed. After
substitution we pair half-tiles into full Penrose tiles using the standard
convention:

* Two acute halves glued along a long edge form a kite.
* Two obtuse halves glued along a short edge form a dart.

Half-tiles whose pairing partner lies outside the patch (because the matching
edge sits on the patch perimeter) are emitted as half-tile cells under
``KITE_HALF_ACUTE_KIND`` / ``DART_HALF_OBTUSE_KIND``. This is the "Option 2"
boundary-half-tile treatment from
``docs/PENROSE_CANONICAL_SUBSTITUTION_PLAN.md`` and matches the canonical
Conway / de Bruijn deflation; the trade-off is that depth-d patches now have
visibly halved kites/darts at the sun perimeter.
"""

from __future__ import annotations

from backend.simulation.aperiodic_family_manifest import (
    DART_HALF_OBTUSE_KIND,
    DART_KIND,
    KITE_HALF_ACUTE_KIND,
    KITE_KIND,
)
from backend.simulation.aperiodic_penrose_canonical import (
    PHI,
    acute_polygon,
    build_p2_sun_seed,
    dart_polygon,
    kite_polygon,
    obtuse_polygon,
    pair_halves_into_kites_and_darts,
    substitute_all,
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


def _cell_id(prefix: str, vertices: tuple[tuple[float, float], ...]) -> str:
    centroid = polygon_centroid(tuple(Vec(v[0], v[1]) for v in vertices))
    return f"{prefix}:{encode_float(centroid.x)}:{encode_float(centroid.y)}"


def _record_for_full_tile(
    prefix: str,
    kind: str,
    vertices: tuple[tuple[float, float], ...],
) -> PatchRecord:
    rounded = tuple(rounded_point(v) for v in vertices)
    centroid = polygon_centroid(tuple(Vec(v[0], v[1]) for v in rounded))
    return {
        "id": _cell_id(prefix, rounded),
        "kind": kind,
        "center": rounded_point(centroid),
        "vertices": rounded,
    }


def build_penrose_p2_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    seed = build_p2_sun_seed(PHI**resolved_depth)
    halves = substitute_all(seed, resolved_depth)
    pairing = pair_halves_into_kites_and_darts(halves)

    records: list[PatchRecord] = []
    for left_index, right_index in pairing.kite_pairs:
        kite_vertices = kite_polygon(halves[left_index], halves[right_index])
        records.append(_record_for_full_tile("p2k", KITE_KIND, kite_vertices))
    for left_index, right_index in pairing.dart_pairs:
        dart_vertices = dart_polygon(halves[left_index], halves[right_index])
        records.append(_record_for_full_tile("p2d", DART_KIND, dart_vertices))
    for index in pairing.unpaired_acute:
        half_vertices = acute_polygon(halves[index])
        records.append(_record_for_full_tile("p2ka", KITE_HALF_ACUTE_KIND, half_vertices))
    for index in pairing.unpaired_obtuse:
        half_vertices = obtuse_polygon(halves[index])
        records.append(_record_for_full_tile("p2do", DART_HALF_OBTUSE_KIND, half_vertices))

    return patch_from_records(resolved_depth, records, neighbor_mode="segment_overlap")
