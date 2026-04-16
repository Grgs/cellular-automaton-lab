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
_TRACE_GAP_COMPENSATION_SCALE = 1.27
_DODECAGON_WINDOW_ANGLES = tuple(math.radians(step * 30) for step in range(12))
_DODECAGON_WINDOW_VECTORS = tuple(
    (math.cos(angle), math.sin(angle))
    for angle in _DODECAGON_WINDOW_ANGLES
)


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
    representative_window_thresholds: dict[str, float]
    records: list[_ShieldReferenceRecord]


@lru_cache(maxsize=1)
def _load_reference_payload() -> _ShieldReferencePayload:
    return json.loads(_DATA_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_reference_records() -> tuple[_ShieldReferenceRecord, ...]:
    return tuple(_load_reference_payload()["records"])


@lru_cache(maxsize=1)
def _window_thresholds() -> dict[int, float]:
    payload = _load_reference_payload()
    return {
        int(depth): float(distance)
        for depth, distance in payload["representative_window_thresholds"].items()
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


def _window_threshold(patch_depth: int) -> float:
    resolved_depth = max(0, int(patch_depth))
    thresholds = _window_thresholds()
    if resolved_depth in thresholds:
        return thresholds[resolved_depth]
    return thresholds[max(thresholds)]


def _dodecagon_window_distance(
    point: tuple[float, float],
    *,
    pivot: tuple[float, float],
) -> float:
    translated_x = point[0] - pivot[0]
    translated_y = point[1] - pivot[1]
    return max(
        abs((translated_x * axis_x) + (translated_y * axis_y))
        for axis_x, axis_y in _DODECAGON_WINDOW_VECTORS
    )


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


def _largest_connected_component_ids(
    selected_ids: set[str],
    *,
    record_by_id: dict[str, _ShieldReferenceRecord],
) -> set[str]:
    if not selected_ids:
        return set()
    remaining = set(selected_ids)
    components: list[list[str]] = []
    while remaining:
        start_id = min(remaining)
        pending = [start_id]
        component: list[str] = []
        remaining.remove(start_id)
        while pending:
            current_id = pending.pop()
            component.append(current_id)
            for neighbor_id in record_by_id[current_id]["neighbors"]:
                if neighbor_id in remaining:
                    remaining.remove(neighbor_id)
                    pending.append(neighbor_id)
        components.append(sorted(component))
    largest_component = max(
        components,
        key=lambda component: (len(component), tuple(component)),
    )
    return set(largest_component)


def _compensate_trace_gaps(
    vertices: tuple[tuple[float, float], ...],
    *,
    center: tuple[float, float],
) -> tuple[tuple[float, float], ...]:
    return tuple(
        (
            round(center[0] + ((vertex[0] - center[0]) * _TRACE_GAP_COMPENSATION_SCALE), 6),
            round(center[1] + ((vertex[1] - center[1]) * _TRACE_GAP_COMPENSATION_SCALE), 6),
        )
        for vertex in vertices
    )


def build_shield_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    pivot = _reference_pivot()
    max_window_distance = _window_threshold(resolved_depth)
    records = _load_reference_records()
    selected_records = tuple(
        record
        for record in records
        if _dodecagon_window_distance(
            (float(record["center"][0]), float(record["center"][1])),
            pivot=pivot,
        ) <= max_window_distance
    )
    selected_ids = {record["id"] for record in selected_records}
    record_by_id = {record["id"]: record for record in records}
    selected_ids = _largest_connected_component_ids(
        selected_ids,
        record_by_id=record_by_id,
    )
    selected_records = tuple(
        sorted(
            (
                record
                for record in selected_records
                if record["id"] in selected_ids
            ),
            key=lambda record: record["id"],
        )
    )

    rotate_patch = resolved_depth % 2 == 1
    cells: list[AperiodicPatchCell] = []
    for record in selected_records:
        center = (float(record["center"][0]), float(record["center"][1]))
        vertices = tuple(
            (float(vertex[0]), float(vertex[1]))
            for vertex in record["vertices"]
        )
        orientation_token = record.get("orientation_token")
        decoration_tokens = record["decoration_tokens"]
        vertices = _compensate_trace_gaps(vertices, center=center)
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
