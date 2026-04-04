from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
import math
from pathlib import Path
from typing import Callable, NotRequired, TypedDict

from backend.payload_types import PeriodicFaceTilingDescriptorPayload, RawJsonObject
from backend.simulation.topology_catalog import (
    ARCHIMEDEAN_31212_GEOMETRY,
    ARCHIMEDEAN_33336_GEOMETRY,
    ARCHIMEDEAN_33344_GEOMETRY,
    ARCHIMEDEAN_33434_GEOMETRY,
    ARCHIMEDEAN_3464_GEOMETRY,
    ARCHIMEDEAN_4612_GEOMETRY,
    ARCHIMEDEAN_488_GEOMETRY,
    CAIRO_GEOMETRY,
    DELTOIDAL_HEXAGONAL_GEOMETRY,
    DELTOIDAL_TRIHEXAGONAL_GEOMETRY,
    FLORET_PENTAGONAL_GEOMETRY,
    KAGOME_GEOMETRY,
    PRISMATIC_PENTAGONAL_GEOMETRY,
    RHOMBILLE_GEOMETRY,
    SNUB_SQUARE_DUAL_GEOMETRY,
    TETRAKIS_SQUARE_GEOMETRY,
    TRIAKIS_TRIANGULAR_GEOMETRY,
)

PERIODIC_FACE_TILING_GEOMETRIES = (
    ARCHIMEDEAN_488_GEOMETRY,
    ARCHIMEDEAN_31212_GEOMETRY,
    ARCHIMEDEAN_3464_GEOMETRY,
    ARCHIMEDEAN_4612_GEOMETRY,
    ARCHIMEDEAN_33434_GEOMETRY,
    ARCHIMEDEAN_33344_GEOMETRY,
    ARCHIMEDEAN_33336_GEOMETRY,
    KAGOME_GEOMETRY,
    CAIRO_GEOMETRY,
    RHOMBILLE_GEOMETRY,
    DELTOIDAL_HEXAGONAL_GEOMETRY,
    DELTOIDAL_TRIHEXAGONAL_GEOMETRY,
    TETRAKIS_SQUARE_GEOMETRY,
    TRIAKIS_TRIANGULAR_GEOMETRY,
    PRISMATIC_PENTAGONAL_GEOMETRY,
    FLORET_PENTAGONAL_GEOMETRY,
    SNUB_SQUARE_DUAL_GEOMETRY,
)

_DATA_PATH = Path(__file__).with_name("data") / "periodic_face_patterns.json"
_ANGLE_START = -3 * math.pi / 4


@dataclass(frozen=True)
class FaceTemplate:
    slot: str
    kind: str
    prefix: str
    center: tuple[float, float]
    vertices: tuple[tuple[float, float], ...]
    repeat_x_extra: int = 0
    repeat_y_extra: int = 0


@dataclass(frozen=True)
class PeriodicFaceCell:
    id: str
    kind: str
    slot: str
    neighbors: tuple[str, ...]
    center: tuple[float, float]
    vertices: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class PeriodicFaceTilingDescriptor:
    geometry: str
    label: str
    metric_model: str
    base_edge: float
    unit_width: float
    unit_height: float
    min_dimension: int
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    cell_count_per_unit: int
    build_faces: Callable[[int, int], tuple[PeriodicFaceCell, ...]]
    face_template_count: int
    face_kinds: tuple[str, ...]
    face_slots: tuple[str, ...]
    row_offset_x: float = 0.0
    id_pattern: str = "{prefix}:{slot}:{x}:{y}"

    def to_frontend_dict(self) -> PeriodicFaceTilingDescriptorPayload:
        return {
            "geometry": self.geometry,
            "label": self.label,
            "metric_model": self.metric_model,
            "base_edge": self.base_edge,
            "unit_width": self.unit_width,
            "unit_height": self.unit_height,
            "min_dimension": self.min_dimension,
            "min_x": self.min_x,
            "min_y": self.min_y,
            "max_x": self.max_x,
            "max_y": self.max_y,
            "cell_count_per_unit": self.cell_count_per_unit,
            "row_offset_x": self.row_offset_x,
        }


class _JsonPoint(TypedDict):
    x: float
    y: float


class _JsonFace(TypedDict):
    slot: str
    kind: str
    prefix: str
    center: _JsonPoint
    vertices: list[_JsonPoint]
    repeat_x_extra: NotRequired[int]
    repeat_y_extra: NotRequired[int]


class _JsonPatternDescriptor(TypedDict):
    geometry: str
    label: str
    unit_width: float
    unit_height: float
    base_edge: float
    min_dimension: int
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    cell_count_per_unit: int
    faces: list[_JsonFace]
    row_offset_x: NotRequired[float]
    id_pattern: NotRequired[str]


def _require_object(value: object, *, context: str) -> RawJsonObject:
    if not isinstance(value, dict):
        raise ValueError(f"{context} is invalid.")
    return value


def _require_string(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context} is invalid.")
    return value


def _require_int(value: object, *, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{context} is invalid.")
    return value


def _require_float(value: object, *, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{context} is invalid.")
    return float(value)


def _require_point_payload(value: object, *, context: str) -> _JsonPoint:
    payload = _require_object(value, context=context)
    return {
        "x": _require_float(payload.get("x"), context=f"{context}.x"),
        "y": _require_float(payload.get("y"), context=f"{context}.y"),
    }


def _require_face_payload(value: object, *, context: str) -> _JsonFace:
    payload = _require_object(value, context=context)
    vertices_value = payload.get("vertices")
    if not isinstance(vertices_value, list):
        raise ValueError(f"{context}.vertices is invalid.")
    normalized_face: _JsonFace = {
        "slot": _require_string(payload.get("slot"), context=f"{context}.slot"),
        "kind": _require_string(payload.get("kind"), context=f"{context}.kind"),
        "prefix": _require_string(payload.get("prefix"), context=f"{context}.prefix"),
        "center": _require_point_payload(payload.get("center"), context=f"{context}.center"),
        "vertices": [
            _require_point_payload(vertex, context=f"{context}.vertices[{index}]")
            for index, vertex in enumerate(vertices_value)
        ],
    }
    repeat_x_extra = payload.get("repeat_x_extra")
    if repeat_x_extra is not None:
        normalized_face["repeat_x_extra"] = _require_int(
            repeat_x_extra,
            context=f"{context}.repeat_x_extra",
        )
    repeat_y_extra = payload.get("repeat_y_extra")
    if repeat_y_extra is not None:
        normalized_face["repeat_y_extra"] = _require_int(
            repeat_y_extra,
            context=f"{context}.repeat_y_extra",
        )
    return normalized_face


def _require_pattern_descriptor_payload(
    value: object,
    *,
    geometry_key: str,
) -> _JsonPatternDescriptor:
    payload = _require_object(value, context=f"Periodic face tiling descriptor '{geometry_key}'")
    faces_value = payload.get("faces")
    if not isinstance(faces_value, list):
        raise ValueError(f"Periodic face tiling descriptor '{geometry_key}'.faces is invalid.")
    normalized_payload: _JsonPatternDescriptor = {
        "geometry": _require_string(payload.get("geometry"), context=f"{geometry_key}.geometry"),
        "label": _require_string(payload.get("label"), context=f"{geometry_key}.label"),
        "unit_width": _require_float(payload.get("unit_width"), context=f"{geometry_key}.unit_width"),
        "unit_height": _require_float(payload.get("unit_height"), context=f"{geometry_key}.unit_height"),
        "base_edge": _require_float(payload.get("base_edge"), context=f"{geometry_key}.base_edge"),
        "min_dimension": _require_int(payload.get("min_dimension"), context=f"{geometry_key}.min_dimension"),
        "min_x": _require_float(payload.get("min_x"), context=f"{geometry_key}.min_x"),
        "min_y": _require_float(payload.get("min_y"), context=f"{geometry_key}.min_y"),
        "max_x": _require_float(payload.get("max_x"), context=f"{geometry_key}.max_x"),
        "max_y": _require_float(payload.get("max_y"), context=f"{geometry_key}.max_y"),
        "cell_count_per_unit": _require_int(
            payload.get("cell_count_per_unit"),
            context=f"{geometry_key}.cell_count_per_unit",
        ),
        "faces": [
            _require_face_payload(face, context=f"{geometry_key}.faces[{index}]")
            for index, face in enumerate(faces_value)
        ],
    }
    row_offset_x = payload.get("row_offset_x")
    if row_offset_x is not None:
        normalized_payload["row_offset_x"] = _require_float(
            row_offset_x,
            context=f"{geometry_key}.row_offset_x",
        )
    id_pattern = payload.get("id_pattern")
    if id_pattern is not None:
        normalized_payload["id_pattern"] = _require_string(
            id_pattern,
            context=f"{geometry_key}.id_pattern",
        )
    return normalized_payload


def _load_pattern_payload() -> dict[str, _JsonPatternDescriptor]:
    payload = _require_object(
        json.loads(_DATA_PATH.read_text(encoding="utf-8")),
        context="Periodic face tiling data payload",
    )
    normalized_payload: dict[str, _JsonPatternDescriptor] = {}
    for geometry_key, descriptor_payload in payload.items():
        if not isinstance(geometry_key, str) or not geometry_key:
            raise ValueError("Periodic face tiling data payload is invalid.")
        normalized_payload[geometry_key] = _require_pattern_descriptor_payload(
            descriptor_payload,
            geometry_key=geometry_key,
        )
    return normalized_payload


def _edge_key(left: tuple[float, float], right: tuple[float, float]) -> tuple[tuple[float, float], tuple[float, float]]:
    normalized_left = (round(left[0], 6), round(left[1], 6))
    normalized_right = (round(right[0], 6), round(right[1], 6))
    return (
        (normalized_left, normalized_right)
        if normalized_left <= normalized_right
        else (normalized_right, normalized_left)
    )


def _sort_neighbor_ids(
    cell: PeriodicFaceCell,
    neighbor_ids: set[str],
    cells_by_id: dict[str, PeriodicFaceCell],
) -> tuple[str, ...]:
    center_x, center_y = cell.center

    def sort_key(neighbor_id: str) -> tuple[float, float, str]:
        neighbor = cells_by_id[neighbor_id]
        delta_x = neighbor.center[0] - center_x
        delta_y = neighbor.center[1] - center_y
        angle = (math.atan2(delta_y, delta_x) - _ANGLE_START) % (2 * math.pi)
        distance = (delta_x * delta_x) + (delta_y * delta_y)
        return (round(angle, 8), round(distance, 8), neighbor_id)

    return tuple(sorted(neighbor_ids, key=sort_key))


def _attach_neighbors(cells: list[PeriodicFaceCell]) -> tuple[PeriodicFaceCell, ...]:
    cells_by_id = {cell.id: cell for cell in cells}
    edge_map: dict[tuple[tuple[float, float], tuple[float, float]], list[str]] = {}

    for cell in cells:
        vertices = cell.vertices
        for index, left in enumerate(vertices):
            right = vertices[(index + 1) % len(vertices)]
            edge_map.setdefault(_edge_key(left, right), []).append(cell.id)

    neighbor_sets: dict[str, set[str]] = {cell.id: set() for cell in cells}
    for edge_cells in edge_map.values():
        unique_edge_cells = tuple(dict.fromkeys(edge_cells))
        if len(unique_edge_cells) < 2:
            continue
        for cell_id in unique_edge_cells:
            neighbor_sets[cell_id].update(
                other_id
                for other_id in unique_edge_cells
                if other_id != cell_id
            )

    return tuple(
        PeriodicFaceCell(
            id=cell.id,
            kind=cell.kind,
            slot=cell.slot,
            neighbors=_sort_neighbor_ids(cell, neighbor_sets[cell.id], cells_by_id),
            center=cell.center,
            vertices=cell.vertices,
        )
        for cell in cells
    )


def _pattern_cells(
    unit_width: float,
    unit_height: float,
    faces: tuple[FaceTemplate, ...],
    row_offset_x: float,
    id_pattern: str,
    width: int,
    height: int,
) -> tuple[PeriodicFaceCell, ...]:
    cells: list[PeriodicFaceCell] = []
    for face in faces:
        for logical_y in range(height + face.repeat_y_extra):
            translate_y = logical_y * unit_height
            translate_x_offset = row_offset_x if logical_y % 2 == 1 else 0.0
            for logical_x in range(width + face.repeat_x_extra):
                translate_x = (logical_x * unit_width) + translate_x_offset
                cells.append(
                    PeriodicFaceCell(
                        id=id_pattern.format(
                            prefix=face.prefix,
                            slot=face.slot,
                            x=logical_x,
                            y=logical_y,
                        ),
                        kind=face.kind,
                        slot=face.slot,
                        neighbors=(),
                        center=(face.center[0] + translate_x, face.center[1] + translate_y),
                        vertices=tuple(
                            (vertex_x + translate_x, vertex_y + translate_y)
                            for vertex_x, vertex_y in face.vertices
                        ),
                    )
                )

    return _attach_neighbors(cells)


def _pattern_descriptor_from_payload(payload: _JsonPatternDescriptor) -> PeriodicFaceTilingDescriptor:
    faces = tuple(
        FaceTemplate(
            slot=face["slot"],
            kind=face["kind"],
            prefix=face["prefix"],
            center=(face["center"]["x"], face["center"]["y"]),
            vertices=tuple(
                (vertex["x"], vertex["y"])
                for vertex in face["vertices"]
            ),
            repeat_x_extra=face.get("repeat_x_extra", 0),
            repeat_y_extra=face.get("repeat_y_extra", 0),
        )
        for face in payload["faces"]
    )
    geometry = payload["geometry"]
    label = payload["label"]
    unit_width = payload["unit_width"]
    unit_height = payload["unit_height"]
    base_edge = payload["base_edge"]
    min_dimension = payload["min_dimension"]
    min_x = payload["min_x"]
    min_y = payload["min_y"]
    max_x = payload["max_x"]
    max_y = payload["max_y"]
    cell_count_per_unit = payload["cell_count_per_unit"]
    row_offset_x = payload.get("row_offset_x", 0.0)
    id_pattern = payload.get("id_pattern", "{prefix}:{slot}:{x}:{y}")
    face_template_count = len(faces)
    face_kinds = tuple(sorted({face.kind for face in faces}))
    face_slots = tuple(sorted(face.slot for face in faces))

    return PeriodicFaceTilingDescriptor(
        geometry=geometry,
        label=label,
        metric_model="pattern",
        base_edge=base_edge,
        unit_width=unit_width,
        unit_height=unit_height,
        min_dimension=min_dimension,
        min_x=min_x,
        min_y=min_y,
        max_x=max_x,
        max_y=max_y,
        cell_count_per_unit=cell_count_per_unit,
        build_faces=lambda width, height: _pattern_cells(
            unit_width,
            unit_height,
            faces,
            row_offset_x,
            id_pattern,
            width,
            height,
        ),
        face_template_count=face_template_count,
        face_kinds=face_kinds,
        face_slots=face_slots,
        row_offset_x=row_offset_x,
        id_pattern=id_pattern,
    )


@lru_cache(maxsize=1)
def _loaded_pattern_descriptors() -> dict[str, PeriodicFaceTilingDescriptor]:
    payload = _load_pattern_payload()
    return {
        geometry: _pattern_descriptor_from_payload(descriptor_payload)
        for geometry, descriptor_payload in payload.items()
    }


@lru_cache(maxsize=1)
def _descriptor_registry() -> dict[str, PeriodicFaceTilingDescriptor]:
    return _loaded_pattern_descriptors()


def is_periodic_face_tiling(geometry: str) -> bool:
    return geometry in _descriptor_registry()


def get_periodic_face_tiling_descriptor(geometry: str) -> PeriodicFaceTilingDescriptor:
    return _descriptor_registry()[geometry]


def describe_periodic_face_tilings() -> list[PeriodicFaceTilingDescriptorPayload]:
    return [
        _descriptor_registry()[geometry].to_frontend_dict()
        for geometry in PERIODIC_FACE_TILING_GEOMETRIES
        if geometry in _descriptor_registry()
    ]


def build_periodic_face_cells(geometry: str, width: int, height: int) -> tuple[PeriodicFaceCell, ...]:
    return get_periodic_face_tiling_descriptor(geometry).build_faces(width, height)
