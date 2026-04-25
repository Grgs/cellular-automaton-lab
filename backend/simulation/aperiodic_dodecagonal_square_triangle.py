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
_SUBSTITUTION_SPEC_DATA = (
    Path(__file__).with_name("data") / "dodecagonal_square_triangle_substitution_spec.json"
)
_MAX_PATCH_DEPTH = 40
_RUNTIME_SUBSTITUTION_LEVEL = 3
_EDGE_PRECISION = 6

_TILE_FAMILY = "dodecagonal-square-triangle"


@dataclass(frozen=True)
class _SourceCell:
    index: int
    kind: str
    chirality: str | None
    vertices: tuple[tuple[float, float], ...]
    neighbors: tuple[int, ...]


@dataclass(frozen=True)
class _SubstitutionChild:
    label: str
    transform: tuple[float, float, float, float, float, float]


@dataclass(frozen=True)
class _PublicMapping:
    kind: str
    chirality: str | None


@dataclass(frozen=True)
class _SubstitutionSpec:
    inflation_factor: float
    root_label: str
    prototypes: dict[str, tuple[tuple[float, float], ...]]
    public_mapping: dict[str, _PublicMapping]
    rules: dict[str, tuple[_SubstitutionChild, ...]]


@dataclass(frozen=True)
class _SubstitutionNode:
    label: str
    transform: tuple[float, float, float, float, float, float]
    path: tuple[int, ...]


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
        ((x - origin[0]) / unit_scale, (origin[1] - y) / unit_scale) for x, y in vertices
    )
    return _rotate_vertices(normalized)


def _orientation_token(vertices: tuple[tuple[float, float], ...]) -> str:
    angle = _edge_angle(vertices[0], vertices[1])
    snapped = int(round(angle / 30.0) * 30) % 360
    return str(snapped)


def _affine_apply(
    transform: tuple[float, float, float, float, float, float],
    point: tuple[float, float],
) -> tuple[float, float]:
    return (
        (transform[0] * point[0]) + (transform[1] * point[1]) + transform[2],
        (transform[3] * point[0]) + (transform[4] * point[1]) + transform[5],
    )


def _affine_multiply(
    left: tuple[float, float, float, float, float, float],
    right: tuple[float, float, float, float, float, float],
) -> tuple[float, float, float, float, float, float]:
    return (
        (left[0] * right[0]) + (left[1] * right[3]),
        (left[0] * right[1]) + (left[1] * right[4]),
        (left[0] * right[2]) + (left[1] * right[5]) + left[2],
        (left[3] * right[0]) + (left[4] * right[3]),
        (left[3] * right[1]) + (left[4] * right[4]),
        (left[3] * right[2]) + (left[4] * right[5]) + left[5],
    )


def _scale_transform(factor: float) -> tuple[float, float, float, float, float, float]:
    return (factor, 0.0, 0.0, 0.0, factor, 0.0)


def _node_id(path: tuple[int, ...]) -> str:
    encoded_path = ".".join(f"{part:02d}" for part in path) if path else "root"
    return f"dst:sub:{encoded_path}"


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
            neighbors=tuple(int(neighbor) for neighbor in cast(list[int], raw_cell["neighbors"])),
        )
        for raw_cell in cast(list[dict[str, object]], payload["cells"])
    }

    seed = cells[seed_index]
    seed_center = _polygon_center(seed.vertices)
    seed_scale = math.dist(seed.vertices[0], seed.vertices[1])
    return cells, seed_index, seed_center, seed_scale


@lru_cache(maxsize=1)
def _load_substitution_spec() -> _SubstitutionSpec:
    if not _SUBSTITUTION_SPEC_DATA.exists():
        raise FileNotFoundError(f"missing substitution spec: {_SUBSTITUTION_SPEC_DATA}")

    payload = cast(
        dict[str, object],
        json.loads(_SUBSTITUTION_SPEC_DATA.read_text(encoding="utf-8")),
    )
    prototypes = {
        str(label): tuple(
            (float(vertex[0]), float(vertex[1])) for vertex in cast(list[list[float]], vertices)
        )
        for label, vertices in cast(dict[str, object], payload["prototypes"]).items()
    }
    public_mapping = {
        str(label): _PublicMapping(
            kind=str(cast(dict[str, object], mapping)["kind"]),
            chirality=cast(str | None, cast(dict[str, object], mapping).get("chirality")),
        )
        for label, mapping in cast(dict[str, object], payload["public_mapping"]).items()
    }
    rules = {
        str(label): tuple(
            _SubstitutionChild(
                label=str(cast(dict[str, object], child)["label"]),
                transform=tuple(
                    float(value)
                    for value in cast(list[float], cast(dict[str, object], child)["transform"])
                ),
            )
            for child in cast(list[object], children)
        )
        for label, children in cast(dict[str, object], payload["rules"]).items()
    }
    return _SubstitutionSpec(
        inflation_factor=float(cast(dict[str, object], payload["inflation_factor"])["value"]),
        root_label=str(payload["root_label"]),
        prototypes=prototypes,
        public_mapping=public_mapping,
        rules=rules,
    )


def _expand_nodes(spec: _SubstitutionSpec, level: int) -> tuple[_SubstitutionNode, ...]:
    nodes = (
        _SubstitutionNode(
            label=spec.root_label,
            transform=_scale_transform(spec.inflation_factor**level),
            path=(),
        ),
    )
    for _round in range(level):
        expanded: list[_SubstitutionNode] = []
        for node in nodes:
            for child_index, child in enumerate(spec.rules[node.label]):
                expanded.append(
                    _SubstitutionNode(
                        label=child.label,
                        transform=_affine_multiply(node.transform, child.transform),
                        path=(*node.path, child_index),
                    )
                )
        nodes = tuple(expanded)
    return nodes


def _records_for_nodes(
    spec: _SubstitutionSpec,
    nodes: tuple[_SubstitutionNode, ...],
) -> list[PatchRecord]:
    records: list[PatchRecord] = []
    for node in nodes:
        vertices = tuple(
            _affine_apply(node.transform, vertex) for vertex in spec.prototypes[node.label]
        )
        center = _polygon_center(vertices)
        public = spec.public_mapping[node.label]
        records.append(
            {
                "id": _node_id(node.path),
                "kind": public.kind,
                "center": (round(center[0], 9), round(center[1], 9)),
                "vertices": tuple((round(x, 9), round(y, 9)) for x, y in vertices),
                "tile_family": _TILE_FAMILY,
                "orientation_token": _orientation_token(vertices),
                "chirality_token": public.chirality,
                "decoration_tokens": None,
            }
        )
    return records


def _distances_from_seed(patch: AperiodicPatch) -> dict[str, int]:
    by_id = {cell.id: cell for cell in patch.cells}
    component_by_id: dict[str, int] = {}
    components: list[list[str]] = []
    for cell in patch.cells:
        if cell.id in component_by_id:
            continue
        component_index = len(components)
        components.append([])
        queue: deque[str] = deque((cell.id,))
        component_by_id[cell.id] = component_index
        while queue:
            current = queue.popleft()
            components[component_index].append(current)
            for neighbor_id in by_id[current].neighbors:
                if neighbor_id in component_by_id:
                    continue
                component_by_id[neighbor_id] = component_index
                queue.append(neighbor_id)

    largest_component = max(
        components,
        key=lambda component: (
            len(component),
            -min(
                (by_id[cell_id].center[0] ** 2) + (by_id[cell_id].center[1] ** 2)
                for cell_id in component
            ),
        ),
    )
    degree_four_ids = [
        cell_id for cell_id in largest_component if len(by_id[cell_id].neighbors) == 4
    ]
    seed_candidates = degree_four_ids if degree_four_ids else largest_component
    seed_id = min(
        seed_candidates,
        key=lambda cell_id: (
            (by_id[cell_id].center[0] ** 2) + (by_id[cell_id].center[1] ** 2),
            cell_id,
        ),
    )

    distances: dict[str, int] = {seed_id: 0}
    queue = deque((seed_id,))
    while queue:
        current = queue.popleft()
        for neighbor_id in by_id[current].neighbors:
            if neighbor_id in distances:
                continue
            distances[neighbor_id] = distances[current] + 1
            queue.append(neighbor_id)
    return distances


@lru_cache(maxsize=1)
def _runtime_substitution_patch() -> AperiodicPatch:
    spec = _load_substitution_spec()
    return patch_from_records(
        _RUNTIME_SUBSTITUTION_LEVEL,
        _records_for_nodes(spec, _expand_nodes(spec, _RUNTIME_SUBSTITUTION_LEVEL)),
        edge_precision=_EDGE_PRECISION,
    )


@lru_cache(maxsize=1)
def _runtime_substitution_distances() -> dict[str, int]:
    return _distances_from_seed(_runtime_substitution_patch())


def _build_substitution_patch(patch_depth: int) -> AperiodicPatch:
    spec = _load_substitution_spec()
    if patch_depth == 0:
        return patch_from_records(
            patch_depth,
            _records_for_nodes(spec, _expand_nodes(spec, 0)),
            edge_precision=_EDGE_PRECISION,
        )

    full_patch = _runtime_substitution_patch()
    distances = _runtime_substitution_distances()
    if max(distances.values(), default=0) < patch_depth:
        raise ValueError(
            f"patch_depth {patch_depth} exceeds generated dodecagonal substitution support "
            f"at level {_RUNTIME_SUBSTITUTION_LEVEL}"
        )

    selected_ids = {cell_id for cell_id, distance in distances.items() if distance <= patch_depth}
    selected_records: list[PatchRecord] = []
    for cell in full_patch.cells:
        if cell.id not in selected_ids:
            continue
        selected_records.append(
            {
                "id": cell.id,
                "kind": cell.kind,
                "center": cell.center,
                "vertices": cell.vertices,
                "tile_family": cell.tile_family,
                "orientation_token": cell.orientation_token,
                "chirality_token": cell.chirality_token,
                "decoration_tokens": cell.decoration_tokens,
            }
        )
    return patch_from_records(
        patch_depth,
        selected_records,
        edge_precision=_EDGE_PRECISION,
    )


def build_dodecagonal_square_triangle_rule_image_diagnostic_patch(
    patch_depth: int,
) -> AperiodicPatch:
    """Build the experimental rule-image path for diagnostics only.

    The Bielefeld rule image describes valid one-level patch rules, but the
    current five labels are not enough to recursively substitute public tiles
    without overlaps. Keep this callable so the extracted spec can be studied
    without exposing it as the runtime generator.
    """
    resolved_depth = int(patch_depth)
    if resolved_depth < 0:
        raise ValueError("patch_depth must be non-negative")
    return _build_substitution_patch(resolved_depth)


def build_dodecagonal_square_triangle_literature_oracle_patch(
    patch_depth: int,
) -> AperiodicPatch:
    resolved_depth = int(patch_depth)
    if resolved_depth < 0:
        raise ValueError("patch_depth must be non-negative")
    if resolved_depth > _MAX_PATCH_DEPTH:
        raise ValueError(
            f"patch_depth {resolved_depth} exceeds available literature crop depth {_MAX_PATCH_DEPTH}"
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


def build_dodecagonal_square_triangle_patch(patch_depth: int) -> AperiodicPatch:
    resolved_depth = int(patch_depth)
    if resolved_depth < 0:
        raise ValueError("patch_depth must be non-negative")
    if resolved_depth > _MAX_PATCH_DEPTH:
        raise ValueError(
            f"patch_depth {resolved_depth} exceeds configured dodecagonal depth {_MAX_PATCH_DEPTH}"
        )
    return build_dodecagonal_square_triangle_literature_oracle_patch(resolved_depth)
