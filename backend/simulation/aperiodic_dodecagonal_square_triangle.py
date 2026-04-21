from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any, cast

from backend.simulation.aperiodic_support import AperiodicPatch, PatchRecord, patch_from_records


# This family currently ships as a backend-owned validated public patch sample rather than
# as a symbolic substitution generator. The checked-in reference data is a deterministic
# connected, hole-free subset of the literature patch, annotated with graph distance so the
# app can expose stable patch-depth shells without re-running any cleanup logic at runtime.
_DATA_PATH = Path(__file__).with_name("data") / "dodecagonal_square_triangle_reference_patch.json"
_PATCH_DISTANCE_THRESHOLDS = {
    0: 4,
    1: 16,
    2: 40,
    3: 76,
    4: 97,
}


@lru_cache(maxsize=1)
def _load_payload() -> dict[str, object]:
    return json.loads(_DATA_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_reference_records() -> tuple[PatchRecord, ...]:
    payload = _load_payload()
    raw_records = cast(list[dict[str, Any]], payload["records"])
    records: list[PatchRecord] = []
    for raw_record in raw_records:
        records.append(
            {
                "id": raw_record["id"],
                "kind": raw_record["kind"],
                "center": tuple(raw_record["center"]),
                "vertices": tuple(tuple(vertex) for vertex in raw_record["vertices"]),
                "tile_family": raw_record.get("tile_family"),
                "orientation_token": raw_record.get("orientation_token"),
                "chirality_token": raw_record.get("chirality_token"),
                "decoration_tokens": (
                    tuple(raw_record["decoration_tokens"])
                    if raw_record.get("decoration_tokens") is not None
                    else None
                ),
            }
        )
    return tuple(records)


@lru_cache(maxsize=1)
def _load_record_distances() -> dict[str, int]:
    payload = _load_payload()
    raw_records = cast(list[dict[str, Any]], payload["records"])
    return {
        raw_record["id"]: int(raw_record["graph_distance"])
        for raw_record in raw_records
    }


def _distance_threshold(patch_depth: int) -> int:
    resolved_depth = max(0, int(patch_depth))
    available_depths = sorted(_PATCH_DISTANCE_THRESHOLDS)
    if resolved_depth in _PATCH_DISTANCE_THRESHOLDS:
        return _PATCH_DISTANCE_THRESHOLDS[resolved_depth]
    if resolved_depth <= available_depths[0]:
        return _PATCH_DISTANCE_THRESHOLDS[available_depths[0]]
    return _PATCH_DISTANCE_THRESHOLDS[available_depths[-1]]


def build_dodecagonal_square_triangle_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = max(0, int(patch_depth))
    max_distance = _distance_threshold(resolved_depth)
    record_distances = _load_record_distances()
    records = [
        record
        for record in _load_reference_records()
        if record_distances[record["id"]] <= max_distance
    ]
    return patch_from_records(resolved_depth, records, edge_precision=6)
