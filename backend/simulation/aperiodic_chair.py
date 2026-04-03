from __future__ import annotations

from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    PatchRecord,
    Vec,
    id_from_anchor,
    patch_from_records,
    polygon_centroid,
    rounded_point,
)


_CHAIR_KIND = "chair"
_CHAIR_POLYGONS: dict[int, tuple[Vec, ...]] = {
    0: (
        Vec(0.0, 0.0),
        Vec(0.0, 1.0),
        Vec(0.0, 2.0),
        Vec(1.0, 2.0),
        Vec(1.0, 1.0),
        Vec(2.0, 1.0),
        Vec(2.0, 0.0),
        Vec(1.0, 0.0),
    ),
    1: (
        Vec(0.0, 0.0),
        Vec(0.0, 1.0),
        Vec(1.0, 1.0),
        Vec(1.0, 2.0),
        Vec(2.0, 2.0),
        Vec(2.0, 1.0),
        Vec(2.0, 0.0),
        Vec(1.0, 0.0),
    ),
    2: (
        Vec(2.0, 0.0),
        Vec(1.0, 0.0),
        Vec(1.0, 1.0),
        Vec(0.0, 1.0),
        Vec(0.0, 2.0),
        Vec(1.0, 2.0),
        Vec(2.0, 2.0),
        Vec(2.0, 1.0),
    ),
    3: (
        Vec(1.0, 0.0),
        Vec(0.0, 0.0),
        Vec(0.0, 1.0),
        Vec(0.0, 2.0),
        Vec(1.0, 2.0),
        Vec(2.0, 2.0),
        Vec(2.0, 1.0),
        Vec(1.0, 1.0),
    ),
}
_CHAIR_SUBSTITUTION_RULES: dict[int, tuple[tuple[int, int, int], ...]] = {
    0: ((0, 0, 0), (0, 1, 1), (1, 2, 0), (3, 0, 2)),
    1: ((0, 0, 0), (1, 1, 1), (1, 2, 0), (2, 2, 2)),
    2: ((1, 2, 0), (2, 1, 1), (2, 2, 2), (3, 0, 2)),
    3: ((0, 0, 0), (2, 2, 2), (3, 0, 2), (3, 1, 1)),
}


def _chair_record(orientation: int, anchor_x: int, anchor_y: int) -> PatchRecord:
    polygon = tuple(
        Vec(vertex.x + anchor_x, vertex.y + anchor_y)
        for vertex in _CHAIR_POLYGONS[orientation]
    )
    return {
        "id": id_from_anchor(_CHAIR_KIND, Vec(anchor_x, anchor_y), orientation),
        "kind": _CHAIR_KIND,
        "center": rounded_point(polygon_centroid(polygon)),
        "vertices": tuple(rounded_point(vertex) for vertex in polygon),
    }


def _collect_chair_records(
    remaining_depth: int,
    orientation: int,
    anchor_x: int,
    anchor_y: int,
    records: list[PatchRecord],
) -> None:
    if remaining_depth <= 0:
        records.append(_chair_record(orientation, anchor_x, anchor_y))
        return

    child_scale = 2 ** (remaining_depth - 1)
    for child_orientation, offset_x, offset_y in _CHAIR_SUBSTITUTION_RULES[orientation]:
        _collect_chair_records(
            remaining_depth - 1,
            child_orientation,
            anchor_x + (offset_x * child_scale),
            anchor_y + (offset_y * child_scale),
            records,
        )


def build_chair_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = int(patch_depth)
    records: list[PatchRecord] = []
    _collect_chair_records(resolved_depth, 0, 0, 0, records)
    return patch_from_records(resolved_depth, records)
