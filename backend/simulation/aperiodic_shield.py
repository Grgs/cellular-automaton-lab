from __future__ import annotations

import math

from shapely.geometry import Polygon

from backend.simulation.aperiodic_support import (
    AFFINE_IDENTITY,
    Affine,
    AperiodicPatch,
    AperiodicPatchCell,
    PatchRecord,
    Vec,
    affine_apply,
    affine_multiply,
    id_from_transform,
    patch_from_cells,
    polygon_centroid,
    rotation,
    rounded_point,
    scale as affine_scale,
    translation,
)


_BASE_SHIELD = (
    Vec(-0.5, -1.0),
    Vec(0.0, -1.5),
    Vec(0.5, -1.0),
    Vec(0.5, 1.0),
    Vec(0.0, 1.5),
    Vec(-0.5, 1.0),
)
_BASE_SQUARES: tuple[tuple[str, tuple[Vec, ...]], ...] = (
    (
        "left",
        (
            Vec(-1.5, -0.5),
            Vec(-0.5, -0.5),
            Vec(-0.5, 0.5),
            Vec(-1.5, 0.5),
        ),
    ),
    (
        "right",
        (
            Vec(0.5, -0.5),
            Vec(1.5, -0.5),
            Vec(1.5, 0.5),
            Vec(0.5, 0.5),
        ),
    ),
)
_BASE_TRIANGLES: tuple[tuple[str, str, tuple[Vec, ...]], ...] = (
    (
        "top-left",
        "left",
        (
            Vec(-0.5, -1.0),
            Vec(0.0, -1.5),
            Vec(-1.0, -1.5),
        ),
    ),
    (
        "top-right",
        "right",
        (
            Vec(0.0, -1.5),
            Vec(0.5, -1.0),
            Vec(1.0, -1.5),
        ),
    ),
    (
        "bottom-left",
        "left",
        (
            Vec(-1.0, 1.5),
            Vec(0.0, 1.5),
            Vec(-0.5, 1.0),
        ),
    ),
    (
        "bottom-right",
        "right",
        (
            Vec(0.0, 1.5),
            Vec(1.0, 1.5),
            Vec(0.5, 1.0),
        ),
    ),
)
_CHILD_CLUSTERS: tuple[tuple[str, Vec, float], ...] = (
    ("north-west", Vec(-3.0, -3.0), -math.pi / 6),
    ("north-east", Vec(3.0, -3.0), math.pi / 6),
    ("south-west", Vec(-3.0, 3.0), math.pi / 6),
    ("south-east", Vec(3.0, 3.0), -math.pi / 6),
)
_CHILD_SCALE = 0.45


def _orientation_token(transform: Affine) -> str:
    angle = math.degrees(math.atan2(transform[3], transform[0]))
    return str(int(round(angle)) % 360)


def _apply_polygon(transform: Affine, vertices: tuple[Vec, ...]) -> tuple[Vec, ...]:
    return tuple(affine_apply(transform, vertex) for vertex in vertices)


def _record(
    prefix: str,
    kind: str,
    transform: Affine,
    vertices: tuple[Vec, ...],
    *,
    chirality_token: str | None = None,
    decoration_tokens: tuple[str, ...] | None = None,
) -> PatchRecord:
    resolved_vertices = _apply_polygon(transform, vertices)
    return {
        "id": id_from_transform(prefix, transform),
        "kind": kind,
        "center": rounded_point(polygon_centroid(resolved_vertices)),
        "vertices": tuple((vertex.x, vertex.y) for vertex in resolved_vertices),
        "tile_family": "shield",
        "orientation_token": _orientation_token(transform),
        "chirality_token": chirality_token,
        "decoration_tokens": decoration_tokens,
    }


def _cluster_transform(parent: Affine, offset: Vec, angle: float) -> Affine:
    local = affine_multiply(
        translation(offset.x, offset.y),
        affine_multiply(rotation(angle), affine_scale(_CHILD_SCALE)),
    )
    return affine_multiply(parent, local)


def _collect_cluster_records(
    remaining_depth: int,
    transform: Affine,
    path: str,
    phase: int,
    records: list[PatchRecord],
) -> None:
    phase_label = phase % 4
    records.append(
        _record(
            f"shield:{path}:shield:phase-{phase_label}",
            "shield-shield",
            transform,
            _BASE_SHIELD,
            decoration_tokens=(f"arrow-{phase_label}", f"ring-{phase_label % 2}"),
        )
    )
    for square_role, polygon in _BASE_SQUARES:
        records.append(
            _record(
                f"shield:{path}:square:{square_role}",
                "shield-square",
                transform,
                polygon,
            )
        )
    for role, chirality_token, polygon in _BASE_TRIANGLES:
        records.append(
            _record(
                f"shield:{path}:triangle:{role}:phase-{phase_label}",
                "shield-triangle",
                transform,
                polygon,
                chirality_token=chirality_token,
                decoration_tokens=(f"arm-{role}", f"phase-{phase_label % 2}"),
            )
        )

    if remaining_depth <= 0:
        return

    for index, (label, offset, angle_delta) in enumerate(_CHILD_CLUSTERS):
        _collect_cluster_records(
            remaining_depth - 1,
            _cluster_transform(transform, offset, angle_delta),
            f"{path}.{label}",
            phase + index + 1,
            records,
        )


def build_shield_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    records: list[PatchRecord] = []
    _collect_cluster_records(resolved_depth, AFFINE_IDENTITY, "root", 0, records)

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
            tile_family=record.get("tile_family"),
            orientation_token=record.get("orientation_token"),
            chirality_token=record.get("chirality_token"),
            decoration_tokens=record.get("decoration_tokens"),
        )
        for record in sorted(records, key=lambda item: item["id"])
    )
    return patch_from_cells(resolved_depth, cells)
