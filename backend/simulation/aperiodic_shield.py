from __future__ import annotations

from functools import lru_cache
import json
import math
from pathlib import Path
from typing import TypedDict

from backend.simulation.aperiodic_support import (
    AperiodicPatch,
    AperiodicPatchCell,
    patch_from_cells,
)


_DATA_PATH = Path(__file__).with_name("data") / "shield_reference_patch.json"
_ROTATION_STEP_DEGREES = 15
_ROTATION_STEP_RADIANS = math.radians(_ROTATION_STEP_DEGREES)
_POLYGON_SCALE = 1.62 / 1.11


class _ShieldReferenceRecord(TypedDict):
    id: str
    kind: str
    center: list[float]
    vertices: list[list[float]]
    tile_family: str | None
    orientation_token: str | None
    chirality_token: str | None
    decoration_tokens: list[str] | None
    graph_distance: int
    neighbors: list[str]


class _ShieldReferencePayload(TypedDict):
    source: str
    contact_threshold: int
    rotation_step_degrees: int
    graph_distance_thresholds: dict[str, int]
    records: list[_ShieldReferenceRecord]


@lru_cache(maxsize=1)
def _load_reference_payload() -> _ShieldReferencePayload:
    return json.loads(_DATA_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_reference_records() -> tuple[_ShieldReferenceRecord, ...]:
    return tuple(_load_reference_payload()["records"])


@lru_cache(maxsize=1)
def _distance_thresholds() -> dict[int, int]:
    payload = _load_reference_payload()
    return {
        int(depth): int(distance)
        for depth, distance in payload["graph_distance_thresholds"].items()
    }


@lru_cache(maxsize=1)
def _reference_pivot() -> tuple[float, float]:
    seed_records = [
        record
        for record in _load_reference_records()
        if int(record["graph_distance"]) == 0
    ]
    if not seed_records:
        raise ValueError("Shield reference patch is missing a graph-distance seed cell.")
    center = seed_records[0]["center"]
    return (float(center[0]), float(center[1]))


def _distance_threshold(patch_depth: int) -> int:
    resolved_depth = max(0, int(patch_depth))
    thresholds = _distance_thresholds()
    if resolved_depth in thresholds:
        return thresholds[resolved_depth]
    return thresholds[max(thresholds)]


def _rotate_point(
    point: tuple[float, float],
    *,
    pivot: tuple[float, float],
    radians: float,
) -> tuple[float, float]:
    translated_x = point[0] - pivot[0]
    translated_y = point[1] - pivot[1]
    cosine = math.cos(radians)
    sine = math.sin(radians)
    return (
        round((translated_x * cosine) - (translated_y * sine) + pivot[0], 6),
        round((translated_x * sine) + (translated_y * cosine) + pivot[1], 6),
    )


def _rotate_orientation_token(
    token: str | None,
    *,
    degrees: int,
) -> str | None:
    if token is None:
        return None
    try:
        return str((int(token) + degrees) % 360)
    except ValueError:
        return token


def _scale_vertices(
    vertices: tuple[tuple[float, float], ...],
    *,
    center: tuple[float, float],
) -> tuple[tuple[float, float], ...]:
    return tuple(
        (
            round(center[0] + ((vertex[0] - center[0]) * _POLYGON_SCALE), 6),
            round(center[1] + ((vertex[1] - center[1]) * _POLYGON_SCALE), 6),
        )
        for vertex in vertices
    )


def build_shield_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    max_distance = _distance_threshold(resolved_depth)
    selected_records = tuple(
        record
        for record in _load_reference_records()
        if int(record["graph_distance"]) <= max_distance
    )
    selected_ids = {record["id"] for record in selected_records}

    rotate_patch = resolved_depth % 2 == 1
    pivot = _reference_pivot()
    cells: list[AperiodicPatchCell] = []
    for record in selected_records:
        center = (float(record["center"][0]), float(record["center"][1]))
        vertices = tuple(
            (float(vertex[0]), float(vertex[1]))
            for vertex in record["vertices"]
        )
        orientation_token = record.get("orientation_token")
        decoration_tokens = record["decoration_tokens"]
        vertices = _scale_vertices(vertices, center=center)
        if rotate_patch:
            center = _rotate_point(
                center,
                pivot=pivot,
                radians=_ROTATION_STEP_RADIANS,
            )
            vertices = tuple(
                _rotate_point(vertex, pivot=pivot, radians=_ROTATION_STEP_RADIANS)
                for vertex in vertices
            )
            orientation_token = _rotate_orientation_token(
                orientation_token,
                degrees=_ROTATION_STEP_DEGREES,
            )

        cells.append(
            AperiodicPatchCell(
                id=record["id"],
                kind=record["kind"],
                center=center,
                vertices=vertices,
                neighbors=tuple(
                    neighbor_id
                    for neighbor_id in record["neighbors"]
                    if neighbor_id in selected_ids
                ),
                tile_family=record.get("tile_family"),
                orientation_token=orientation_token,
                chirality_token=record.get("chirality_token"),
                decoration_tokens=(
                    tuple(decoration_tokens)
                    if decoration_tokens is not None
                    else None
                ),
            )
        )

    return patch_from_cells(
        resolved_depth,
        sorted(cells, key=lambda cell: cell.id),
    )
