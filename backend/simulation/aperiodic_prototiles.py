from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, TypedDict

from backend.simulation.topology_catalog import (
    AMMANN_BEENKER_GEOMETRY,
    PENROSE_GEOMETRY,
    PENROSE_P2_GEOMETRY,
    PENROSE_VERTEX_GEOMETRY,
    SPECTRE_GEOMETRY,
)
from backend.simulation.penrose import (
    PENROSE_EDGE_ADJACENCY,
    PENROSE_VERTEX_ADJACENCY,
    build_penrose_patch,
)


PHI = (1 + math.sqrt(5)) / 2
SILVER_RATIO = 1 + math.sqrt(2)
COORDINATE_PRECISION = 6

_Affine = tuple[float, float, float, float, float, float]
_AFFINE_IDENTITY: _Affine = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0)
_AFFINE_REFLECT_X: _Affine = (-1.0, 0.0, 0.0, 0.0, 1.0, 0.0)


@dataclass(frozen=True)
class AperiodicPatchCell:
    id: str
    kind: str
    center: tuple[float, float]
    vertices: tuple[tuple[float, float], ...]
    neighbors: tuple[str, ...]


@dataclass(frozen=True)
class AperiodicPatch:
    patch_depth: int
    width: int
    height: int
    cells: tuple[AperiodicPatchCell, ...]


@dataclass(frozen=True)
class _Vec:
    x: float
    y: float

    def __add__(self, other: "_Vec") -> "_Vec":
        return _Vec(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "_Vec") -> "_Vec":
        return _Vec(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "_Vec":
        return _Vec(self.x * scalar, self.y * scalar)


@dataclass(frozen=True)
class _LeafTile:
    kind: str
    vertices: tuple[_Vec, ...]
    center: _Vec
    anchor: _Vec
    orientation: int


@dataclass(frozen=True)
class _SpectreTemplate:
    quad: tuple[_Vec, _Vec, _Vec, _Vec]
    children: tuple[tuple[str, _Affine], ...]


class _PatchRecord(TypedDict):
    id: str
    kind: str
    center: tuple[float, float]
    vertices: tuple[tuple[float, float], ...]


def _rounded_point(point: _Vec | tuple[float, float]) -> tuple[float, float]:
    x_value, y_value = point if isinstance(point, tuple) else (point.x, point.y)
    return (
        round(float(x_value), COORDINATE_PRECISION),
        round(float(y_value), COORDINATE_PRECISION),
    )


def _canonical_edge(
    point_a: tuple[float, float],
    point_b: tuple[float, float],
) -> tuple[tuple[float, float], tuple[float, float]]:
    return (point_a, point_b) if point_a <= point_b else (point_b, point_a)


def _compatibility_extent(values: list[float]) -> int:
    if not values:
        return 1
    return max(1, int(math.ceil(max(values) - min(values))))


def _polygon_centroid(vertices: Iterable[_Vec]) -> _Vec:
    points = list(vertices)
    if not points:
        return _Vec(0.0, 0.0)
    area_twice = 0.0
    centroid_x = 0.0
    centroid_y = 0.0
    for index, point in enumerate(points):
        next_point = points[(index + 1) % len(points)]
        cross = (point.x * next_point.y) - (next_point.x * point.y)
        area_twice += cross
        centroid_x += (point.x + next_point.x) * cross
        centroid_y += (point.y + next_point.y) * cross
    if math.isclose(area_twice, 0.0):
        return _Vec(
            sum(point.x for point in points) / len(points),
            sum(point.y for point in points) / len(points),
        )
    scale = 1 / (3 * area_twice)
    return _Vec(centroid_x * scale, centroid_y * scale)


def _encode_float(value: float) -> str:
    scaled = int(round(value * 1_000_000))
    if scaled < 0:
        return f"n{abs(scaled)}"
    if scaled > 0:
        return f"p{scaled}"
    return "0"


def _affine_multiply(left: _Affine, right: _Affine) -> _Affine:
    return (
        (left[0] * right[0]) + (left[1] * right[3]),
        (left[0] * right[1]) + (left[1] * right[4]),
        (left[0] * right[2]) + (left[1] * right[5]) + left[2],
        (left[3] * right[0]) + (left[4] * right[3]),
        (left[3] * right[1]) + (left[4] * right[4]),
        (left[3] * right[2]) + (left[4] * right[5]) + left[5],
    )


def _affine_apply(transform: _Affine, point: _Vec) -> _Vec:
    return _Vec(
        (transform[0] * point.x) + (transform[1] * point.y) + transform[2],
        (transform[3] * point.x) + (transform[4] * point.y) + transform[5],
    )


def _translation(tx: float, ty: float) -> _Affine:
    return (1.0, 0.0, float(tx), 0.0, 1.0, float(ty))


def _translation_to(source: _Vec, target: _Vec) -> _Affine:
    return _translation(target.x - source.x, target.y - source.y)


def _rotation(radians: float) -> _Affine:
    cosine = math.cos(radians)
    sine = math.sin(radians)
    return (cosine, -sine, 0.0, sine, cosine, 0.0)


def _id_from_anchor(prefix: str, anchor: _Vec, orientation: int) -> str:
    return f"{prefix}:{orientation % 360}:{_encode_float(anchor.x)}:{_encode_float(anchor.y)}"


def _id_from_transform(prefix: str, transform: _Affine) -> str:
    return prefix + ":" + ":".join(_encode_float(value) for value in transform)


def _logical_indexes(points: list[tuple[float, float]]) -> dict[tuple[float, float], tuple[int, int]]:
    unique_x = {value: index for index, value in enumerate(sorted({point[0] for point in points}))}
    unique_y = {value: index for index, value in enumerate(sorted({point[1] for point in points}))}
    return {
        point: (unique_x[point[0]], unique_y[point[1]])
        for point in points
    }


def _build_edge_neighbors(records: list[_PatchRecord]) -> dict[str, tuple[str, ...]]:
    edge_map: dict[tuple[tuple[float, float], tuple[float, float]], list[str]] = defaultdict(list)
    for record in records:
        cell_id = record["id"]
        vertices = record["vertices"]
        for index, left in enumerate(vertices):
            right = vertices[(index + 1) % len(vertices)]
            edge_map[_canonical_edge(left, right)].append(cell_id)
    neighbor_sets: dict[str, set[str]] = {record["id"]: set() for record in records}
    for owners in edge_map.values():
        unique_owners = tuple(sorted(set(owners)))
        if len(unique_owners) != 2:
            continue
        neighbor_left, neighbor_right = unique_owners
        neighbor_sets[neighbor_left].add(neighbor_right)
        neighbor_sets[neighbor_right].add(neighbor_left)
    return {
        cell_id: tuple(sorted(neighbors))
        for cell_id, neighbors in neighbor_sets.items()
    }


def _patch_from_records(patch_depth: int, records: list[_PatchRecord]) -> AperiodicPatch:
    neighbors_by_id = _build_edge_neighbors(records)
    cells = tuple(
        AperiodicPatchCell(
            id=record["id"],
            kind=record["kind"],
            center=record["center"],
            vertices=record["vertices"],
            neighbors=neighbors_by_id[record["id"]],
        )
        for record in sorted(records, key=lambda item: item["id"])
    )
    all_x = [vertex[0] for cell in cells for vertex in cell.vertices]
    all_y = [vertex[1] for cell in cells for vertex in cell.vertices]
    return AperiodicPatch(
        patch_depth=int(patch_depth),
        width=_compatibility_extent(all_x),
        height=_compatibility_extent(all_y),
        cells=cells,
    )


def _logo_forward(point: _Vec, heading_degrees: float, distance: float) -> _Vec:
    radians = math.radians(heading_degrees)
    return _Vec(
        point.x + (distance * math.sin(radians)),
        point.y + (distance * math.cos(radians)),
    )


def _kite_vertices(anchor: _Vec, heading: float, length: float) -> tuple[_Vec, ...]:
    short_length = length / PHI
    vertices = [anchor]
    current = anchor
    current_heading = heading - 36
    current = _logo_forward(current, current_heading, length)
    vertices.append(current)
    current_heading += 108
    current = _logo_forward(current, current_heading, short_length)
    vertices.append(current)
    current_heading += 36
    current = _logo_forward(current, current_heading, short_length)
    vertices.append(current)
    return tuple(vertices)


def _dart_vertices(anchor: _Vec, heading: float, length: float) -> tuple[_Vec, ...]:
    short_length = length / PHI
    vertices = [anchor]
    current = anchor
    current_heading = heading - 36
    current = _logo_forward(current, current_heading, length)
    vertices.append(current)
    current_heading += 144
    current = _logo_forward(current, current_heading, short_length)
    vertices.append(current)
    current_heading -= 36
    current = _logo_forward(current, current_heading, short_length)
    vertices.append(current)
    return tuple(vertices)


def _inflate_p2_kite(
    anchor: _Vec,
    heading: float,
    length: float,
    depth: int,
    tiles: list[_LeafTile],
) -> tuple[_Vec, float]:
    if depth == 0:
        vertices = _kite_vertices(anchor, heading, length)
        tiles.append(
            _LeafTile(
                kind="kite",
                vertices=vertices,
                center=_polygon_centroid(vertices),
                anchor=anchor,
                orientation=int(round(heading)),
            )
        )
        return anchor, heading

    short_length = length / PHI
    current_anchor = anchor
    current_heading = heading - 36
    current_anchor, current_heading = _inflate_p2_dart(current_anchor, current_heading, short_length, depth - 1, tiles)
    current_anchor = _logo_forward(current_anchor, current_heading, length)
    current_heading += 144
    current_anchor, current_heading = _inflate_p2_kite(current_anchor, current_heading, short_length, depth - 1, tiles)
    current_heading -= 18
    current_anchor = _logo_forward(current_anchor, current_heading, length * (2 * math.cos(3 * math.pi / 10)))
    current_heading += 162
    current_anchor, current_heading = _inflate_p2_kite(current_anchor, current_heading, short_length, depth - 1, tiles)
    current_heading -= 36
    current_anchor = _logo_forward(current_anchor, current_heading, length)
    current_heading += 180
    current_anchor, current_heading = _inflate_p2_dart(current_anchor, current_heading, short_length, depth - 1, tiles)
    current_heading -= 36
    return current_anchor, current_heading


def _inflate_p2_dart(
    anchor: _Vec,
    heading: float,
    length: float,
    depth: int,
    tiles: list[_LeafTile],
) -> tuple[_Vec, float]:
    if depth == 0:
        vertices = _dart_vertices(anchor, heading, length)
        tiles.append(
            _LeafTile(
                kind="dart",
                vertices=vertices,
                center=_polygon_centroid(vertices),
                anchor=anchor,
                orientation=int(round(heading)),
            )
        )
        return anchor, heading

    short_length = length / PHI
    current_anchor = anchor
    current_heading = heading
    current_anchor, current_heading = _inflate_p2_kite(current_anchor, current_heading, short_length, depth - 1, tiles)
    current_heading -= 36
    current_anchor = _logo_forward(current_anchor, current_heading, length)
    current_heading += 180
    current_anchor, current_heading = _inflate_p2_dart(current_anchor, current_heading, short_length, depth - 1, tiles)
    current_heading -= 54
    current_anchor = _logo_forward(current_anchor, current_heading, length * (2 * math.cos(3 * math.pi / 10)))
    current_heading += 126
    current_anchor, current_heading = _inflate_p2_dart(current_anchor, current_heading, short_length, depth - 1, tiles)
    current_anchor = _logo_forward(current_anchor, current_heading, length)
    current_heading += 144
    return current_anchor, current_heading


def _build_penrose_p2_patch(patch_depth: int) -> AperiodicPatch:
    root_length = PHI ** int(patch_depth)
    tiles: list[_LeafTile] = []
    anchor = _Vec(0.0, 0.0)
    heading = 0.0
    for _ in range(5):
        anchor, heading = _inflate_p2_kite(anchor, heading, root_length, int(patch_depth), tiles)
        heading -= 72

    records: list[_PatchRecord] = []
    for tile in tiles:
        rounded_vertices = tuple(_rounded_point(vertex) for vertex in tile.vertices)
        center = _rounded_point(tile.center)
        records.append(
            {
                "id": _id_from_anchor("p2k" if tile.kind == "kite" else "p2d", tile.anchor, tile.orientation),
                "kind": tile.kind,
                "center": center,
                "vertices": rounded_vertices,
            }
        )
    return _patch_from_records(patch_depth, records)


_AB_DIRECTIONS = tuple(
    _Vec(math.cos(index * math.pi / 4), math.sin(index * math.pi / 4))
    for index in range(8)
)
_AB_RHOMB_VERTICES = ((), (1,), (1, 1), (0, 1))
_AB_TRIANGLE_VERTICES = ((), (1,), (1, 0, 1))
_AB_SUBSTITUTIONS = {
    "rhomb": (
        ("rhomb", (), 0),
        ("rhomb", (1, 1, 1, -1), 0),
        ("rhomb", (1, 1, 1), 6),
        ("RSquare", (1, 1, 0, -1), 3),
        ("RSquare", (1, 1, 1), 7),
        ("LSquare", (0, 1), 0),
        ("LSquare", (2, 1, 1, -1), 4),
    ),
    "RSquare": (
        ("rhomb", (0,), 0),
        ("rhomb", (1, 1, 0, -1), 2),
        ("LSquare", (0, 1), 0),
        ("RSquare", (1, 1, 0, -1), 3),
        ("RSquare", (1, 2, 1), 5),
    ),
    "LSquare": (
        ("rhomb", (0, 1), 7),
        ("rhomb", (1, 1), 1),
        ("LSquare", (0, 1, 0, -1), 3),
        ("RSquare", (0, 1), 0),
        ("LSquare", (1, 2), 5),
    ),
}


def _ab_vector(coefficients: tuple[int, ...], orientation: int, length: float) -> _Vec:
    point = _Vec(0.0, 0.0)
    for index, coefficient in enumerate(coefficients):
        if coefficient == 0:
            continue
        direction = _AB_DIRECTIONS[(orientation + index) % 8]
        point = point + (direction * (coefficient * length))
    return point


def _ab_vertices(name: str, anchor: _Vec, orientation: int, length: float) -> tuple[_Vec, ...]:
    base_shape = _AB_RHOMB_VERTICES if name == "rhomb" else _AB_TRIANGLE_VERTICES
    return tuple(anchor + _ab_vector(tuple(vertex), orientation, length) for vertex in base_shape)


def _inflate_ammann_tile(
    name: str,
    anchor: _Vec,
    orientation: int,
    length: float,
    depth: int,
    leaves: list[tuple[str, tuple[_Vec, ...], _Vec, int]],
) -> None:
    if depth == 0:
        vertices = _ab_vertices(name, anchor, orientation, length)
        leaves.append((name, vertices, anchor, orientation))
        return

    child_length = length / SILVER_RATIO
    for child_name, origin, child_orientation in _AB_SUBSTITUTIONS[name]:
        child_anchor = anchor + _ab_vector(tuple(origin), orientation, child_length)
        _inflate_ammann_tile(
            child_name,
            child_anchor,
            (orientation + child_orientation) % 8,
            child_length,
            depth - 1,
            leaves,
        )


def _merge_ammann_triangles(
    leaves: list[tuple[str, tuple[_Vec, ...], _Vec, int]]
) -> list[_PatchRecord]:
    records: list[_PatchRecord] = []
    triangle_pairs: dict[tuple[tuple[float, float], tuple[float, float]], list[tuple[str, tuple[_Vec, ...], _Vec, int]]] = defaultdict(list)
    for name, vertices, anchor, orientation in leaves:
        if name == "rhomb":
            rounded_vertices = tuple(_rounded_point(vertex) for vertex in vertices)
            center = _rounded_point(_polygon_centroid(vertices))
            records.append(
                {
                    "id": _id_from_anchor("abr", anchor, orientation * 45),
                    "kind": "rhomb",
                    "center": center,
                    "vertices": rounded_vertices,
                }
            )
            continue
        hypotenuse = _canonical_edge(_rounded_point(vertices[0]), _rounded_point(vertices[2]))
        triangle_pairs[hypotenuse].append((name, vertices, anchor, orientation))

    for edge_key, pair in triangle_pairs.items():
        if len(pair) != 2:
            continue
        unique_vertices = {
            _rounded_point(vertex)
            for _, vertices, _, _ in pair
            for vertex in vertices
        }
        polygon_vertices = sorted(
            unique_vertices,
            key=lambda point: math.atan2(
                point[1] - sum(vertex[1] for vertex in unique_vertices) / len(unique_vertices),
                point[0] - sum(vertex[0] for vertex in unique_vertices) / len(unique_vertices),
            ),
        )
        rounded_vertices = tuple(polygon_vertices)
        center = _rounded_point(
            _polygon_centroid(tuple(_Vec(x_value, y_value) for x_value, y_value in rounded_vertices))
        )
        records.append(
            {
                "id": f"abs:{edge_key[0][0]}:{edge_key[0][1]}:{edge_key[1][0]}:{edge_key[1][1]}",
                "kind": "square",
                "center": center,
                "vertices": rounded_vertices,
            }
        )
    return records


def _build_ammann_beenker_patch(patch_depth: int) -> AperiodicPatch:
    root_length = SILVER_RATIO ** int(patch_depth)
    leaves: list[tuple[str, tuple[_Vec, ...], _Vec, int]] = []
    for orientation in range(8):
        _inflate_ammann_tile("rhomb", _Vec(0.0, 0.0), orientation, root_length, int(patch_depth), leaves)
    patch = _patch_from_records(patch_depth, _merge_ammann_triangles(leaves))
    # The raw substitution emits eight seed-adjacent rhombs with no shared edges in the
    # final merged patch. They are isolated artifacts rather than valid boundary tiles.
    if any(not cell.neighbors for cell in patch.cells):
        return AperiodicPatch(
            patch_depth=patch.patch_depth,
            width=patch.width,
            height=patch.height,
            cells=tuple(cell for cell in patch.cells if cell.neighbors),
        )
    return patch


_SPECTRE_LABELS = (
    "Gamma",
    "Delta",
    "Theta",
    "Lambda",
    "Xi",
    "Pi",
    "Sigma",
    "Phi",
    "Psi",
)
_SPECTRE_ROOT_LABEL = "Delta"
_SPECTRE_BASE_VERTICES = (
    _Vec(0.0, 0.0),
    _Vec(1.0, 0.0),
    _Vec(1.5, -0.8660254037844386),
    _Vec(2.366025403784439, -0.36602540378443865),
    _Vec(2.366025403784439, 0.6339745962155614),
    _Vec(3.366025403784439, 0.6339745962155614),
    _Vec(3.866025403784439, 1.5),
    _Vec(3.0, 2.0),
    _Vec(2.133974596215561, 1.5),
    _Vec(1.6339745962155614, 2.3660254037844393),
    _Vec(0.6339745962155614, 2.3660254037844393),
    _Vec(-0.3660254037844386, 2.3660254037844393),
    _Vec(-0.866025403784439, 1.5),
    _Vec(0.0, 1.0),
)
_SPECTRE_BASE_QUAD = (
    _SPECTRE_BASE_VERTICES[3],
    _SPECTRE_BASE_VERTICES[5],
    _SPECTRE_BASE_VERTICES[7],
    _SPECTRE_BASE_VERTICES[11],
)
_SPECTRE_GAMMA_SECONDARY_TRANSFORM = _affine_multiply(
    _translation(_SPECTRE_BASE_VERTICES[8].x, _SPECTRE_BASE_VERTICES[8].y),
    _rotation(math.pi / 6),
)
_SPECTRE_SUBSTITUTION_RULES: dict[str, tuple[str | None, ...]] = {
    "Gamma": ("Pi", "Delta", None, "Theta", "Sigma", "Xi", "Phi", "Gamma"),
    "Delta": ("Xi", "Delta", "Xi", "Phi", "Sigma", "Pi", "Phi", "Gamma"),
    "Theta": ("Psi", "Delta", "Pi", "Phi", "Sigma", "Pi", "Phi", "Gamma"),
    "Lambda": ("Psi", "Delta", "Xi", "Phi", "Sigma", "Pi", "Phi", "Gamma"),
    "Xi": ("Psi", "Delta", "Pi", "Phi", "Sigma", "Psi", "Phi", "Gamma"),
    "Pi": ("Psi", "Delta", "Xi", "Phi", "Sigma", "Psi", "Phi", "Gamma"),
    "Sigma": ("Xi", "Delta", "Xi", "Phi", "Sigma", "Pi", "Lambda", "Gamma"),
    "Phi": ("Psi", "Delta", "Psi", "Phi", "Sigma", "Pi", "Phi", "Gamma"),
    "Psi": ("Psi", "Delta", "Psi", "Phi", "Sigma", "Psi", "Phi", "Gamma"),
}


def _build_spectre_supertile_child_transforms(quad: tuple[_Vec, _Vec, _Vec, _Vec]) -> tuple[_Affine, ...]:
    transition_rules = (
        (60, 3, 1),
        (0, 2, 0),
        (60, 3, 1),
        (60, 3, 1),
        (0, 2, 0),
        (60, 3, 1),
        (-120, 3, 3),
    )
    transforms: list[_Affine] = [_AFFINE_IDENTITY]
    total_angle = 0.0
    rotation_transform = _AFFINE_IDENTITY
    transformed_quad = list(quad)
    for angle, from_index, to_index in transition_rules:
        total_angle += angle
        if angle != 0:
            rotation_transform = _rotation(math.radians(total_angle))
            transformed_quad = [
                _affine_apply(rotation_transform, point)
                for point in quad
            ]
        translation_transform = _translation_to(
            transformed_quad[to_index],
            _affine_apply(transforms[-1], quad[from_index]),
        )
        transforms.append(_affine_multiply(translation_transform, rotation_transform))
    return tuple(
        _affine_multiply(_AFFINE_REFLECT_X, transform)
        for transform in transforms
    )


_SPECTRE_BASE_TEMPLATES = {
    label: _SpectreTemplate(
        quad=_SPECTRE_BASE_QUAD,
        children=(
            (label, _AFFINE_IDENTITY),
            (label, _SPECTRE_GAMMA_SECONDARY_TRANSFORM),
        )
        if label == "Gamma"
        else ((label, _AFFINE_IDENTITY),),
    )
    for label in _SPECTRE_LABELS
}


def _spectre_supertile_quad(
    quad: tuple[_Vec, _Vec, _Vec, _Vec],
    child_transforms: tuple[_Affine, ...],
) -> tuple[_Vec, _Vec, _Vec, _Vec]:
    return (
        _affine_apply(child_transforms[6], quad[2]),
        _affine_apply(child_transforms[5], quad[1]),
        _affine_apply(child_transforms[3], quad[2]),
        _affine_apply(child_transforms[0], quad[1]),
    )


@lru_cache(maxsize=None)
def _spectre_template_for_depth(label: str, depth: int) -> _SpectreTemplate:
    if depth <= 0:
        return _SPECTRE_BASE_TEMPLATES[label]

    prior_delta = _spectre_template_for_depth(_SPECTRE_ROOT_LABEL, depth - 1)
    child_transforms = _build_spectre_supertile_child_transforms(prior_delta.quad)
    return _SpectreTemplate(
        quad=_spectre_supertile_quad(prior_delta.quad, child_transforms),
        children=tuple(
            (child_label, child_transforms[index])
            for index, child_label in enumerate(_SPECTRE_SUBSTITUTION_RULES[label])
            if child_label is not None
        ),
    )


def _collect_spectre_leaf_transforms(
    label: str,
    depth: int,
    transform: _Affine,
    leaves: list[_Affine],
) -> None:
    template = _spectre_template_for_depth(label, depth)
    if depth <= 0:
        for _, child_transform in template.children:
            leaves.append(_affine_multiply(transform, child_transform))
        return

    for child_label, child_transform in template.children:
        _collect_spectre_leaf_transforms(
            child_label,
            depth - 1,
            _affine_multiply(transform, child_transform),
            leaves,
        )


def _build_spectre_patch(patch_depth: int) -> AperiodicPatch:
    leaf_transforms: list[_Affine] = []
    _collect_spectre_leaf_transforms(
        _SPECTRE_ROOT_LABEL,
        int(patch_depth),
        _AFFINE_IDENTITY,
        leaf_transforms,
    )

    records: list[_PatchRecord] = []
    for transform in leaf_transforms:
        vertices = tuple(_affine_apply(transform, vertex) for vertex in _SPECTRE_BASE_VERTICES)
        records.append(
            {
                "id": _id_from_transform("spectre", transform),
                "kind": "spectre",
                "center": _rounded_point(_polygon_centroid(vertices)),
                "vertices": tuple(_rounded_point(vertex) for vertex in vertices),
            }
        )
    return _patch_from_records(patch_depth, records)


def build_aperiodic_patch(geometry: str, patch_depth: int) -> AperiodicPatch:
    if geometry in {PENROSE_GEOMETRY, PENROSE_VERTEX_GEOMETRY}:
        penrose_patch = build_penrose_patch(
            patch_depth,
            adjacency_mode=(
                PENROSE_VERTEX_ADJACENCY if geometry == PENROSE_VERTEX_GEOMETRY else PENROSE_EDGE_ADJACENCY
            ),
        )
        return AperiodicPatch(
            patch_depth=penrose_patch.patch_depth,
            width=penrose_patch.width,
            height=penrose_patch.height,
            cells=tuple(
                AperiodicPatchCell(
                    id=cell.id,
                    kind=cell.kind,
                    center=cell.center,
                    vertices=cell.vertices,
                    neighbors=cell.neighbors,
                )
                for cell in penrose_patch.cells
            ),
        )
    if geometry == PENROSE_P2_GEOMETRY:
        return _build_penrose_p2_patch(patch_depth)
    if geometry == AMMANN_BEENKER_GEOMETRY:
        return _build_ammann_beenker_patch(patch_depth)
    if geometry == SPECTRE_GEOMETRY:
        return _build_spectre_patch(patch_depth)
    raise ValueError(f"Unsupported aperiodic geometry '{geometry}'.")
