from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import json
import math
from typing import cast

from backend.simulation.aperiodic_support import AperiodicPatch, PatchRecord, patch_from_records


_SOURCE_PATCH_DATA = (
    Path(__file__).with_name("data") / "dodecagonal_square_triangle_literature_source.json"
)
_MAX_PATCH_DEPTH = 7
_EDGE_PRECISION = 6

_TILE_FAMILY = "dodecagonal-square-triangle"
@dataclass(frozen=True)
class _SourceCell:
    index: int
    kind: str
    chirality: str | None
    vertices: tuple[tuple[float, float], ...]
    neighbors: tuple[int, ...]


def _edge_angle(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360.0


def _rotate_vertices(
    vertices: tuple[tuple[float, float], ...],
) -> tuple[tuple[float, float], ...]:
    rotations: list[tuple[float, tuple[tuple[float, float], ...]]] = []
    for offset in range(len(vertices)):
        rotated = vertices[offset:] + vertices[:offset]
        angle = _edge_angle(rotated[0], rotated[1])
        rotations.append((round(angle, 6), tuple(rotated)))
    return min(rotations, key=lambda item: item[0])[1]


def _polygon_center(vertices: tuple[tuple[float, float], ...]) -> tuple[float, float]:
    count = len(vertices)
    return (
        sum(x for x, _ in vertices) / count,
        sum(y for _, y in vertices) / count,
    )


def _normalize_vertices(
    vertices: tuple[tuple[float, float], ...],
    *,
    origin: tuple[float, float],
    unit_scale: float,
) -> tuple[tuple[float, float], ...]:
    normalized = tuple(
        ((x - origin[0]) / unit_scale, (origin[1] - y) / unit_scale)
        for x, y in vertices
    )
    return _rotate_vertices(normalized)


def _orientation_token(vertices: tuple[tuple[float, float], ...]) -> str:
    angle = _edge_angle(vertices[0], vertices[1])
    snapped = int(round(angle / 30.0) * 30) % 360
    return str(snapped)


@lru_cache(maxsize=1)
def _load_source_patch() -> tuple[dict[int, _SourceCell], int, tuple[float, float], float]:
    if not _SOURCE_PATCH_DATA.exists():
        raise FileNotFoundError(f"missing literature source: {_SOURCE_PATCH_DATA}")

    payload = cast(dict[str, object], json.loads(_SOURCE_PATCH_DATA.read_text(encoding="utf-8")))
    seed_index = int(cast(int, payload["seed_index"]))
    cells = {
        int(cast(int, raw_cell["index"])): _SourceCell(
            index=int(cast(int, raw_cell["index"])),
            kind=str(raw_cell["kind"]),
            chirality=cast(str | None, raw_cell.get("chirality")),
            vertices=tuple(
                (float(vertex[0]), float(vertex[1]))
                for vertex in cast(list[list[float]], raw_cell["vertices"])
            ),
            neighbors=tuple(
                int(neighbor)
                for neighbor in cast(list[int], raw_cell["neighbors"])
            ),
        )
        for raw_cell in cast(list[dict[str, object]], payload["cells"])
    }

    seed = cells[seed_index]
    seed_center = _polygon_center(seed.vertices)
    seed_scale = math.dist(seed.vertices[0], seed.vertices[1])
    return cells, seed_index, seed_center, seed_scale


def build_dodecagonal_square_triangle_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = int(patch_depth)
    if resolved_depth < 0:
        raise ValueError("patch_depth must be non-negative")
    if resolved_depth > _MAX_PATCH_DEPTH:
        raise ValueError(
            f"patch_depth {resolved_depth} exceeds validated literature crop depth {_MAX_PATCH_DEPTH}"
        )

    cells, seed_index, seed_center, unit_scale = _load_source_patch()

    distances: dict[int, int] = {seed_index: 0}
    queue: deque[int] = deque((seed_index,))
    while queue:
        current = queue.popleft()
        if distances[current] == resolved_depth:
            continue
        for neighbor in cells[current].neighbors:
            if neighbor in distances:
                continue
            distances[neighbor] = distances[current] + 1
            queue.append(neighbor)

    selected_indexes = sorted(distances, key=lambda index: (distances[index], index))
    records: list[PatchRecord] = []
    for index in selected_indexes:
        vertices = _normalize_vertices(
            cells[index].vertices,
            origin=seed_center,
            unit_scale=unit_scale,
        )
        center = _polygon_center(vertices)
        records.append(
            {
                "id": f"dst:lit:{index:05d}",
                "kind": cells[index].kind,
                "center": (round(center[0], 9), round(center[1], 9)),
                "vertices": tuple((round(x, 9), round(y, 9)) for x, y in vertices),
                "tile_family": _TILE_FAMILY,
                "orientation_token": _orientation_token(vertices),
                "chirality_token": cells[index].chirality,
                "decoration_tokens": None,
            }
        )

    return patch_from_records(
        resolved_depth,
        records,
        edge_precision=_EDGE_PRECISION,
    )
