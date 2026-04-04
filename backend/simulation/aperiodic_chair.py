from __future__ import annotations

from shapely.geometry import Polygon

from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    AperiodicPatchCell,
    PatchRecord,
    Vec,
    encode_float,
    patch_from_cells,
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

# A scale-4 chair can be tiled by one scale-2 chair plus these 12 unit chairs.
_SMALL_CHAIR_PLACEMENTS: tuple[tuple[int, float, float], ...] = (
    (0, 0.0, 4.0),
    (3, 0.0, 6.0),
    (3, 1.0, 5.0),
    (0, 2.0, 2.0),
    (3, 2.0, 4.0),
    (2, 2.0, 6.0),
    (0, 3.0, 3.0),
    (0, 4.0, 0.0),
    (1, 4.0, 2.0),
    (1, 5.0, 1.0),
    (1, 6.0, 0.0),
    (2, 6.0, 2.0),
)


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
    }


def _collect_chair_records(
    remaining_depth: int,
    parent_scale: float,
    anchor_x: float,
    anchor_y: float,
    path: str,
    records: list[PatchRecord],
) -> None:
    if remaining_depth <= 0:
        records.append(_chair_record(path, 0, parent_scale, anchor_x, anchor_y))
        return

    leaf_scale = parent_scale / 4.0
    for index, (orientation, local_x, local_y) in enumerate(_SMALL_CHAIR_PLACEMENTS):
        records.append(
            _chair_record(
                f"{path}.leaf{index}",
                orientation,
                leaf_scale,
                anchor_x + (leaf_scale * local_x),
                anchor_y + (leaf_scale * local_y),
            )
        )

    _collect_chair_records(
        remaining_depth - 1,
        parent_scale / 2.0,
        anchor_x,
        anchor_y,
        f"{path}.macro",
        records,
    )


def build_chair_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    records: list[PatchRecord] = []
    if resolved_depth == 0:
        records.append(_chair_record("root", 0, 1.0, 0.0, 0.0))
    else:
        _collect_chair_records(
            resolved_depth,
            float(2 ** (resolved_depth + 1)),
            0.0,
            0.0,
            "root",
            records,
        )

    polygons = {
        record["id"]: Polygon(record["vertices"])
        for record in records
    }
    neighbors: dict[str, set[str]] = {record["id"]: set() for record in records}
    for left_index, left in enumerate(records):
        left_polygon = polygons[left["id"]]
        for right in records[left_index + 1 :]:
            right_polygon = polygons[right["id"]]
            if left_polygon.boundary.intersection(right_polygon.boundary).length <= 1e-9:
                continue
            neighbors[left["id"]].add(right["id"])
            neighbors[right["id"]].add(left["id"])

    cells = tuple(
        AperiodicPatchCell(
            id=record["id"],
            kind=record["kind"],
            center=record["center"],
            vertices=record["vertices"],
            neighbors=tuple(sorted(neighbors[record["id"]])),
        )
        for record in sorted(records, key=lambda item: item["id"])
    )
    return patch_from_cells(resolved_depth, cells)
