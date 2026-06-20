from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from typing import NotRequired, TypedDict

from backend.payload_types import PeriodicFaceTilingDescriptorPayload, RawJsonObject
from backend.simulation.periodic_face_pattern_data import load_periodic_face_pattern_payloads
from backend.simulation.topology_family_manifest import TOPOLOGY_FAMILY_MANIFEST

_PERIODIC_FACE_PATTERN_KEYS = frozenset(load_periodic_face_pattern_payloads())
_UNREGISTERED_PERIODIC_FACE_PATTERNS = sorted(
    _PERIODIC_FACE_PATTERN_KEYS - TOPOLOGY_FAMILY_MANIFEST.keys()
)
if _UNREGISTERED_PERIODIC_FACE_PATTERNS:
    raise ValueError(
        "Periodic face descriptors missing topology manifest entries: "
        f"{_UNREGISTERED_PERIODIC_FACE_PATTERNS}"
    )
PERIODIC_FACE_TILING_GEOMETRIES = tuple(
    sorted(
        _PERIODIC_FACE_PATTERN_KEYS,
        key=lambda geometry: (
            TOPOLOGY_FAMILY_MANIFEST[geometry].picker_order,
            geometry,
        ),
    )
)

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
    # When set, switches the lattice from the row_offset_x "alternating brick"
    # semantic (only odd rows shifted) to a cumulative skew per row (every row
    # shifted by k * lattice_skew_x). Needed for genuinely-skewed-parallelogram
    # tilings like Stein-14 whose primitive cell is not axis-aligned.
    lattice_skew_x: float | None = None
    id_pattern: str = "{prefix}:{slot}:{x}:{y}"

    def to_frontend_dict(self) -> PeriodicFaceTilingDescriptorPayload:
        payload: PeriodicFaceTilingDescriptorPayload = {
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
        if self.lattice_skew_x is not None:
            payload["lattice_skew_x"] = self.lattice_skew_x
        return payload


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
    lattice_skew_x: NotRequired[float]
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
        "unit_width": _require_float(
            payload.get("unit_width"), context=f"{geometry_key}.unit_width"
        ),
        "unit_height": _require_float(
            payload.get("unit_height"), context=f"{geometry_key}.unit_height"
        ),
        "base_edge": _require_float(payload.get("base_edge"), context=f"{geometry_key}.base_edge"),
        "min_dimension": _require_int(
            payload.get("min_dimension"), context=f"{geometry_key}.min_dimension"
        ),
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
    lattice_skew_x = payload.get("lattice_skew_x")
    if lattice_skew_x is not None:
        normalized_payload["lattice_skew_x"] = _require_float(
            lattice_skew_x,
            context=f"{geometry_key}.lattice_skew_x",
        )
    id_pattern = payload.get("id_pattern")
    if id_pattern is not None:
        normalized_payload["id_pattern"] = _require_string(
            id_pattern,
            context=f"{geometry_key}.id_pattern",
        )
    return normalized_payload


def _load_pattern_payload() -> dict[str, _JsonPatternDescriptor]:
    normalized_payload: dict[str, _JsonPatternDescriptor] = {}
    for geometry_key, descriptor_payload in load_periodic_face_pattern_payloads().items():
        normalized_payload[geometry_key] = _require_pattern_descriptor_payload(
            descriptor_payload,
            geometry_key=geometry_key,
        )
    return normalized_payload


def _edge_key(
    left: tuple[float, float], right: tuple[float, float]
) -> tuple[tuple[float, float], tuple[float, float]]:
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


_T_JUNCTION_DISTANCE_TOLERANCE = 1e-3


def _point_on_segment(
    point: tuple[float, float],
    seg_start: tuple[float, float],
    seg_end: tuple[float, float],
    *,
    tolerance: float = _T_JUNCTION_DISTANCE_TOLERANCE,
) -> bool:
    """True iff ``point`` lies strictly inside the closed segment seg_start->
    seg_end (excluding the endpoints themselves), within ``tolerance`` in the
    perpendicular direction. Used to detect T-junction adjacency where one
    tile's vertex sits on the midpoint of another tile's edge."""
    px, py = point
    ax, ay = seg_start
    bx, by = seg_end
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    if length_sq < tolerance * tolerance:
        return False
    # Parametric position of point on the seg_start->seg_end line: t in [0, 1].
    t = ((px - ax) * dx + (py - ay) * dy) / length_sq
    if t <= tolerance or t >= 1.0 - tolerance:
        return False  # endpoint or off-segment, no T-junction
    # Perpendicular distance from point to line (a, b).
    proj_x = ax + t * dx
    proj_y = ay + t * dy
    perp_sq = (px - proj_x) ** 2 + (py - proj_y) ** 2
    return perp_sq <= tolerance * tolerance


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
                other_id for other_id in unique_edge_cells if other_id != cell_id
            )

    # T-junction adjacency: in non-edge-to-edge tilings like Stein-14, one
    # cell's vertex sits on the midpoint of another cell's edge. The two
    # cells share a half-edge but have no matching endpoint pair, so they
    # don't show up in edge_map.
    #
    # Restrict the scan to single-owner edges: an edge with 2+ owners is
    # already fully matched at its endpoints (typical edge-to-edge case),
    # so any vertex on its interior is either a degeneracy or already
    # captured by the edge-key match. Single-owner edges are the boundary
    # edges and the T-junction-carrying edges; only the latter benefit from
    # this pass. This skips >99% of the work in edge-to-edge tilings.
    #
    # For each single-owner edge, look up candidate vertices via a coarse
    # grid hash (cell side = max edge length we'd plausibly contain). This
    # avoids the O(V*E) all-pairs check that dominated previously.
    single_owner_edges = [
        (edge_key_tuple, edge_cells)
        for edge_key_tuple, edge_cells in edge_map.items()
        if len(set(edge_cells)) == 1
    ]
    if single_owner_edges:
        vertex_index: dict[tuple[float, float], set[str]] = {}
        for cell in cells:
            for vertex in cell.vertices:
                key = (round(vertex[0], 6), round(vertex[1], 6))
                vertex_index.setdefault(key, set()).add(cell.id)

        # Spatial hash: bin vertices by a coarse grid so each edge looks up
        # only the vertices that might lie inside its bounding box. Bin size
        # is chosen larger than the longest edge so every relevant vertex
        # falls in at most 2x2 bins relative to the edge midpoint.
        max_edge_length = 0.0
        for (a, b), _ in single_owner_edges:
            length = math.hypot(b[0] - a[0], b[1] - a[1])
            if length > max_edge_length:
                max_edge_length = length
        bin_size = max(max_edge_length, 1.0)
        vertex_bins: dict[tuple[int, int], list[tuple[float, float]]] = {}
        for vertex_key in vertex_index:
            bx = int(vertex_key[0] // bin_size)
            by = int(vertex_key[1] // bin_size)
            vertex_bins.setdefault((bx, by), []).append(vertex_key)

        for edge_key_tuple, edge_cells in single_owner_edges:
            edge_a, edge_b = edge_key_tuple
            edge_owner_set = set(edge_cells)
            # Look up vertices in bins that overlap the edge's bounding box.
            bx_lo = int(min(edge_a[0], edge_b[0]) // bin_size)
            bx_hi = int(max(edge_a[0], edge_b[0]) // bin_size)
            by_lo = int(min(edge_a[1], edge_b[1]) // bin_size)
            by_hi = int(max(edge_a[1], edge_b[1]) // bin_size)
            for bx in range(bx_lo, bx_hi + 1):
                for by in range(by_lo, by_hi + 1):
                    for vertex_key in vertex_bins.get((bx, by), ()):
                        if vertex_key == edge_a or vertex_key == edge_b:
                            continue
                        vertex_owners = vertex_index[vertex_key]
                        if vertex_owners.issubset(edge_owner_set):
                            continue
                        if not _point_on_segment(vertex_key, edge_a, edge_b):
                            continue
                        for edge_owner in edge_owner_set:
                            for vertex_owner in vertex_owners:
                                if vertex_owner == edge_owner:
                                    continue
                                neighbor_sets[edge_owner].add(vertex_owner)
                                neighbor_sets[vertex_owner].add(edge_owner)

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
    lattice_skew_x: float | None = None,
) -> tuple[PeriodicFaceCell, ...]:
    cells: list[PeriodicFaceCell] = []
    for face in faces:
        for logical_y in range(height + face.repeat_y_extra):
            translate_y = logical_y * unit_height
            if lattice_skew_x is not None:
                # Cumulative skew per row: every row shifts by k*lattice_skew_x.
                translate_x_offset = lattice_skew_x * logical_y
            else:
                # Alternating "brick" semantic: only odd rows shifted.
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


def _pattern_descriptor_from_payload(
    payload: _JsonPatternDescriptor,
) -> PeriodicFaceTilingDescriptor:
    faces = tuple(
        FaceTemplate(
            slot=face["slot"],
            kind=face["kind"],
            prefix=face["prefix"],
            center=(face["center"]["x"], face["center"]["y"]),
            vertices=tuple((vertex["x"], vertex["y"]) for vertex in face["vertices"]),
            repeat_x_extra=face.get("repeat_x_extra", 0),
            repeat_y_extra=face.get("repeat_y_extra", 0),
        )
        for face in payload["faces"]
    )
    geometry = payload["geometry"]
    manifest_entry = TOPOLOGY_FAMILY_MANIFEST.get(geometry)
    if manifest_entry is None:
        raise ValueError(f"Periodic face tiling geometry '{geometry}' is missing catalog metadata.")
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
    lattice_skew_x = payload.get("lattice_skew_x")
    id_pattern = payload.get("id_pattern", "{prefix}:{slot}:{x}:{y}")
    face_template_count = len(faces)
    face_kinds = tuple(sorted({face.kind for face in faces}))
    face_slots = tuple(sorted(face.slot for face in faces))

    return PeriodicFaceTilingDescriptor(
        geometry=geometry,
        label=manifest_entry.label,
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
            lattice_skew_x,
        ),
        face_template_count=face_template_count,
        face_kinds=face_kinds,
        face_slots=face_slots,
        row_offset_x=row_offset_x,
        lattice_skew_x=lattice_skew_x,
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


def build_periodic_face_cells(
    geometry: str, width: int, height: int
) -> tuple[PeriodicFaceCell, ...]:
    return get_periodic_face_tiling_descriptor(geometry).build_faces(width, height)
