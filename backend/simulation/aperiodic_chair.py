from __future__ import annotations

from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    PatchRecord,
    Vec,
    encode_float,
    patch_from_records,
    polygon_centroid,
    rounded_point,
)


_CHAIR_KIND = "chair"
_UNIT_CHAIR_POLYGONS: dict[int, tuple[Vec, ...]] = {
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

_CHAIR_SUBSTITUTION_RULES: dict[int, tuple[tuple[int, float, float], ...]] = {
    0: (
        (0, 0.0, 0.0),
        (0, 1.0, 1.0),
        (1, 2.0, 0.0),
        (3, 0.0, 2.0),
    ),
    1: (
        (0, 0.0, 0.0),
        (1, 1.0, 1.0),
        (1, 2.0, 0.0),
        (2, 2.0, 2.0),
    ),
    2: (
        (1, 2.0, 0.0),
        (2, 1.0, 1.0),
        (2, 2.0, 2.0),
        (3, 0.0, 2.0),
    ),
    3: (
        (0, 0.0, 0.0),
        (2, 2.0, 2.0),
        (3, 0.0, 2.0),
        (3, 1.0, 1.0),
    ),
}


def _chair_id(path: str, orientation: int, scale_factor: float, anchor_x: float, anchor_y: float) -> str:
    return (
        f"chair:{path}:o{orientation}:s{encode_float(scale_factor)}:"
        f"{encode_float(anchor_x)}:{encode_float(anchor_y)}"
    )


def _scaled_polygon(
    orientation: int,
    scale_factor: float,
    anchor_x: float,
    anchor_y: float,
) -> tuple[Vec, ...]:
    return tuple(
        Vec(
            anchor_x + (scale_factor * vertex.x),
            anchor_y + (scale_factor * vertex.y),
        )
        for vertex in _UNIT_CHAIR_POLYGONS[orientation]
    )


def _chair_record(
    path: str,
    orientation: int,
    scale_factor: float,
    anchor_x: float,
    anchor_y: float,
) -> PatchRecord:
    polygon = _scaled_polygon(orientation, scale_factor, anchor_x, anchor_y)
    return {
        "id": _chair_id(path, orientation, scale_factor, anchor_x, anchor_y),
        "kind": _CHAIR_KIND,
        "center": rounded_point(polygon_centroid(polygon)),
        "vertices": tuple(rounded_point(vertex) for vertex in polygon),
        "orientation_token": str(orientation),
    }


def _collect_chair_records(
    remaining_depth: int,
    orientation: int,
    parent_scale: float,
    anchor_x: float,
    anchor_y: float,
    path: str,
    records: list[PatchRecord],
) -> None:
    if remaining_depth <= 0:
        records.append(_chair_record(path, orientation, parent_scale, anchor_x, anchor_y))
        return

    child_scale = parent_scale / 2.0
    for index, (child_orientation, grid_x, grid_y) in enumerate(
        _CHAIR_SUBSTITUTION_RULES[orientation]
    ):
        _collect_chair_records(
            remaining_depth - 1,
            child_orientation,
            child_scale,
            anchor_x + (grid_x * child_scale),
            anchor_y + (grid_y * child_scale),
            f"{path}.child{index}",
            records,
        )


def build_chair_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    records: list[PatchRecord] = []
    _collect_chair_records(
        resolved_depth,
        0,
        1.0,
        0.0,
        0.0,
        "root",
        records,
    )
    return patch_from_records(
        resolved_depth,
        records,
        neighbor_mode="segment_overlap",
    )
