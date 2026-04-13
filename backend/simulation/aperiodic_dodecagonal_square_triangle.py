from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from backend.simulation.aperiodic_support import AperiodicPatch, PatchRecord, patch_from_records


# This checked-in patch is a cleaned dense central component from the dodecagonal square-triangle
# literature patch. A few stray fringe triangles are excluded to keep the public sample
# connected and overlap-free while still presenting a visibly bulk-filled patch.
_DATA_PATH = Path(__file__).with_name("data") / "dodecagonal_square_triangle_reference_patch.json"
_EXCLUDED_RECORD_IDS = frozenset(
    {
        "sqtri:ref:05726",
        "sqtri:ref:05782",
        "sqtri:ref:06625",
    }
)
_PATCH_DISTANCE_THRESHOLDS = {
    0: 4,
    1: 16,
    2: 40,
    3: 76,
    4: 97,
}


@lru_cache(maxsize=1)
def _load_reference_records() -> tuple[PatchRecord, ...]:
    payload = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    records: list[PatchRecord] = []
    for raw_record in payload["records"]:
        if raw_record["id"] in _EXCLUDED_RECORD_IDS:
            continue
        records.append(
            {
                "id": raw_record["id"],
                "kind": raw_record["kind"],
                "center": tuple(raw_record["center"]),
                "vertices": tuple(tuple(vertex) for vertex in raw_record["vertices"]),
                "tile_family": raw_record.get("tile_family"),
                "orientation_token": raw_record.get("orientation_token"),
                "chirality_token": raw_record.get("chirality_token"),
                "decoration_tokens": raw_record.get("decoration_tokens"),
            }
        )
    return tuple(records)


@lru_cache(maxsize=1)
def _load_record_distances() -> dict[str, int]:
    payload = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    return {
        raw_record["id"]: int(raw_record["graph_distance"])
        for raw_record in payload["records"]
        if raw_record["id"] not in _EXCLUDED_RECORD_IDS
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
