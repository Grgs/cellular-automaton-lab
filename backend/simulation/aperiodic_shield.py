from __future__ import annotations

import math
from typing import Literal

from backend.simulation.aperiodic_family_manifest import (
    SHIELD_SHIELD_KIND,
    SHIELD_SQUARE_KIND,
    SHIELD_TILE_FAMILY,
    SHIELD_TRIANGLE_KIND,
)
from backend.simulation.aperiodic_support import (
    Affine,
    AperiodicPatch,
    PatchRecord,
    Vec,
    affine_multiply,
    patch_from_records,
    polygon_centroid,
    rotation,
    scale,
    translation,
)


# Franz Gahler published an exact recursive shield tiling renderer as a
# hand-coded PostScript program. This module translates that marked symbolic
# substitution into the app's public square / triangle / shield topology model.
#
# Source:
# https://www.math.uni-bielefeld.de/~gaehler/tilings/sh.ps

ShieldTileLabel = Literal[
    "left-black-triangle",
    "right-black-triangle",
    "left-white-triangle",
    "right-white-triangle",
    "left-square",
    "right-square",
    "left-shield",
    "right-shield",
]

_SQRT3 = math.sqrt(3.0)
_RT2H = math.sqrt(2.0) / 2.0
_THETA = math.sqrt(2.0 + _SQRT3)
_TR3A = _THETA / 2.0
_TR3B = math.sqrt(2.0 - _SQRT3) / 2.0
_DEFAULT_COMPATIBILITY_SCALE = 1.0
_DEFAULT_COMPATIBILITY_WINDOW = 1.0

_TRIANGLE_VERTICES: tuple[Vec, ...] = (
    Vec(0.0, 0.0),
    Vec(1.0, 0.0),
    Vec(0.5, _SQRT3 / 2.0),
)
_SQUARE_VERTICES: tuple[Vec, ...] = (
    Vec(0.0, 0.0),
    Vec(1.0, 0.0),
    Vec(1.0, 1.0),
    Vec(0.0, 1.0),
)
_SHIELD_VERTICES: tuple[Vec, ...] = (
    Vec(0.0, 0.0),
    Vec(1.0, 0.0),
    Vec(1.0 + math.cos(math.radians(30.0)), math.sin(math.radians(30.0))),
    Vec(
        1.0 + math.cos(math.radians(30.0)) + math.cos(math.radians(120.0)),
        math.sin(math.radians(30.0)) + math.sin(math.radians(120.0)),
    ),
    Vec(0.5, 1.0 + (_SQRT3 / 2.0)),
    Vec(0.0, 1.0),
)

_PUBLIC_KIND_BY_LABEL: dict[ShieldTileLabel, str] = {
    "left-black-triangle": SHIELD_TRIANGLE_KIND,
    "right-black-triangle": SHIELD_TRIANGLE_KIND,
    "left-white-triangle": SHIELD_TRIANGLE_KIND,
    "right-white-triangle": SHIELD_TRIANGLE_KIND,
    "left-square": SHIELD_SQUARE_KIND,
    "right-square": SHIELD_SQUARE_KIND,
    "left-shield": SHIELD_SHIELD_KIND,
    "right-shield": SHIELD_SHIELD_KIND,
}
_VERTICES_BY_LABEL: dict[ShieldTileLabel, tuple[Vec, ...]] = {
    "left-black-triangle": _TRIANGLE_VERTICES,
    "right-black-triangle": _TRIANGLE_VERTICES,
    "left-white-triangle": _TRIANGLE_VERTICES,
    "right-white-triangle": _TRIANGLE_VERTICES,
    "left-square": _SQUARE_VERTICES,
    "right-square": _SQUARE_VERTICES,
    "left-shield": _SHIELD_VERTICES,
    "right-shield": _SHIELD_VERTICES,
}


def _tile_chirality(label: ShieldTileLabel) -> str:
    return "left" if label.startswith("left-") else "right"


def _tile_decoration_tokens(label: ShieldTileLabel) -> tuple[str, ...]:
    if "black-triangle" in label:
        return ("triangle:black", _tile_chirality(label))
    if "white-triangle" in label:
        return ("triangle:white", _tile_chirality(label))
    return (_tile_chirality(label),)


def _dod2orth_translation(
    u: float,
    v: float,
    w: float,
    x: float,
    y: float,
    z: float,
) -> tuple[float, float]:
    return (
        ((u - z) * _TR3A) + ((v - y) * _RT2H) + ((w - x) * _TR3B),
        ((u + z) * _TR3B) + ((v + y) * _RT2H) + ((w + x) * _TR3A),
    )


def _child_transform(
    placement: tuple[float, float, float, float, float, float],
    *,
    rotation_degrees: float,
) -> Affine:
    tx, ty = _dod2orth_translation(*placement)
    return affine_multiply(
        translation(tx / _THETA, ty / _THETA),
        affine_multiply(rotation(math.radians(rotation_degrees)), scale(1.0 / _THETA)),
    )


def _rotation_degrees(transform: Affine) -> int:
    return int(round(math.degrees(math.atan2(transform[3], transform[0])))) % 360


def _centered_records(records: list[PatchRecord]) -> list[PatchRecord]:
    if not records:
        return records
    all_x = [vertex[0] for record in records for vertex in record["vertices"]]
    all_y = [vertex[1] for record in records for vertex in record["vertices"]]
    offset_x = (max(all_x) + min(all_x)) / 2.0
    offset_y = (max(all_y) + min(all_y)) / 2.0
    centered: list[PatchRecord] = []
    for record in records:
        vertices = tuple(
            (
                round(vertex_x - offset_x, 6),
                round(vertex_y - offset_y, 6),
            )
            for vertex_x, vertex_y in record["vertices"]
        )
        centroid = polygon_centroid(tuple(Vec(vertex_x, vertex_y) for vertex_x, vertex_y in vertices))
        centered.append(
            {
                **record,
                "center": (round(centroid.x, 6), round(centroid.y, 6)),
                "vertices": vertices,
            }
        )
    return centered


def _leaf_record(
    label: ShieldTileLabel,
    *,
    path: str,
    transform: Affine,
) -> PatchRecord:
    vertices = tuple(
        (
            round(
                (transform[0] * vertex.x) + (transform[1] * vertex.y) + transform[2],
                6,
            ),
            round(
                (transform[3] * vertex.x) + (transform[4] * vertex.y) + transform[5],
                6,
            ),
        )
        for vertex in _VERTICES_BY_LABEL[label]
    )
    centroid = polygon_centroid(tuple(Vec(vertex_x, vertex_y) for vertex_x, vertex_y in vertices))
    return {
        "id": f"shield:{path}",
        "kind": _PUBLIC_KIND_BY_LABEL[label],
        "center": (round(centroid.x, 6), round(centroid.y, 6)),
        "vertices": vertices,
        "tile_family": SHIELD_TILE_FAMILY,
        "orientation_token": str(_rotation_degrees(transform)),
        "chirality_token": _tile_chirality(label),
        "decoration_tokens": _tile_decoration_tokens(label),
    }


_SUBSTITUTION_RULES: dict[
    ShieldTileLabel,
    tuple[tuple[ShieldTileLabel, tuple[float, float, float, float, float, float], float], ...],
] = {
    "right-black-triangle": (
        ("right-shield", (0, 1, 1, 0, 0, 0), 225),
    ),
    "left-black-triangle": (
        ("left-shield", (0, 1, 1, 0, 0, 0), 225),
    ),
    "right-white-triangle": (
        ("left-white-triangle", (0, 0, 1, 0, 0, 0), -105),
        ("right-white-triangle", (1, 0, 0, 0, 0, -1), 105),
        ("left-square", (1, 0, 0, 1, 0, -1), 135),
    ),
    "left-white-triangle": (
        ("left-white-triangle", (0, 0, 1, 0, 0, 0), -105),
        ("right-white-triangle", (1, 0, 0, 0, 0, -1), 105),
        ("right-square", (0, 1, 1, 0, 0, 0), -135),
    ),
    "right-square": (
        ("left-black-triangle", (0, 0, 1, 0, 0, 0), -105),
        ("right-black-triangle", (1, 0, 0, 0, 0, -1), 105),
        ("left-square", (1, 0, 0, 1, 0, -1), 135),
        ("left-black-triangle", (0, 1, 1, 0, 0, 0), 165),
        ("right-black-triangle", (1, 1, 1, 0, 0, 0), 195),
    ),
    "left-square": (
        ("left-black-triangle", (0, 0, 1, 0, 0, 0), -105),
        ("right-black-triangle", (1, 0, 0, 0, 0, -1), 105),
        ("right-square", (0, 1, 1, 0, 0, 0), -135),
        ("left-black-triangle", (0, 1, 1, 0, 0, 0), 165),
        ("right-black-triangle", (1, 1, 1, 0, 0, 0), 195),
    ),
    "left-shield": (
        ("left-black-triangle", (0, 0, 1, 0, 0, 0), -105),
        ("right-black-triangle", (1, 0, 0, 0, 0, -1), 105),
        ("left-square", (1, 0, 0, 1, 0, -1), 135),
        ("left-black-triangle", (0, 1, 1, 0, 0, 0), 165),
        ("right-black-triangle", (1, 1, 1, 0, 0, 0), 195),
        ("left-square", (0, 1, 1, 0, 0, 0), 15),
        ("right-white-triangle", (0, 1, 1, 0, 0, 1), -15),
        ("left-black-triangle", (1, 1, 1, 1, 0, 0), 135),
        ("left-white-triangle", (1, 1, 1, 0, 0, 0), 45),
        ("right-square", (1, 1, 1, 0, 0, 0), -105),
        ("right-black-triangle", (1, 2, 1, 0, 0, 0), -135),
        ("left-white-triangle", (1, 1, 0, 0, 0, 0), -75),
        ("right-black-triangle", (2, 1, 0, 0, 0, -1), 135),
    ),
    "right-shield": (
        ("right-black-triangle", (0, 0, 0, 0, 0, 0), 15),
        ("right-black-triangle", (1, 0, 0, 0, 0, -1), 105),
        ("right-square", (1, 0, 0, 1, 0, -1), 135),
        ("left-black-triangle", (0, 1, 1, 0, 0, 0), 165),
        ("left-black-triangle", (0, 1, 1, 0, -1, 0), 75),
        ("left-square", (0, 1, 1, 0, 0, 0), 15),
        ("right-white-triangle", (0, 1, 1, 0, 0, 1), -15),
        ("left-black-triangle", (1, 1, 1, 1, 0, 0), 135),
        ("left-black-triangle", (1, 1, 1, 0, 0, 0), 45),
        ("right-square", (1, 1, 1, 0, 0, 0), -105),
        ("right-white-triangle", (1, 2, 1, 0, 0, 0), -135),
        ("left-white-triangle", (1, 1, 0, 0, 0, 0), -75),
        ("right-black-triangle", (2, 1, 0, 0, 0, -1), 135),
    ),
}


def _collect_records(
    label: ShieldTileLabel,
    *,
    path: str,
    remaining_depth: int,
    transform: Affine,
    records: list[PatchRecord],
) -> None:
    if remaining_depth <= 0:
        records.append(_leaf_record(label, path=path, transform=transform))
        return
    for index, (child_label, placement, rotation_degrees) in enumerate(_SUBSTITUTION_RULES[label]):
        _collect_records(
            child_label,
            path=f"{path}.{index}",
            remaining_depth=remaining_depth - 1,
            transform=affine_multiply(
                transform,
                _child_transform(placement, rotation_degrees=rotation_degrees),
            ),
            records=records,
        )


def build_shield_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    records: list[PatchRecord] = []
    _collect_records(
        "right-shield",
        path="root",
        remaining_depth=resolved_depth,
        transform=scale(_THETA**resolved_depth),
        records=records,
    )
    return patch_from_records(
        resolved_depth,
        _centered_records(records),
        edge_precision=6,
    )


def default_shield_trace_geometry_cleanup_scale() -> float:
    return _DEFAULT_COMPATIBILITY_SCALE


def build_shield_patch_for_window_threshold(
    patch_depth: int,
    *,
    window_threshold: float,
    cleanup_scale: float | None = None,
) -> AperiodicPatch:
    del window_threshold, cleanup_scale
    return build_shield_patch(patch_depth)


def build_shield_patch_for_cleanup_scale(
    patch_depth: int,
    *,
    cleanup_scale: float,
) -> AperiodicPatch:
    del cleanup_scale
    return build_shield_patch(patch_depth)


def default_shield_window_threshold() -> float:
    return _DEFAULT_COMPATIBILITY_WINDOW

