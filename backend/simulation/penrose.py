from __future__ import annotations

import itertools
import math
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import Enum
from functools import cached_property

from backend.simulation.aperiodic_family_manifest import THICK_RHOMB_KIND, THIN_RHOMB_KIND

PHI = (1 + math.sqrt(5)) / 2
PENROSE_P3_OFFSETS = (0.2, 0.2, 0.2, 0.2, 0.2)
PENROSE_BASE_HALF_EXTENT = 0.85
PENROSE_COORDINATE_PRECISION = 6
PENROSE_SECTOR_OFFSET = math.pi / 5
PENROSE_EDGE_ADJACENCY = "edge"
PENROSE_VERTEX_ADJACENCY = "vertex"


@dataclass(frozen=True)
class PenrosePatchCell:
    id: str
    kind: str
    logical_x: int
    logical_y: int
    center: tuple[float, float]
    vertices: tuple[tuple[float, float], ...]
    neighbors: tuple[str, ...]


@dataclass(frozen=True)
class PenrosePatch:
    patch_depth: int
    width: int
    height: int
    cells: tuple[PenrosePatchCell, ...]


@dataclass(frozen=True)
class _ProvisionalPenroseCell:
    id: str
    kind: str
    center: tuple[float, float]
    vertices: tuple[tuple[float, float], ...]


class _RhombusType(Enum):
    THIN = THIN_RHOMB_KIND
    THICK = THICK_RHOMB_KIND


@dataclass(frozen=True)
class _Vector:
    x: float
    y: float

    def __add__(self, other: "_Vector") -> "_Vector":
        return _Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "_Vector") -> "_Vector":
        return _Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "_Vector":
        return _Vector(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: float) -> "_Vector":
        return _Vector(self.x / scalar, self.y / scalar)

    def dot(self, other: "_Vector") -> float:
        return (self.x * other.x) + (self.y * other.y)

    @cached_property
    def length(self) -> float:
        return math.hypot(self.x, self.y)


@dataclass(frozen=True)
class _Grid:
    origin: _Vector
    grid_size: _Vector

    def cell(self, x_multiple: int, y_multiple: int) -> "_GridCell":
        return _GridCell(self, x_multiple, y_multiple)


@dataclass(frozen=True)
class _GridCell:
    grid: _Grid
    x_multiple: int
    y_multiple: int

    @property
    def origin(self) -> _Vector:
        return self.grid.origin + _Vector(
            self.grid.grid_size.x * self.x_multiple,
            self.grid.grid_size.y * self.y_multiple,
        )

    @property
    def extent(self) -> _Vector:
        return self.origin + self.grid.grid_size

    def corners(self, margin: float = 0.0) -> tuple[_Vector, _Vector, _Vector, _Vector]:
        return (
            self.origin + _Vector(-margin, -margin),
            _Vector(self.origin.x - margin, self.extent.y + margin),
            self.extent + _Vector(margin, margin),
            _Vector(self.extent.x + margin, self.origin.y - margin),
        )


class _PentAngle:
    _SIN = tuple(math.sin(index * 2 * math.pi / 5) for index in range(5))
    _COS = tuple(math.cos(index * 2 * math.pi / 5) for index in range(5))
    _INVERSE_SIN = tuple(
        0 if index == 0 else 1 / math.sin(index * 2 * math.pi / 5) for index in range(5)
    )

    def __init__(self, index: int) -> None:
        self.index = int(index % 5)

    def sin(self, other: "_PentAngle" | None = None) -> float:
        if other is None:
            return self._SIN[self.index]
        return self._SIN[(other.index - self.index) % 5]

    def cos(self, other: "_PentAngle" | None = None) -> float:
        if other is None:
            return self._COS[self.index]
        return self._COS[(other.index - self.index) % 5]

    def inverse_sin(self, other: "_PentAngle") -> float:
        return self._INVERSE_SIN[(other.index - self.index) % 5]

    def unit(self) -> _Vector:
        return _Vector(self.sin(), self.cos())


PENT_ANGLES = tuple(_PentAngle(index) for index in range(5))


def _other_pent_angles(index: int) -> Iterator[_PentAngle]:
    for pent_angle in PENT_ANGLES:
        if pent_angle.index != index:
            yield pent_angle


def _det(x1: float, y1: float, x2: float, y2: float) -> float:
    return (x1 * y2) - (y1 * x2)


def _ccw(point_a: _Vector, point_b: _Vector, point_c: _Vector) -> int:
    value = ((point_b.x - point_a.x) * (point_c.y - point_a.y)) - (
        (point_c.x - point_a.x) * (point_b.y - point_a.y)
    )
    if math.isclose(value, 0.0):
        return 0
    return 1 if value > 0 else -1


def _intersection(
    point_a: _Vector, point_b: _Vector, point_c: _Vector, point_d: _Vector
) -> _Vector:
    denominator = _det(
        point_a.x - point_b.x,
        point_a.y - point_b.y,
        point_c.x - point_d.x,
        point_c.y - point_d.y,
    )
    x_numerator = _det(
        _det(point_a.x, point_a.y, point_b.x, point_b.y),
        point_a.x - point_b.x,
        _det(point_c.x, point_c.y, point_d.x, point_d.y),
        point_c.x - point_d.x,
    )
    y_numerator = _det(
        _det(point_a.x, point_a.y, point_b.x, point_b.y),
        point_a.y - point_b.y,
        _det(point_c.x, point_c.y, point_d.x, point_d.y),
        point_c.y - point_d.y,
    )
    return _Vector(x_numerator / denominator, y_numerator / denominator)


class _StripFamily:
    def __init__(self, tiling: "_PenroseTiling", offset: float, pent_angle: _PentAngle) -> None:
        self.tiling = tiling
        self.offset = offset
        self.pent_angle = pent_angle

    def direction(self) -> _Vector:
        return self.pent_angle.unit()

    def offset_direction(self) -> _Vector:
        direction = self.direction()
        return _Vector(direction.y, -direction.x)

    def strip(self, multiple: int) -> "_Strip":
        return _Strip(self, multiple)

    def strips_near_point(self, point: _Vector) -> Iterator[_Strip]:
        pentagrid_point = point / 2.5
        multiple = (pentagrid_point - self.strip(0).origin()).dot(self.offset_direction())
        ceiling = math.ceil(multiple)
        floor = math.floor(multiple)
        if abs(ceiling - multiple) <= 0.8:
            yield self.strip(ceiling)
        if abs(floor - multiple) <= 0.8 and floor != ceiling:
            yield self.strip(floor)


class _Strip:
    def __init__(self, family: _StripFamily, multiple: int) -> None:
        self.family = family
        self.multiple = int(multiple)

    def origin(self) -> _Vector:
        return self.family.offset_direction() * (self.family.offset + self.multiple)

    def two_points(self) -> tuple[_Vector, _Vector]:
        point = self.origin()
        return point, point + (self.family.direction() * 1000)

    def intersection(self, other: "_Strip") -> _Vector | None:
        if self.family.pent_angle.index == other.family.pent_angle.index:
            return None
        return _intersection(*self.two_points(), *other.two_points())

    def intersection_distance_from_point(self, other: "_Strip") -> float:
        intersection = self.intersection(other)
        if intersection is None:
            raise ValueError("Parallel strips do not intersect.")
        return (intersection - self.origin()).dot(self.family.direction())

    def rhombus_at_intersection(self, other: "_Strip") -> "_Rhombus":
        lattice_coords = [0] * 5
        lattice_coords[self.family.pent_angle.index] = self.multiple
        distance = self.intersection_distance_from_point(other)

        for pent_angle in _other_pent_angles(self.family.pent_angle.index):
            if pent_angle.index == other.family.pent_angle.index:
                lattice_coords[other.family.pent_angle.index] = other.multiple
                continue

            other_family = self.family.tiling.strip_family(pent_angle)
            initial_intersection = self.intersection_distance_from_point(other_family.strip(0))
            delta = initial_intersection - distance
            inverse_sin = self.family.pent_angle.inverse_sin(pent_angle)

            if inverse_sin > 0:
                multiple = int(math.floor(delta / inverse_sin))
                lattice_coords[pent_angle.index] = multiple
            else:
                multiple = int(math.ceil(delta / inverse_sin))
                lattice_coords[pent_angle.index] = multiple - 1

        return _Rhombus(self, other, tuple(lattice_coords))

    def rhombus(self, target_distance: float) -> "_Rhombus":
        forward_rhombus = next(self.rhombi(target_distance, True))
        backward_rhombus = next(self.rhombi(target_distance, False))
        candidates = [forward_rhombus, backward_rhombus]
        candidates.sort(
            key=lambda rhombus: abs(
                self.intersection_distance_from_point(rhombus.strip_b) - target_distance
            )
        )
        return candidates[0]

    def rhombi(self, distance: float, forward: bool) -> Iterator[_Rhombus]:
        intersection_tuples: list[tuple[_PentAngle, int, float]] = []
        lattice_coords = [0] * 5
        lattice_coords[self.family.pent_angle.index] = self.multiple

        for pent_angle in _other_pent_angles(self.family.pent_angle.index):
            other_family = self.family.tiling.strip_family(pent_angle)
            initial_intersection = self.intersection_distance_from_point(other_family.strip(0))
            delta = initial_intersection - distance
            inverse_sin = self.family.pent_angle.inverse_sin(pent_angle)

            if (forward and inverse_sin > 0) or (not forward and inverse_sin <= 0):
                multiple = int(math.floor(delta / inverse_sin))
                lattice_coords[pent_angle.index] = multiple
            else:
                multiple = int(math.ceil(delta / inverse_sin))
                lattice_coords[pent_angle.index] = multiple - 1

            intersection = initial_intersection - (inverse_sin * multiple)
            intersection_tuples.append((pent_angle, multiple, intersection))
            intersection_tuples.sort(key=lambda value: value[2], reverse=not forward)

        while True:
            closest = intersection_tuples.pop(0)
            inverse_sin = self.family.pent_angle.inverse_sin(closest[0])

            if (forward and inverse_sin < 0) or (not forward and inverse_sin > 0):
                lattice_coords[closest[0].index] += 1
                rhombus_coords = tuple(lattice_coords)
                next_tuple = (closest[0], closest[1] + 1, closest[2] - inverse_sin)
            else:
                rhombus_coords = tuple(lattice_coords)
                lattice_coords[closest[0].index] -= 1
                next_tuple = (closest[0], closest[1] - 1, closest[2] + inverse_sin)

            yield _Rhombus(
                self,
                self.family.tiling.strip_family(closest[0]).strip(closest[1]),
                rhombus_coords,
            )

            inserted = False
            for index in range(len(intersection_tuples) - 1, -1, -1):
                current = intersection_tuples[index]
                if (forward and next_tuple[2] > current[2]) or (
                    not forward and next_tuple[2] < current[2]
                ):
                    intersection_tuples.insert(index + 1, next_tuple)
                    inserted = True
                    break
            if not inserted:
                intersection_tuples.insert(0, next_tuple)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, _Strip)
            and self.family.pent_angle.index == other.family.pent_angle.index
            and self.multiple == other.multiple
        )

    def __hash__(self) -> int:
        return hash((self.family.pent_angle.index, self.multiple))


@dataclass(frozen=True)
class _RhombusVertex:
    coordinate: _Vector
    lattice_coordinate: tuple[int, ...]


class _Rhombus:
    _VERTEX_OFFSETS = (
        (0, 0),
        (0, -1),
        (-1, -1),
        (-1, 0),
    )

    def __init__(self, strip_a: _Strip, strip_b: _Strip, lattice_coords: tuple[int, ...]) -> None:
        self.strip_a = strip_a
        self.strip_b = strip_b
        self.lattice_coords = tuple(lattice_coords)

    def kind(self) -> _RhombusType:
        difference = abs(
            self.strip_a.family.pent_angle.index - self.strip_b.family.pent_angle.index
        )
        return _RhombusType.THICK if difference in {1, 4} else _RhombusType.THIN

    def vertices(self) -> list[_RhombusVertex]:
        vertices: list[_RhombusVertex] = []
        for offset_a, offset_b in self._VERTEX_OFFSETS:
            coords = list(self.lattice_coords)
            coords[self.strip_a.family.pent_angle.index] += offset_a
            coords[self.strip_b.family.pent_angle.index] += offset_b
            vertices.append(_RhombusVertex(self._cartesian_from_lattice(coords), tuple(coords)))

        if _ccw(vertices[0].coordinate, vertices[1].coordinate, vertices[2].coordinate) > 0:
            vertices.reverse()
        return vertices

    @cached_property
    def midpoint(self) -> _Vector:
        opposite_vertices: list[_Vector] = []
        for offset_a, offset_b in (self._VERTEX_OFFSETS[0], self._VERTEX_OFFSETS[2]):
            coords = list(self.lattice_coords)
            coords[self.strip_a.family.pent_angle.index] += offset_a
            coords[self.strip_b.family.pent_angle.index] += offset_b
            opposite_vertices.append(self._cartesian_from_lattice(coords))
        return _Vector(
            (opposite_vertices[0].x + opposite_vertices[1].x) / 2,
            (opposite_vertices[0].y + opposite_vertices[1].y) / 2,
        )

    def ordered_strips(self) -> tuple[_Strip, _Strip]:
        if self.strip_a.family.pent_angle.index < self.strip_b.family.pent_angle.index:
            return self.strip_a, self.strip_b
        return self.strip_b, self.strip_a

    @staticmethod
    def _cartesian_from_lattice(lattice_coords: list[int]) -> _Vector:
        x_coord = 0.0
        y_coord = 0.0
        for pent_angle in PENT_ANGLES:
            x_coord += lattice_coords[pent_angle.index] * pent_angle.cos()
            y_coord -= lattice_coords[pent_angle.index] * pent_angle.sin()
        return _Vector(x_coord, y_coord)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Rhombus) and self.ordered_strips() == other.ordered_strips()

    def __hash__(self) -> int:
        return hash(self.ordered_strips())


class _PenroseTiling:
    def __init__(self, offsets: tuple[float, ...] = PENROSE_P3_OFFSETS) -> None:
        self._families = tuple(
            _StripFamily(self, offsets[pent_angle.index], pent_angle) for pent_angle in PENT_ANGLES
        )

    def strip_family(self, pent_angle: _PentAngle) -> _StripFamily:
        return self._families[pent_angle.index]

    def rhombi_in_square(self, half_extent: float) -> Iterator[_Rhombus]:
        grid_cell = _Grid(
            origin=_Vector(-half_extent, -half_extent),
            grid_size=_Vector(half_extent * 2, half_extent * 2),
        ).cell(0, 0)

        def rhombus_in_cell(rhombus: _Rhombus) -> bool:
            midpoint = rhombus.midpoint
            return (
                grid_cell.origin.x <= midpoint.x < grid_cell.extent.x
                and grid_cell.origin.y <= midpoint.y < grid_cell.extent.y
            )

        grid_corners = list(grid_cell.corners(1.6))
        for pent_angle in _other_pent_angles(4):
            family = self.strip_family(pent_angle)

            min_multiple = math.inf
            max_multiple = -math.inf
            for corner in grid_corners:
                for strip in family.strips_near_point(corner):
                    min_multiple = min(min_multiple, strip.multiple)
                    max_multiple = max(max_multiple, strip.multiple)

            for multiple in range(int(min_multiple), int(max_multiple) + 1):
                strip = family.strip(multiple)
                intersection_distances: list[float] = []
                line_points = strip.two_points()

                for corner_a, corner_b in itertools.pairwise(grid_corners + [grid_corners[0]]):
                    if _ccw(*line_points, corner_a / 2.5) == _ccw(*line_points, corner_b / 2.5):
                        continue
                    intersection = _intersection(*line_points, corner_a / 2.5, corner_b / 2.5)
                    intersection_distances.append(
                        (intersection - strip.origin()).dot(strip.family.direction())
                    )

                if len(intersection_distances) != 2:
                    continue

                if intersection_distances[0] > intersection_distances[1]:
                    intersection_distances.reverse()

                start_rhombus = strip.rhombus(intersection_distances[0])
                stop_rhombus = strip.rhombus(intersection_distances[1])
                if start_rhombus == stop_rhombus:
                    if rhombus_in_cell(start_rhombus):
                        yield start_rhombus
                    continue

                for rhombus in strip.rhombi(intersection_distances[0], True):
                    if (
                        rhombus.strip_b.family.pent_angle.index > strip.family.pent_angle.index
                        and rhombus_in_cell(rhombus)
                    ):
                        yield rhombus
                    if rhombus == stop_rhombus:
                        break


def penrose_half_extent(patch_depth: int) -> float:
    return PENROSE_BASE_HALF_EXTENT * (PHI ** int(patch_depth))


def _rounded_point(vector: _Vector) -> tuple[float, float]:
    return (
        round(vector.x, PENROSE_COORDINATE_PRECISION),
        round(vector.y, PENROSE_COORDINATE_PRECISION),
    )


def _rounded_vertices(rhombus: _Rhombus) -> tuple[tuple[float, float], ...]:
    return tuple(_rounded_point(vertex.coordinate) for vertex in rhombus.vertices())


def _sector_index(center: tuple[float, float]) -> int:
    angle = math.atan2(center[1], center[0])
    normalized = (angle - PENROSE_SECTOR_OFFSET) % (2 * math.pi)
    return int(normalized / (2 * math.pi / 5)) % 5


def _encode_lattice_coords(lattice_coords: tuple[int, ...]) -> str:
    segments = []
    for value in lattice_coords:
        if value < 0:
            segments.append(f"n{abs(value)}")
        elif value > 0:
            segments.append(f"p{value}")
        else:
            segments.append("0")
    return "_".join(segments)


def _penrose_cell_id(
    kind: str,
    center: tuple[float, float],
    lattice_coords: tuple[int, ...],
    strip_indexes: tuple[int, int],
) -> str:
    prefix = "rt" if kind == _RhombusType.THICK.value else "rn"
    strip_key = f"{strip_indexes[0]}{strip_indexes[1]}"
    return f"{prefix}:{_sector_index(center)}:{strip_key}:{_encode_lattice_coords(lattice_coords)}"


def _canonical_edge(
    point_a: tuple[float, float], point_b: tuple[float, float]
) -> tuple[tuple[float, float], tuple[float, float]]:
    return (point_a, point_b) if point_a <= point_b else (point_b, point_a)


def _compatibility_extent(values: list[float]) -> int:
    if not values:
        return 1
    return max(1, int(math.ceil(max(values) - min(values))))


def _connect_owner_groups(
    owners_by_group: Iterable[Iterable[str]],
    neighbors_by_id: dict[str, set[str]],
    *,
    require_pair: bool,
) -> None:
    for owners in owners_by_group:
        unique_owners = tuple(sorted(set(owners)))
        if require_pair and len(unique_owners) != 2:
            continue
        if len(unique_owners) < 2:
            continue
        for index, left in enumerate(unique_owners):
            for right in unique_owners[index + 1 :]:
                neighbors_by_id[left].add(right)
                neighbors_by_id[right].add(left)


def build_penrose_patch(
    patch_depth: int,
    *,
    adjacency_mode: str = PENROSE_EDGE_ADJACENCY,
) -> PenrosePatch:
    if adjacency_mode not in {PENROSE_EDGE_ADJACENCY, PENROSE_VERTEX_ADJACENCY}:
        raise ValueError(f"Unsupported Penrose adjacency mode '{adjacency_mode}'.")

    tiling = _PenroseTiling()
    rhombi = list(tiling.rhombi_in_square(penrose_half_extent(patch_depth)))

    provisional: list[_ProvisionalPenroseCell] = []
    edge_map: dict[tuple[tuple[float, float], tuple[float, float]], list[str]] = {}
    vertex_map: dict[tuple[float, float], list[str]] = {}
    center_x_values: list[float] = []
    center_y_values: list[float] = []

    for rhombus in rhombi:
        kind = rhombus.kind().value
        center = _rounded_point(rhombus.midpoint)
        vertices = _rounded_vertices(rhombus)
        ordered_strips = rhombus.ordered_strips()
        cell_id = _penrose_cell_id(
            kind,
            center,
            rhombus.lattice_coords,
            (ordered_strips[0].family.pent_angle.index, ordered_strips[1].family.pent_angle.index),
        )
        provisional.append(
            _ProvisionalPenroseCell(
                id=cell_id,
                kind=kind,
                center=center,
                vertices=vertices,
            )
        )
        center_x_values.append(center[0])
        center_y_values.append(center[1])

        for index in range(len(vertices)):
            edge_key = _canonical_edge(vertices[index], vertices[(index + 1) % len(vertices)])
            edge_map.setdefault(edge_key, []).append(cell_id)
        for vertex in vertices:
            vertex_map.setdefault(vertex, []).append(cell_id)

    unique_x = {value: index for index, value in enumerate(sorted(set(center_x_values)))}
    unique_y = {value: index for index, value in enumerate(sorted(set(center_y_values)))}
    neighbors_by_id: dict[str, set[str]] = {record.id: set() for record in provisional}

    if adjacency_mode == PENROSE_VERTEX_ADJACENCY:
        _connect_owner_groups(vertex_map.values(), neighbors_by_id, require_pair=False)
    else:
        _connect_owner_groups(edge_map.values(), neighbors_by_id, require_pair=True)

    cells = tuple(
        PenrosePatchCell(
            id=record.id,
            kind=record.kind,
            logical_x=unique_x[record.center[0]],
            logical_y=unique_y[record.center[1]],
            center=record.center,
            vertices=record.vertices,
            neighbors=tuple(sorted(neighbors_by_id[record.id])),
        )
        for record in sorted(provisional, key=lambda item: item.id)
    )

    all_x = [vertex[0] for cell in cells for vertex in cell.vertices]
    all_y = [vertex[1] for cell in cells for vertex in cell.vertices]
    return PenrosePatch(
        patch_depth=int(patch_depth),
        width=_compatibility_extent(all_x),
        height=_compatibility_extent(all_y),
        cells=cells,
    )
