from __future__ import annotations

import math
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from shapely.geometry import Polygon
from shapely.ops import unary_union


Point = tuple[float, float]


@dataclass(frozen=True)
class BoundaryLineFamily:
    axis_angle: int
    offsets: tuple[float, ...]
    segment_count: int


@dataclass(frozen=True)
class BoundaryLineEquation:
    axis_angle: int
    normal_x: float
    normal_y: float
    offset: float
    equation: str


@dataclass(frozen=True)
class TemplateRegionComponent:
    region_signature: tuple[int, ...]
    subset: tuple[int, ...]
    macro_kind: str | None
    side_count: int
    quantized_area_ratio: float
    marked_cell_signature: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class ResolvedTemplateOccurrence:
    occurrence: Any
    components: tuple[TemplateRegionComponent, ...]


def build_polygon_context(
    cells: Mapping[int, Any],
    *,
    preferred_kind_suffix: str | None = "square",
) -> tuple[dict[int, Polygon], float]:
    polygons = {
        index: Polygon(cell.vertices)
        for index, cell in cells.items()
    }
    primitive_area = polygons[min(cells)].area
    if preferred_kind_suffix is not None:
        for index, cell in cells.items():
            if cell.kind.endswith(preferred_kind_suffix):
                primitive_area = polygons[index].area
                break
    return polygons, primitive_area


def edge_angle(a: Point, b: Point) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360.0


def snap_angle(angle: float, *, increment: float = 30.0) -> int:
    return int(round(angle / increment) * increment) % 360


def rotate_vertices(
    vertices: tuple[Point, ...],
) -> tuple[Point, ...]:
    rotations: list[tuple[float, tuple[Point, ...]]] = []
    for offset in range(len(vertices)):
        rotated = vertices[offset:] + vertices[:offset]
        angle = edge_angle(rotated[0], rotated[1])
        rotations.append((round(angle, 6), tuple(rotated)))
    return min(rotations, key=lambda item: item[0])[1]


def compress_collinear_boundary(
    coordinates: list[Point],
    *,
    tolerance: float = 1e-6,
) -> tuple[Point, ...]:
    points = list(coordinates[:-1])
    changed = True
    while changed and len(points) >= 3:
        changed = False
        reduced: list[Point] = []
        for index, point in enumerate(points):
            left = points[(index - 1) % len(points)]
            right = points[(index + 1) % len(points)]
            left_vector = (point[0] - left[0], point[1] - left[1])
            right_vector = (right[0] - point[0], right[1] - point[1])
            cross = (
                left_vector[0] * right_vector[1]
                - left_vector[1] * right_vector[0]
            )
            if abs(cross) <= tolerance:
                changed = True
                continue
            reduced.append((round(point[0], 6), round(point[1], 6)))
        points = reduced
    return tuple(points)


def edge_lengths(vertices: tuple[Point, ...]) -> tuple[float, ...]:
    lengths: list[float] = []
    for index, left in enumerate(vertices):
        right = vertices[(index + 1) % len(vertices)]
        lengths.append(math.dist(left, right))
    return tuple(lengths)


def interior_angles(vertices: tuple[Point, ...]) -> tuple[float, ...]:
    angles: list[float] = []
    for index, point in enumerate(vertices):
        left = vertices[(index - 1) % len(vertices)]
        right = vertices[(index + 1) % len(vertices)]
        incoming = (left[0] - point[0], left[1] - point[1])
        outgoing = (right[0] - point[0], right[1] - point[1])
        incoming_length = math.hypot(*incoming)
        outgoing_length = math.hypot(*outgoing)
        if incoming_length == 0 or outgoing_length == 0:
            angles.append(0.0)
            continue
        dot = incoming[0] * outgoing[0] + incoming[1] * outgoing[1]
        cosine = max(-1.0, min(1.0, dot / (incoming_length * outgoing_length)))
        angles.append(math.degrees(math.acos(cosine)))
    return tuple(angles)


def classify_macro_kind(
    side_count: int,
    edge_lengths_value: tuple[float, ...],
    interior_angles_value: tuple[float, ...],
) -> str | None:
    if not edge_lengths_value or min(edge_lengths_value) <= 1e-9:
        return None
    edge_ratio = max(edge_lengths_value) / min(edge_lengths_value)
    if side_count == 3 and edge_ratio <= 1.35:
        if max(abs(angle - 60.0) for angle in interior_angles_value) <= 30.0:
            return "triangle"
    if side_count == 4 and edge_ratio <= 1.35:
        if max(abs(angle - 90.0) for angle in interior_angles_value) <= 30.0:
            return "square"
    return None


def compactness(area: float, perimeter: float) -> float:
    if perimeter <= 1e-9:
        return 0.0
    return (4.0 * math.pi * area) / (perimeter * perimeter)


def merged_boundary(
    subset: frozenset[int] | tuple[int, ...],
    polygons: Mapping[int, Polygon],
) -> tuple[Polygon, tuple[Point, ...]] | None:
    merged = unary_union([polygons[index] for index in subset])
    if merged.geom_type != "Polygon":
        return None
    if len(merged.interiors) > 0:
        return None
    boundary = compress_collinear_boundary(list(merged.exterior.coords))
    if len(boundary) < 3:
        return None
    return merged, boundary


def evaluate_subset(
    subset: frozenset[int],
    polygons: Mapping[int, Polygon],
    *,
    primitive_area: float,
) -> tuple[tuple[Any, ...], dict[str, Any]] | None:
    merged_result = merged_boundary(subset, polygons)
    if merged_result is None:
        return None
    merged, boundary = merged_result

    edge_lengths_value = edge_lengths(boundary)
    interior_angles_value = interior_angles(boundary)
    side_count = len(boundary)
    convex_hull_area = merged.convex_hull.area
    convexity = merged.area / convex_hull_area if convex_hull_area > 1e-9 else 1.0
    area_ratio = merged.area / primitive_area
    compactness_value = compactness(merged.area, merged.length)
    macro_kind = classify_macro_kind(side_count, edge_lengths_value, interior_angles_value)

    shape_penalty = min(abs(side_count - 3), abs(side_count - 4))
    score = (
        -shape_penalty,
        round(convexity, 6),
        round(compactness_value, 6),
        round(area_ratio, 6),
    )

    edge_signature = tuple(
        sorted(
            round(length / sum(edge_lengths_value), 2)
            for length in edge_lengths_value
        )
    )
    angle_signature = tuple(
        sorted(int(round(angle / 5.0) * 5) for angle in interior_angles_value)
    )

    metrics = {
        "macro_kind": macro_kind,
        "side_count": side_count,
        "area_ratio": area_ratio,
        "compactness": compactness_value,
        "edge_length_signature": edge_signature,
        "angle_signature": angle_signature,
    }
    return score, metrics


def multi_source_ball(
    cells: Mapping[int, Any],
    sources: tuple[int, ...],
    radius: int,
) -> tuple[int, ...]:
    distances: dict[int, int] = {source: 0 for source in sources}
    queue: deque[int] = deque(sources)
    while queue:
        current = queue.popleft()
        if distances[current] == radius:
            continue
        for neighbor in cells[current].neighbors:
            if neighbor in distances:
                continue
            distances[neighbor] = distances[current] + 1
            queue.append(neighbor)
    return tuple(sorted(distances))


def shape_symmetry_transforms(
    macro_kind: str,
    x: float,
    y: float,
) -> tuple[Point, ...]:
    transforms: set[Point] = set()
    if macro_kind == "square":
        rotation_steps = 4
        angle_increment = 90.0
    else:
        rotation_steps = 3
        angle_increment = 120.0

    for step in range(rotation_steps):
        angle = math.radians(step * angle_increment)
        rotated_x = x * math.cos(angle) - y * math.sin(angle)
        rotated_y = x * math.sin(angle) + y * math.cos(angle)
        for reflection in (1.0, -1.0):
            transforms.add((
                round(reflection * rotated_x, 2),
                round(rotated_y, 2),
            ))
    return tuple(sorted(transforms))


def canonical_slot_key(
    *,
    centroid: Point,
    orientation: int,
    scale: float,
    macro_kind: str,
    polygon: Polygon,
    cell_signature: str,
) -> tuple[float, float, str]:
    offset_x = polygon.centroid.x - centroid[0]
    offset_y = polygon.centroid.y - centroid[1]
    rotation = math.radians(-orientation)
    local_x = (
        offset_x * math.cos(rotation) - offset_y * math.sin(rotation)
    ) / scale
    local_y = (
        offset_x * math.sin(rotation) + offset_y * math.cos(rotation)
    ) / scale
    transforms = shape_symmetry_transforms(macro_kind, local_x, local_y)
    canonical_x, canonical_y = min(transforms)
    return (canonical_x, canonical_y, cell_signature)


def format_slot_key(slot_key: tuple[float, float, str]) -> str:
    return f"{slot_key[2]}@({slot_key[0]:.2f},{slot_key[1]:.2f})"


def subset_frame(
    subset: tuple[int, ...],
    polygons: Mapping[int, Polygon],
) -> tuple[Point, int, float] | None:
    merged_result = merged_boundary(subset, polygons)
    if merged_result is None:
        return None
    merged, boundary = merged_result
    rotated_boundary = rotate_vertices(boundary)
    orientation = snap_angle(edge_angle(rotated_boundary[0], rotated_boundary[1]))
    edge_lengths_value = edge_lengths(rotated_boundary)
    scale = sum(edge_lengths_value) / len(edge_lengths_value)
    if scale <= 1e-9:
        return None
    return ((merged.centroid.x, merged.centroid.y), orientation, scale)


def boundary_direction_histogram(
    boundary: tuple[Point, ...],
    *,
    orientation: int,
) -> tuple[tuple[int, int], ...]:
    histogram: Counter[int] = Counter()
    for index, point in enumerate(boundary):
        right = boundary[(index + 1) % len(boundary)]
        local_angle = (edge_angle(point, right) - orientation) % 360.0
        histogram[snap_angle(local_angle)] += 1
    return tuple(sorted(histogram.items()))


def normalized_boundary(
    boundary: tuple[Point, ...],
    *,
    centroid: Point,
    orientation: int,
    scale: float,
) -> tuple[Point, ...]:
    rotation = math.radians(-orientation)
    normalized_vertices: list[Point] = []
    for x_value, y_value in boundary:
        delta_x = x_value - centroid[0]
        delta_y = y_value - centroid[1]
        local_x = (
            delta_x * math.cos(rotation) - delta_y * math.sin(rotation)
        ) / scale
        local_y = (
            delta_x * math.sin(rotation) + delta_y * math.cos(rotation)
        ) / scale
        rounded_x = round(local_x, 2)
        rounded_y = round(local_y, 2)
        normalized_vertices.append((
            0.0 if abs(rounded_x) == 0.0 else rounded_x,
            0.0 if abs(rounded_y) == 0.0 else rounded_y,
        ))
    return tuple(normalized_vertices)


def normalize_point(
    point: Point,
    *,
    centroid: Point,
    orientation: int,
    scale: float,
) -> Point:
    rotation = math.radians(-orientation)
    delta_x = point[0] - centroid[0]
    delta_y = point[1] - centroid[1]
    local_x = (
        delta_x * math.cos(rotation) - delta_y * math.sin(rotation)
    ) / scale
    local_y = (
        delta_x * math.sin(rotation) + delta_y * math.cos(rotation)
    ) / scale
    rounded_x = round(local_x, 2)
    rounded_y = round(local_y, 2)
    return (
        0.0 if abs(rounded_x) == 0.0 else rounded_x,
        0.0 if abs(rounded_y) == 0.0 else rounded_y,
    )


def transform_normalized_point(
    point: Point,
    *,
    macro_kind: str,
    rotation_step: int,
    reflection: bool,
) -> Point:
    angle_increment = 90.0 if macro_kind == "square" else 120.0
    angle = math.radians(rotation_step * angle_increment)
    rotated_x = point[0] * math.cos(angle) - point[1] * math.sin(angle)
    rotated_y = point[0] * math.sin(angle) + point[1] * math.cos(angle)
    if reflection:
        rotated_x = -rotated_x
    rounded_x = round(rotated_x, 2)
    rounded_y = round(rotated_y, 2)
    return (
        0.0 if abs(rounded_x) == 0.0 else rounded_x,
        0.0 if abs(rounded_y) == 0.0 else rounded_y,
    )


def canonical_cycle(
    points: tuple[Point, ...],
) -> tuple[Point, ...]:
    rotations = [
        tuple(points[offset:] + points[:offset])
        for offset in range(len(points))
    ]
    reversed_points = tuple(reversed(points))
    rotations.extend(
        tuple(reversed_points[offset:] + reversed_points[:offset])
        for offset in range(len(reversed_points))
    )
    return min(rotations)


def canonicalize_boundary_template(
    boundary: tuple[Point, ...],
    *,
    centroid: Point,
    orientation: int,
    scale: float,
    macro_kind: str,
) -> tuple[Point, ...]:
    normalized_vertices = normalized_boundary(
        boundary,
        centroid=centroid,
        orientation=orientation,
        scale=scale,
    )
    rotation_steps = 4 if macro_kind == "square" else 3
    candidates: list[tuple[Point, ...]] = []
    for step in range(rotation_steps):
        for reflection in (False, True):
            transformed = tuple(
                transform_normalized_point(
                    point,
                    macro_kind=macro_kind,
                    rotation_step=step,
                    reflection=reflection,
                )
                for point in normalized_vertices
            )
            candidates.append(canonical_cycle(transformed))
    return min(candidates)


def line_families_from_canonical_vertices(
    canonical_vertices: tuple[Point, ...],
) -> tuple[BoundaryLineFamily, ...]:
    offsets_by_axis: dict[int, list[float]] = defaultdict(list)
    counts_by_axis: Counter[int] = Counter()
    for index, point in enumerate(canonical_vertices):
        right = canonical_vertices[(index + 1) % len(canonical_vertices)]
        direction = snap_angle(edge_angle(point, right))
        axis_angle = (direction + 90) % 180
        theta = math.radians(axis_angle)
        offset = round(point[0] * math.cos(theta) + point[1] * math.sin(theta), 2)
        offsets_by_axis[axis_angle].append(offset)
        counts_by_axis[axis_angle] += 1
    return tuple(
        BoundaryLineFamily(
            axis_angle=axis_angle,
            offsets=tuple(sorted(set(offsets_by_axis[axis_angle]))),
            segment_count=int(counts_by_axis[axis_angle]),
        )
        for axis_angle in sorted(offsets_by_axis)
    )


def line_equations_from_line_families(
    line_families: tuple[BoundaryLineFamily, ...],
) -> tuple[BoundaryLineEquation, ...]:
    equations: list[BoundaryLineEquation] = []
    for family in line_families:
        theta = math.radians(family.axis_angle)
        normal_x = round(math.cos(theta), 3)
        normal_y = round(math.sin(theta), 3)
        for offset in family.offsets:
            equations.append(
                BoundaryLineEquation(
                    axis_angle=family.axis_angle,
                    normal_x=normal_x,
                    normal_y=normal_y,
                    offset=offset,
                    equation=f"{normal_x}*x + {normal_y}*y = {offset}",
                )
            )
    return tuple(equations)


def resolve_template_occurrences(
    cells: Mapping[int, Any],
    polygons: Mapping[int, Polygon],
    *,
    primitive_area: float,
    line_families: tuple[BoundaryLineFamily, ...],
    matched_occurrences: tuple[Any, ...],
    describe_cell: Callable[[Any], str],
) -> tuple[ResolvedTemplateOccurrence, ...]:
    resolved_occurrences: list[ResolvedTemplateOccurrence] = []
    for occurrence in matched_occurrences:
        frame = subset_frame(occurrence.grown_subset, polygons)
        if frame is None:
            continue
        centroid, orientation, scale = frame
        region_members: dict[tuple[int, ...], list[int]] = defaultdict(list)
        for cell_index in occurrence.grown_subset:
            polygon = polygons[cell_index]
            point = normalize_point(
                (polygon.centroid.x, polygon.centroid.y),
                centroid=centroid,
                orientation=orientation,
                scale=scale,
            )
            region_signature_values: list[int] = []
            for family in line_families:
                theta = math.radians(family.axis_angle)
                value = point[0] * math.cos(theta) + point[1] * math.sin(theta)
                interval_index = 0
                while interval_index < len(family.offsets) and value > family.offsets[interval_index]:
                    interval_index += 1
                region_signature_values.append(interval_index)
            region_members[tuple(region_signature_values)].append(cell_index)

        components: list[TemplateRegionComponent] = []
        for region_signature, members in region_members.items():
            remaining = set(members)
            while remaining:
                root_index = remaining.pop()
                queue: deque[int] = deque((root_index,))
                component = {root_index}
                while queue:
                    current = queue.popleft()
                    for neighbor in cells[current].neighbors:
                        if neighbor in remaining:
                            remaining.remove(neighbor)
                            component.add(neighbor)
                            queue.append(neighbor)
                component_subset = tuple(sorted(component))
                evaluated = evaluate_subset(
                    frozenset(component_subset),
                    polygons,
                    primitive_area=primitive_area,
                )
                if evaluated is None:
                    continue
                _, metrics = evaluated
                marked_signature = tuple(sorted(
                    Counter(
                        describe_cell(cells[index])
                        for index in component_subset
                    ).items()
                ))
                components.append(
                    TemplateRegionComponent(
                        region_signature=region_signature,
                        subset=component_subset,
                        macro_kind=metrics["macro_kind"],
                        side_count=int(metrics["side_count"]),
                        quantized_area_ratio=round(float(metrics["area_ratio"]), 2),
                        marked_cell_signature=marked_signature,
                    )
                )
        resolved_occurrences.append(
            ResolvedTemplateOccurrence(
                occurrence=occurrence,
                components=tuple(sorted(
                    components,
                    key=lambda component: (
                        component.region_signature,
                        len(component.subset),
                        component.subset,
                    ),
                )),
            )
        )
    return tuple(resolved_occurrences)


__all__ = [
    "BoundaryLineEquation",
    "BoundaryLineFamily",
    "ResolvedTemplateOccurrence",
    "TemplateRegionComponent",
    "boundary_direction_histogram",
    "build_polygon_context",
    "canonical_slot_key",
    "canonicalize_boundary_template",
    "edge_angle",
    "evaluate_subset",
    "format_slot_key",
    "line_equations_from_line_families",
    "line_families_from_canonical_vertices",
    "merged_boundary",
    "multi_source_ball",
    "normalize_point",
    "resolve_template_occurrences",
    "rotate_vertices",
    "snap_angle",
    "subset_frame",
]
