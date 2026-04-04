from __future__ import annotations

import math

from backend.simulation.aperiodic_support import (
    AFFINE_IDENTITY,
    Affine,
    AperiodicPatch,
    PatchRecord,
    Vec,
    affine_apply,
    affine_multiply,
    id_from_transform,
    patch_from_records,
    polygon_centroid,
    rotation,
    rounded_point,
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
            Vec(-2.5, -1.0),
            Vec(-0.5, -1.0),
            Vec(-0.5, 1.0),
            Vec(-2.5, 1.0),
        ),
    ),
    (
        "right",
        (
            Vec(0.5, -1.0),
            Vec(2.5, -1.0),
            Vec(2.5, 1.0),
            Vec(0.5, 1.0),
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
_CLUSTER_VECTOR_X = Vec(5.0, 0.0)
_CLUSTER_VECTOR_Y = Vec(1.5, 2.5)


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


def _emit_cluster_records(
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


def _cluster_transform(x: int, y: int) -> Affine:
    return affine_multiply(
        translation(
            (x * _CLUSTER_VECTOR_X.x) + (y * _CLUSTER_VECTOR_Y.x),
            (x * _CLUSTER_VECTOR_X.y) + (y * _CLUSTER_VECTOR_Y.y),
        ),
        AFFINE_IDENTITY,
    )


def _cluster_coordinates(patch_depth: int) -> tuple[tuple[int, int], ...]:
    radius = max(0, int(patch_depth))
    return tuple(
        (x, y)
        for y in range(-radius, radius + 1)
        for x in range(-radius, radius + 1)
        if abs(x) + abs(y) <= radius
    )


def _cluster_phase(x: int, y: int) -> int:
    return (x - y) % 4


def build_shield_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    records: list[PatchRecord] = []
    for x, y in _cluster_coordinates(resolved_depth):
        _emit_cluster_records(
            _cluster_transform(x, y),
            f"cluster:{x}:{y}",
            _cluster_phase(x, y),
            records,
        )

    return patch_from_records(resolved_depth, records, edge_precision=6)
