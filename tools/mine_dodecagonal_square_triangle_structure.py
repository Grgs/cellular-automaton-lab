from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

from shapely.geometry import Polygon
from shapely.ops import unary_union


ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_PATCH_PATH = (
    ROOT_DIR
    / "backend"
    / "simulation"
    / "data"
    / "dodecagonal_square_triangle_literature_source.json"
)


@dataclass(frozen=True)
class SourceCell:
    index: int
    kind: str
    chirality: str | None
    orientation_token: str
    vertices: tuple[tuple[float, float], ...]
    neighbors: tuple[int, ...]


@dataclass(frozen=True)
class NeighborhoodClassSummary:
    signature: str
    count: int
    kind_counts: tuple[tuple[str, int], ...]
    depth_histogram: tuple[tuple[int, int], ...]
    example_cells: tuple[int, ...]


@dataclass(frozen=True)
class MacroCandidateGroup:
    macro_kind: str
    side_count: int
    cell_count: int
    occurrence_count: int
    quantized_area_ratio: float
    edge_length_signature: tuple[float, ...]
    angle_signature: tuple[int, ...]
    root_signature_counts: tuple[tuple[str, int], ...]
    example_roots: tuple[int, ...]
    example_subsets: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class SeededSupertileGroup:
    seed_macro_kind: str
    seed_cell_count: int
    grown_macro_kind: str | None
    grown_cell_count: int
    occurrence_count: int
    side_count: int
    quantized_area_ratio: float
    selected_slot_count: int
    selected_slots: tuple[str, ...]
    boundary_direction_histogram: tuple[tuple[int, int], ...]
    marked_cell_signature: tuple[tuple[str, int], ...]
    edge_length_signature: tuple[float, ...]
    angle_signature: tuple[int, ...]
    example_roots: tuple[int, ...]
    example_subsets: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class InflationCandidateGroup:
    seed_macro_kind: str
    seed_cell_count: int
    base_cell_count: int
    grown_macro_kind: str | None
    grown_cell_count: int
    occurrence_count: int
    combo_size: int
    side_count: int
    quantized_area_ratio: float
    inflation_estimate: float
    selected_slots: tuple[str, ...]
    boundary_direction_histogram: tuple[tuple[int, int], ...]
    marked_cell_signature: tuple[tuple[str, int], ...]
    edge_length_signature: tuple[float, ...]
    angle_signature: tuple[int, ...]
    example_roots: tuple[int, ...]
    example_subsets: tuple[tuple[int, ...], ...]


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
class BoundaryTemplateGroup:
    seed_macro_kind: str
    base_cell_count: int
    candidate_cell_count: int
    occurrence_count: int
    template_match_count: int
    template_variant_count: int
    side_count: int
    quantized_area_ratio: float
    inflation_estimate: float
    selected_slots: tuple[str, ...]
    canonical_vertices: tuple[tuple[float, float], ...]
    line_families: tuple[BoundaryLineFamily, ...]
    marked_cell_signature: tuple[tuple[str, int], ...]
    example_roots: tuple[int, ...]
    example_subsets: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class DecompositionComponentGroup:
    region_signature: tuple[int, ...]
    component_macro_kind: str | None
    cell_count: int
    occurrence_count: int
    side_count: int
    quantized_area_ratio: float
    marked_cell_signature: tuple[tuple[str, int], ...]
    example_roots: tuple[int, ...]
    example_subsets: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class SupertileDecompositionGroup:
    seed_macro_kind: str
    base_cell_count: int
    candidate_cell_count: int
    template_match_count: int
    line_equations: tuple[BoundaryLineEquation, ...]
    component_groups: tuple[DecompositionComponentGroup, ...]
    canonical_vertices: tuple[tuple[float, float], ...]
    marked_cell_signature: tuple[tuple[str, int], ...]
    example_roots: tuple[int, ...]
    example_subsets: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class MacroCompositionCandidateGroup:
    seed_macro_kind: str
    base_cell_count: int
    candidate_cell_count: int
    template_match_count: int
    component_region_signatures: tuple[tuple[int, ...], ...]
    composition_macro_kind: str
    composed_cell_count: int
    occurrence_count: int
    side_count: int
    quantized_area_ratio: float
    marked_cell_signature: tuple[tuple[str, int], ...]
    example_roots: tuple[int, ...]
    example_subsets: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class MiningSummary:
    source_cell_count: int
    seed_index: int
    max_available_depth: int
    analyzed_root_count: int
    neighborhood_radius: int
    region_radius: int
    max_candidate_size: int
    min_candidate_size: int
    beam_width: int
    local_neighborhood_classes: tuple[NeighborhoodClassSummary, ...]
    macro_candidate_groups: tuple[MacroCandidateGroup, ...]
    seeded_supertile_groups: tuple[SeededSupertileGroup, ...]
    inflation_candidate_groups: tuple[InflationCandidateGroup, ...]
    boundary_template_groups: tuple[BoundaryTemplateGroup, ...]
    supertile_decomposition_groups: tuple[SupertileDecompositionGroup, ...]
    macro_composition_groups: tuple[MacroCompositionCandidateGroup, ...]


@dataclass(frozen=True)
class _ResolvedSeededOccurrence:
    grown_subset: tuple[int, ...]
    occurrence_roots: tuple[int, ...]
    centroid: tuple[float, float]
    orientation: int
    scale: float


@dataclass(frozen=True)
class _ResolvedSeededSupertileGroup:
    summary: SeededSupertileGroup
    matched_occurrences: tuple[_ResolvedSeededOccurrence, ...]
    selected_slot_keys: tuple[tuple[float, float, str], ...]


@dataclass(frozen=True)
class _ResolvedInflationOccurrence:
    grown_subset: tuple[int, ...]
    occurrence_roots: tuple[int, ...]


@dataclass(frozen=True)
class _ResolvedInflationCandidateGroup:
    summary: InflationCandidateGroup
    matched_occurrences: tuple[_ResolvedInflationOccurrence, ...]
    selected_slot_keys: tuple[tuple[float, float, str], ...]


@dataclass(frozen=True)
class _ResolvedBoundaryTemplateGroup:
    summary: BoundaryTemplateGroup
    matched_occurrences: tuple[_ResolvedInflationOccurrence, ...]


@dataclass(frozen=True)
class _ResolvedRegionComponent:
    region_signature: tuple[int, ...]
    subset: tuple[int, ...]
    macro_kind: str | None
    side_count: int
    quantized_area_ratio: float
    marked_cell_signature: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class _ResolvedTemplateOccurrence:
    occurrence: _ResolvedInflationOccurrence
    components: tuple[_ResolvedRegionComponent, ...]


def _edge_angle(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360.0


def _snap_angle(angle: float, *, increment: float = 30.0) -> int:
    return int(round(angle / increment) * increment) % 360


def _rotate_vertices(
    vertices: tuple[tuple[float, float], ...],
) -> tuple[tuple[float, float], ...]:
    rotations: list[tuple[float, tuple[tuple[float, float], ...]]] = []
    for offset in range(len(vertices)):
        rotated = vertices[offset:] + vertices[:offset]
        angle = _edge_angle(rotated[0], rotated[1])
        rotations.append((round(angle, 6), tuple(rotated)))
    return min(rotations, key=lambda item: item[0])[1]


def _orientation_token(vertices: tuple[tuple[float, float], ...]) -> str:
    rotated = _rotate_vertices(vertices)
    angle = _edge_angle(rotated[0], rotated[1])
    snapped = _snap_angle(angle)
    return str(snapped)


def _short_kind(kind: str) -> str:
    return "square" if kind.endswith("square") else "triangle"


def _short_cell_signature(cell: SourceCell) -> str:
    return f"{_short_kind(cell.kind)}:{cell.chirality or '-'}"


def load_source_cells() -> tuple[dict[int, SourceCell], int]:
    payload = json.loads(SOURCE_PATCH_PATH.read_text(encoding="utf-8"))
    seed_index = int(payload["seed_index"])
    cells = {
        int(raw_cell["index"]): SourceCell(
            index=int(raw_cell["index"]),
            kind=str(raw_cell["kind"]),
            chirality=raw_cell.get("chirality"),
            orientation_token=_orientation_token(
                tuple((float(vertex[0]), float(vertex[1])) for vertex in raw_cell["vertices"])
            ),
            vertices=tuple(
                (float(vertex[0]), float(vertex[1]))
                for vertex in raw_cell["vertices"]
            ),
            neighbors=tuple(int(neighbor) for neighbor in raw_cell["neighbors"]),
        )
        for raw_cell in payload["cells"]
    }
    return cells, seed_index


def compute_shell_distances(
    cells: dict[int, SourceCell],
    seed_index: int,
) -> dict[int, int]:
    distances: dict[int, int] = {seed_index: 0}
    queue: deque[int] = deque((seed_index,))
    while queue:
        current = queue.popleft()
        for neighbor in cells[current].neighbors:
            if neighbor in distances:
                continue
            distances[neighbor] = distances[current] + 1
            queue.append(neighbor)
    return distances


def classify_local_neighborhoods(
    cells: dict[int, SourceCell],
    neighborhood_radius: int,
) -> dict[int, str]:
    labels: dict[int, str] = {}
    for index in cells:
        shell_counts: list[str] = []
        distances: dict[int, int] = {index: 0}
        queue: deque[int] = deque((index,))
        while queue:
            current = queue.popleft()
            if distances[current] == neighborhood_radius:
                continue
            for neighbor in cells[current].neighbors:
                if neighbor in distances:
                    continue
                distances[neighbor] = distances[current] + 1
                queue.append(neighbor)

        for depth in range(neighborhood_radius + 1):
            shell_counter: Counter[str] = Counter()
            for member, member_depth in distances.items():
                if member_depth != depth:
                    continue
                cell = cells[member]
                shell_counter[_short_cell_signature(cell)] += 1
            shell_payload = ",".join(
                f"{label}={count}"
                for label, count in sorted(shell_counter.items())
            )
            shell_counts.append(f"d{depth}[{shell_payload}]")
        labels[index] = "|".join(shell_counts)
    return labels


def summarize_local_neighborhood_classes(
    cells: dict[int, SourceCell],
    shell_distances: dict[int, int],
    labels: dict[int, str],
    *,
    max_source_depth: int,
    top_groups: int,
) -> tuple[NeighborhoodClassSummary, ...]:
    groups: dict[str, list[int]] = defaultdict(list)
    for index, depth in shell_distances.items():
        if depth > max_source_depth:
            continue
        groups[labels[index]].append(index)

    summaries: list[NeighborhoodClassSummary] = []
    for signature, members in groups.items():
        kind_counts = Counter(cells[index].kind for index in members)
        depth_histogram = Counter(shell_distances[index] for index in members)
        summaries.append(
            NeighborhoodClassSummary(
                signature=signature,
                count=len(members),
                kind_counts=tuple(sorted(kind_counts.items())),
                depth_histogram=tuple(sorted(depth_histogram.items())),
                example_cells=tuple(sorted(members)[:5]),
            )
        )
    summaries.sort(
        key=lambda summary: (
            -summary.count,
            summary.kind_counts,
            summary.signature,
        )
    )
    return tuple(summaries[:top_groups])


def graph_ball(
    cells: dict[int, SourceCell],
    root_index: int,
    radius: int,
) -> tuple[int, ...]:
    distances: dict[int, int] = {root_index: 0}
    queue: deque[int] = deque((root_index,))
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


def _compress_collinear_boundary(
    coordinates: list[tuple[float, float]],
    *,
    tolerance: float = 1e-6,
) -> tuple[tuple[float, float], ...]:
    points = list(coordinates[:-1])
    changed = True
    while changed and len(points) >= 3:
        changed = False
        reduced: list[tuple[float, float]] = []
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


def _edge_lengths(vertices: tuple[tuple[float, float], ...]) -> tuple[float, ...]:
    lengths: list[float] = []
    for index, left in enumerate(vertices):
        right = vertices[(index + 1) % len(vertices)]
        lengths.append(math.dist(left, right))
    return tuple(lengths)


def _interior_angles(vertices: tuple[tuple[float, float], ...]) -> tuple[float, ...]:
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


def _classify_macro_kind(
    side_count: int,
    edge_lengths: tuple[float, ...],
    interior_angles: tuple[float, ...],
) -> str | None:
    if not edge_lengths or min(edge_lengths) <= 1e-9:
        return None
    edge_ratio = max(edge_lengths) / min(edge_lengths)
    if side_count == 3 and edge_ratio <= 1.35:
        if max(abs(angle - 60.0) for angle in interior_angles) <= 30.0:
            return "triangle"
    if side_count == 4 and edge_ratio <= 1.35:
        if max(abs(angle - 90.0) for angle in interior_angles) <= 30.0:
            return "square"
    return None


def _compactness(area: float, perimeter: float) -> float:
    if perimeter <= 1e-9:
        return 0.0
    return (4.0 * math.pi * area) / (perimeter * perimeter)


def _merged_boundary(
    subset: frozenset[int] | tuple[int, ...],
    polygons: dict[int, Polygon],
) -> tuple[Polygon, tuple[tuple[float, float], ...]] | None:
    merged = unary_union([polygons[index] for index in subset])
    if merged.geom_type != "Polygon":
        return None
    if len(merged.interiors) > 0:
        return None
    boundary = _compress_collinear_boundary(list(merged.exterior.coords))
    if len(boundary) < 3:
        return None
    return merged, boundary


def _evaluate_subset(
    subset: frozenset[int],
    polygons: dict[int, Polygon],
    *,
    primitive_area: float,
) -> tuple[tuple[Any, ...], dict[str, Any]] | None:
    merged_result = _merged_boundary(subset, polygons)
    if merged_result is None:
        return None
    merged, boundary = merged_result

    edge_lengths = _edge_lengths(boundary)
    interior_angles = _interior_angles(boundary)
    side_count = len(boundary)
    convex_hull_area = merged.convex_hull.area
    convexity = merged.area / convex_hull_area if convex_hull_area > 1e-9 else 1.0
    area_ratio = merged.area / primitive_area
    compactness = _compactness(merged.area, merged.length)
    macro_kind = _classify_macro_kind(side_count, edge_lengths, interior_angles)

    shape_penalty = min(abs(side_count - 3), abs(side_count - 4))
    score = (
        -shape_penalty,
        round(convexity, 6),
        round(compactness, 6),
        round(area_ratio, 6),
    )

    edge_signature = tuple(sorted(round(length / sum(edge_lengths), 2) for length in edge_lengths))
    angle_signature = tuple(sorted(int(round(angle / 5.0) * 5) for angle in interior_angles))

    metrics = {
        "macro_kind": macro_kind,
        "side_count": side_count,
        "area_ratio": area_ratio,
        "compactness": compactness,
        "edge_length_signature": edge_signature,
        "angle_signature": angle_signature,
    }
    return score, metrics


def _multi_source_ball(
    cells: dict[int, SourceCell],
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


def _shape_symmetry_transforms(
    macro_kind: str,
    x: float,
    y: float,
) -> tuple[tuple[float, float], ...]:
    transforms: set[tuple[float, float]] = set()
    if macro_kind == "square":
        rotation_steps = 4
        reflection_offsets = (1.0, -1.0)
        angle_increment = 90.0
    else:
        rotation_steps = 3
        reflection_offsets = (1.0, -1.0)
        angle_increment = 120.0

    for step in range(rotation_steps):
        angle = math.radians(step * angle_increment)
        rotated_x = x * math.cos(angle) - y * math.sin(angle)
        rotated_y = x * math.sin(angle) + y * math.cos(angle)
        for reflection in reflection_offsets:
            transforms.add((
                round(reflection * rotated_x, 2),
                round(rotated_y, 2),
            ))
    return tuple(sorted(transforms))


def _canonical_slot_key(
    *,
    cell: SourceCell,
    centroid: tuple[float, float],
    orientation: int,
    scale: float,
    macro_kind: str,
    polygon: Polygon,
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
    transforms = _shape_symmetry_transforms(macro_kind, local_x, local_y)
    canonical_x, canonical_y = min(transforms)
    return (canonical_x, canonical_y, _short_cell_signature(cell))


def _format_slot_key(slot_key: tuple[float, float, str]) -> str:
    return f"{slot_key[2]}@({slot_key[0]:.2f},{slot_key[1]:.2f})"


def _subset_frame(
    subset: tuple[int, ...],
    polygons: dict[int, Polygon],
) -> tuple[tuple[float, float], int, float] | None:
    merged_result = _merged_boundary(subset, polygons)
    if merged_result is None:
        return None
    merged, boundary = merged_result
    rotated_boundary = _rotate_vertices(boundary)
    orientation = _snap_angle(_edge_angle(rotated_boundary[0], rotated_boundary[1]))
    edge_lengths = _edge_lengths(rotated_boundary)
    scale = sum(edge_lengths) / len(edge_lengths)
    if scale <= 1e-9:
        return None
    return ((merged.centroid.x, merged.centroid.y), orientation, scale)


def _boundary_direction_histogram(
    boundary: tuple[tuple[float, float], ...],
    *,
    orientation: int,
) -> tuple[tuple[int, int], ...]:
    histogram: Counter[int] = Counter()
    for index, point in enumerate(boundary):
        right = boundary[(index + 1) % len(boundary)]
        local_angle = (_edge_angle(point, right) - orientation) % 360.0
        histogram[_snap_angle(local_angle)] += 1
    return tuple(sorted(histogram.items()))


def _normalized_boundary(
    boundary: tuple[tuple[float, float], ...],
    *,
    centroid: tuple[float, float],
    orientation: int,
    scale: float,
) -> tuple[tuple[float, float], ...]:
    rotation = math.radians(-orientation)
    normalized_vertices: list[tuple[float, float]] = []
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


def _normalize_point(
    point: tuple[float, float],
    *,
    centroid: tuple[float, float],
    orientation: int,
    scale: float,
) -> tuple[float, float]:
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


def _transform_normalized_point(
    point: tuple[float, float],
    *,
    macro_kind: str,
    rotation_step: int,
    reflection: bool,
) -> tuple[float, float]:
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


def _canonical_cycle(
    points: tuple[tuple[float, float], ...],
) -> tuple[tuple[float, float], ...]:
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


def _canonicalize_boundary_template(
    boundary: tuple[tuple[float, float], ...],
    *,
    centroid: tuple[float, float],
    orientation: int,
    scale: float,
    macro_kind: str,
) -> tuple[tuple[float, float], ...]:
    normalized_vertices = _normalized_boundary(
        boundary,
        centroid=centroid,
        orientation=orientation,
        scale=scale,
    )
    rotation_steps = 4 if macro_kind == "square" else 3
    candidates: list[tuple[tuple[float, float], ...]] = []
    for step in range(rotation_steps):
        for reflection in (False, True):
            transformed = tuple(
                _transform_normalized_point(
                    point,
                    macro_kind=macro_kind,
                    rotation_step=step,
                    reflection=reflection,
                )
                for point in normalized_vertices
            )
            candidates.append(_canonical_cycle(transformed))
    return min(candidates)


def _line_families_from_canonical_vertices(
    canonical_vertices: tuple[tuple[float, float], ...],
) -> tuple[BoundaryLineFamily, ...]:
    offsets_by_axis: dict[int, list[float]] = defaultdict(list)
    counts_by_axis: Counter[int] = Counter()
    for index, point in enumerate(canonical_vertices):
        right = canonical_vertices[(index + 1) % len(canonical_vertices)]
        direction = _snap_angle(_edge_angle(point, right))
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


def _line_equations_from_line_families(
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


def collect_macro_occurrences(
    cells: dict[int, SourceCell],
    shell_distances: dict[int, int],
    local_labels: dict[int, str],
    *,
    max_source_depth: int,
    region_radius: int,
    max_candidate_size: int,
    min_candidate_size: int,
    beam_width: int,
) -> dict[
    tuple[str, int, float, tuple[float, ...], tuple[int, ...]],
    list[tuple[tuple[int, ...], dict[str, Any]]],
]:
    polygons = {
        index: Polygon(cell.vertices)
        for index, cell in cells.items()
    }
    primitive_area = polygons[min(cells)].area
    for index, cell in cells.items():
        if cell.kind.endswith("square"):
            primitive_area = polygons[index].area
            break

    occurrences_by_subset: dict[tuple[int, ...], dict[str, Any]] = {}

    for root_index, root_depth in sorted(shell_distances.items(), key=lambda item: (item[1], item[0])):
        if root_depth > max_source_depth:
            continue
        region = set(graph_ball(cells, root_index, region_radius))
        frontier: list[frozenset[int]] = [frozenset((root_index,))]
        seen_subsets: set[frozenset[int]] = set(frontier)

        for _ in range(1, max_candidate_size):
            next_states: list[tuple[tuple[Any, ...], frozenset[int], dict[str, Any]]] = []
            for subset in frontier:
                boundary_neighbors: set[int] = set()
                for member in subset:
                    boundary_neighbors.update(
                        neighbor
                        for neighbor in cells[member].neighbors
                        if neighbor in region and neighbor not in subset
                    )
                for neighbor in sorted(boundary_neighbors):
                    candidate = frozenset((*subset, neighbor))
                    if candidate in seen_subsets:
                        continue
                    seen_subsets.add(candidate)
                    evaluated = _evaluate_subset(
                        candidate,
                        polygons,
                        primitive_area=primitive_area,
                    )
                    if evaluated is None:
                        continue
                    score, metrics = evaluated
                    next_states.append((score, candidate, metrics))

                    if len(candidate) < min_candidate_size or metrics["macro_kind"] is None:
                        continue

                    subset_key = tuple(sorted(candidate))
                    occurrence = occurrences_by_subset.setdefault(
                        subset_key,
                        {
                            "macro_kind": metrics["macro_kind"],
                            "side_count": metrics["side_count"],
                            "area_ratio": metrics["area_ratio"],
                            "edge_length_signature": metrics["edge_length_signature"],
                            "angle_signature": metrics["angle_signature"],
                            "roots": set(),
                            "root_signatures": Counter(),
                        },
                    )
                    occurrence["roots"].add(root_index)
                    occurrence["root_signatures"][local_labels[root_index]] += 1

            next_states.sort(key=lambda item: item[0], reverse=True)
            frontier = [subset for _, subset, _ in next_states[:beam_width]]
            if not frontier:
                break

    grouped: dict[
        tuple[str, int, float, tuple[float, ...], tuple[int, ...]],
        list[tuple[tuple[int, ...], dict[str, Any]]],
    ] = defaultdict(list)
    for subset_key, occurrence in occurrences_by_subset.items():
        group_key = (
            str(occurrence["macro_kind"]),
            len(subset_key),
            round(float(occurrence["area_ratio"]), 2),
            tuple(float(value) for value in occurrence["edge_length_signature"]),
            tuple(int(value) for value in occurrence["angle_signature"]),
        )
        grouped[group_key].append((subset_key, occurrence))

    return grouped


def summarize_macro_occurrences(
    grouped: dict[
        tuple[str, int, float, tuple[float, ...], tuple[int, ...]],
        list[tuple[tuple[int, ...], dict[str, Any]]],
    ],
    *,
    top_groups: int,
) -> tuple[MacroCandidateGroup, ...]:
    summaries: list[MacroCandidateGroup] = []
    for (
        macro_kind,
        cell_count,
        quantized_area_ratio,
        edge_length_signature,
        angle_signature,
    ), members in grouped.items():
        root_signature_counts: Counter[str] = Counter()
        example_roots: list[int] = []
        example_subsets: list[tuple[int, ...]] = []
        side_count = int(members[0][1]["side_count"])
        for subset_key, occurrence in members:
            root_signature_counts.update(occurrence["root_signatures"])
            example_roots.extend(sorted(int(root) for root in occurrence["roots"]))
            if len(example_subsets) < 3:
                example_subsets.append(subset_key)
        summaries.append(
            MacroCandidateGroup(
                macro_kind=macro_kind,
                side_count=side_count,
                cell_count=cell_count,
                occurrence_count=len(members),
                quantized_area_ratio=quantized_area_ratio,
                edge_length_signature=edge_length_signature,
                angle_signature=angle_signature,
                root_signature_counts=tuple(root_signature_counts.most_common(5)),
                example_roots=tuple(sorted(set(example_roots))[:5]),
                example_subsets=tuple(example_subsets),
            )
        )
    summaries.sort(
        key=lambda summary: (
            -summary.occurrence_count,
            -summary.cell_count,
            summary.macro_kind,
            summary.edge_length_signature,
            summary.angle_signature,
        )
    )
    return tuple(summaries[:top_groups])


def mine_macro_candidates(
    cells: dict[int, SourceCell],
    shell_distances: dict[int, int],
    local_labels: dict[int, str],
    *,
    max_source_depth: int,
    region_radius: int,
    max_candidate_size: int,
    min_candidate_size: int,
    beam_width: int,
    top_groups: int,
) -> tuple[MacroCandidateGroup, ...]:
    grouped = collect_macro_occurrences(
        cells,
        shell_distances,
        local_labels,
        max_source_depth=max_source_depth,
        region_radius=region_radius,
        max_candidate_size=max_candidate_size,
        min_candidate_size=min_candidate_size,
        beam_width=beam_width,
    )
    return summarize_macro_occurrences(grouped, top_groups=top_groups)


def _resolve_seeded_supertile_groups(
    cells: dict[int, SourceCell],
    grouped_macro_occurrences: dict[
        tuple[str, int, float, tuple[float, ...], tuple[int, ...]],
        list[tuple[tuple[int, ...], dict[str, Any]]],
    ],
    *,
    top_groups: int,
    max_seed_groups: int = 4,
    max_seed_cell_count: int = 4,
    growth_radius: int = 1,
    slot_support_ratio: float = 0.65,
) -> tuple[_ResolvedSeededSupertileGroup, ...]:
    polygons = {
        index: Polygon(cell.vertices)
        for index, cell in cells.items()
    }
    primitive_area = next(
        polygons[index].area
        for index, cell in cells.items()
        if cell.kind.endswith("square")
    )

    sorted_seed_groups = sorted(
        grouped_macro_occurrences.items(),
        key=lambda item: (
            -len(item[1]),
            -item[0][1],
            item[0][0],
            item[0][3],
            item[0][4],
        ),
    )

    resolved_groups: list[_ResolvedSeededSupertileGroup] = []
    candidate_group_limit = max(top_groups * 3, top_groups)
    for group_key, members in sorted_seed_groups[:candidate_group_limit]:
        seed_macro_kind, seed_cell_count, _, _, _ = group_key
        if seed_macro_kind not in {"square", "triangle"}:
            continue
        if seed_cell_count > max_seed_cell_count:
            continue
        if len(members) < 3:
            continue
        if len(resolved_groups) >= max_seed_groups:
            break

        slot_occurrence_counts: Counter[tuple[float, float, str]] = Counter()
        per_occurrence_slots: list[
            tuple[
                tuple[int, ...],
                tuple[int, ...],
                tuple[float, float],
                int,
                float,
                dict[tuple[float, float, str], list[int]],
            ]
        ] = []
        for subset_key, occurrence in members:
            frame = _subset_frame(subset_key, polygons)
            if frame is None:
                continue
            centroid, orientation, scale = frame
            region = _multi_source_ball(cells, subset_key, growth_radius)
            slot_to_cells: dict[tuple[float, float, str], list[int]] = defaultdict(list)
            for candidate_index in region:
                if candidate_index in subset_key:
                    continue
                slot_key = _canonical_slot_key(
                    cell=cells[candidate_index],
                    centroid=centroid,
                    orientation=orientation,
                    scale=scale,
                    macro_kind=seed_macro_kind,
                    polygon=polygons[candidate_index],
                )
                slot_to_cells[slot_key].append(candidate_index)
            per_occurrence_slots.append((
                subset_key,
                tuple(sorted(int(root_index) for root_index in occurrence["roots"])),
                centroid,
                orientation,
                scale,
                slot_to_cells,
            ))
            for slot_key in slot_to_cells:
                slot_occurrence_counts[slot_key] += 1

        if not per_occurrence_slots:
            continue

        slot_support_threshold = max(
            2,
            math.ceil(len(per_occurrence_slots) * slot_support_ratio),
        )
        selected_slots = {
            slot_key
            for slot_key, count in slot_occurrence_counts.items()
            if count >= slot_support_threshold
        }
        if not selected_slots:
            continue

        grown_groups: dict[
            tuple[str | None, int, int, float, tuple[tuple[str, int], ...]],
            dict[str, Any],
        ] = {}
        for (
            subset_key,
            occurrence_roots,
            centroid,
            orientation,
            scale,
            slot_to_cells,
        ) in per_occurrence_slots:
            grown_subset = set(subset_key)
            for slot_key in selected_slots:
                slot_cells = slot_to_cells.get(slot_key)
                if slot_cells:
                    grown_subset.add(min(slot_cells))
            if len(grown_subset) <= len(subset_key):
                continue

            grown_tuple = tuple(sorted(grown_subset))
            evaluated = _evaluate_subset(
                frozenset(grown_tuple),
                polygons,
                primitive_area=primitive_area,
            )
            if evaluated is None:
                continue
            _, metrics = evaluated
            marked_signature = tuple(sorted(
                Counter(_short_cell_signature(cells[index]) for index in grown_tuple).items()
            ))
            grown_group_key = (
                metrics["macro_kind"],
                len(grown_tuple),
                int(metrics["side_count"]),
                round(float(metrics["area_ratio"]), 2),
                marked_signature,
            )
            grown_group = grown_groups.setdefault(
                grown_group_key,
                {
                    "occurrence_count": 0,
                    "roots": set(),
                    "subsets": [],
                    "side_count": metrics["side_count"],
                    "area_ratio": metrics["area_ratio"],
                    "edge_length_signature": metrics["edge_length_signature"],
                    "angle_signature": metrics["angle_signature"],
                    "occurrences": [],
                },
            )
            grown_group["occurrence_count"] += 1
            grown_group["roots"].update(occurrence_roots)
            if len(grown_group["subsets"]) < 3:
                grown_group["subsets"].append(grown_tuple)
            grown_group["occurrences"].append(
                _ResolvedSeededOccurrence(
                    grown_subset=grown_tuple,
                    occurrence_roots=occurrence_roots,
                    centroid=centroid,
                    orientation=orientation,
                    scale=scale,
                )
            )

        if not grown_groups:
            continue

        best_group_key, best_group = max(
            grown_groups.items(),
            key=lambda item: (
                int(item[1]["occurrence_count"]),
                item[0][1],
                item[0][0] or "",
            ),
        )
        grown_macro_kind, grown_cell_count, _side_count, quantized_area_ratio, marked_signature = best_group_key
        boundary_result = _merged_boundary(best_group["subsets"][0], polygons)
        if boundary_result is None:
            continue
        _merged, boundary = boundary_result
        best_occurrence = best_group["occurrences"][0]
        resolved_groups.append(
            _ResolvedSeededSupertileGroup(
                summary=SeededSupertileGroup(
                seed_macro_kind=seed_macro_kind,
                seed_cell_count=seed_cell_count,
                grown_macro_kind=grown_macro_kind,
                grown_cell_count=grown_cell_count,
                occurrence_count=int(best_group["occurrence_count"]),
                side_count=int(best_group["side_count"]),
                quantized_area_ratio=float(quantized_area_ratio),
                selected_slot_count=len(selected_slots),
                selected_slots=tuple(sorted(_format_slot_key(slot_key) for slot_key in selected_slots)),
                boundary_direction_histogram=_boundary_direction_histogram(
                    boundary,
                    orientation=best_occurrence.orientation,
                ),
                marked_cell_signature=marked_signature,
                edge_length_signature=tuple(float(value) for value in best_group["edge_length_signature"]),
                angle_signature=tuple(int(value) for value in best_group["angle_signature"]),
                example_roots=tuple(sorted(int(root) for root in best_group["roots"])[:5]),
                example_subsets=tuple(best_group["subsets"]),
                ),
                matched_occurrences=tuple(best_group["occurrences"]),
                selected_slot_keys=tuple(sorted(selected_slots)),
            )
        )

    resolved_groups.sort(
        key=lambda group: (
            -group.summary.occurrence_count,
            -group.summary.grown_cell_count,
            group.summary.seed_macro_kind,
            group.summary.marked_cell_signature,
        )
    )
    return tuple(resolved_groups[:top_groups])


def mine_seeded_supertile_groups(
    cells: dict[int, SourceCell],
    grouped_macro_occurrences: dict[
        tuple[str, int, float, tuple[float, ...], tuple[int, ...]],
        list[tuple[tuple[int, ...], dict[str, Any]]],
    ],
    *,
    top_groups: int,
    max_seed_groups: int = 4,
    max_seed_cell_count: int = 4,
    growth_radius: int = 1,
    slot_support_ratio: float = 0.65,
) -> tuple[SeededSupertileGroup, ...]:
    resolved_groups = _resolve_seeded_supertile_groups(
        cells,
        grouped_macro_occurrences,
        top_groups=top_groups,
        max_seed_groups=max_seed_groups,
        max_seed_cell_count=max_seed_cell_count,
        growth_radius=growth_radius,
        slot_support_ratio=slot_support_ratio,
    )
    return tuple(group.summary for group in resolved_groups)


def _resolve_inflation_candidate_groups(
    cells: dict[int, SourceCell],
    grouped_macro_occurrences: dict[
        tuple[str, int, float, tuple[float, ...], tuple[int, ...]],
        list[tuple[tuple[int, ...], dict[str, Any]]],
    ],
    *,
    top_groups: int,
    max_combo_size: int = 5,
    growth_radius: int = 2,
    slot_support_ratio: float = 0.65,
) -> tuple[_ResolvedInflationCandidateGroup, ...]:
    polygons = {
        index: Polygon(cell.vertices)
        for index, cell in cells.items()
    }
    primitive_area = next(
        polygons[index].area
        for index, cell in cells.items()
        if cell.kind.endswith("square")
    )

    resolved_seed_groups = _resolve_seeded_supertile_groups(
        cells,
        grouped_macro_occurrences,
        top_groups=top_groups,
    )

    resolved_candidate_groups: list[_ResolvedInflationCandidateGroup] = []
    for resolved_group in resolved_seed_groups:
        slot_occurrence_counts: Counter[tuple[float, float, str]] = Counter()
        per_occurrence_slots: list[
            tuple[_ResolvedSeededOccurrence, dict[tuple[float, float, str], list[int]]]
        ] = []
        for occurrence in resolved_group.matched_occurrences:
            region = _multi_source_ball(cells, occurrence.grown_subset, growth_radius)
            slot_to_cells: dict[tuple[float, float, str], list[int]] = defaultdict(list)
            for candidate_index in region:
                if candidate_index in occurrence.grown_subset:
                    continue
                slot_key = _canonical_slot_key(
                    cell=cells[candidate_index],
                    centroid=occurrence.centroid,
                    orientation=occurrence.orientation,
                    scale=occurrence.scale,
                    macro_kind=resolved_group.summary.seed_macro_kind,
                    polygon=polygons[candidate_index],
                )
                slot_to_cells[slot_key].append(candidate_index)
            per_occurrence_slots.append((occurrence, slot_to_cells))
            for slot_key in slot_to_cells:
                slot_occurrence_counts[slot_key] += 1

        if not per_occurrence_slots:
            continue

        slot_support_threshold = max(
            2,
            math.ceil(len(per_occurrence_slots) * slot_support_ratio),
        )
        stable_slots = sorted(
            slot_key
            for slot_key, count in slot_occurrence_counts.items()
            if count >= slot_support_threshold
        )
        if len(stable_slots) < 2:
            continue

        candidate_groups: dict[
            tuple[
                tuple[tuple[float, float, str], ...],
                str | None,
                int,
                int,
                float,
                tuple[tuple[str, int], ...],
            ],
            dict[str, Any],
        ] = {}
        max_effective_combo_size = min(max_combo_size, len(stable_slots))
        for combo_size in range(2, max_effective_combo_size + 1):
            for slot_combo in combinations(stable_slots, combo_size):
                for occurrence, slot_to_cells in per_occurrence_slots:
                    expanded_subset = set(occurrence.grown_subset)
                    matched_any = False
                    for slot_key in slot_combo:
                        slot_cells = slot_to_cells.get(slot_key)
                        if slot_cells:
                            expanded_subset.add(min(slot_cells))
                            matched_any = True
                    if not matched_any:
                        continue

                    expanded_tuple = tuple(sorted(expanded_subset))
                    evaluated = _evaluate_subset(
                        frozenset(expanded_tuple),
                        polygons,
                        primitive_area=primitive_area,
                    )
                    if evaluated is None:
                        continue

                    _, metrics = evaluated
                    marked_signature = tuple(sorted(
                        Counter(_short_cell_signature(cells[index]) for index in expanded_tuple).items()
                    ))
                    candidate_key = (
                        tuple(slot_combo),
                        metrics["macro_kind"],
                        len(expanded_tuple),
                        int(metrics["side_count"]),
                        round(float(metrics["area_ratio"]), 2),
                        marked_signature,
                    )
                    boundary_result = _merged_boundary(expanded_tuple, polygons)
                    if boundary_result is None:
                        continue
                    _merged, boundary = boundary_result
                    candidate_group = candidate_groups.setdefault(
                        candidate_key,
                        {
                            "occurrence_count": 0,
                            "roots": set(),
                            "subsets": [],
                            "edge_length_signature": metrics["edge_length_signature"],
                            "angle_signature": metrics["angle_signature"],
                            "boundary_direction_histogram": _boundary_direction_histogram(
                                boundary,
                                orientation=occurrence.orientation,
                            ),
                            "occurrences": [],
                        },
                    )
                    candidate_group["occurrence_count"] += 1
                    candidate_group["roots"].update(occurrence.occurrence_roots)
                    if len(candidate_group["subsets"]) < 3:
                        candidate_group["subsets"].append(expanded_tuple)
                    candidate_group["occurrences"].append(
                        _ResolvedInflationOccurrence(
                            grown_subset=expanded_tuple,
                            occurrence_roots=occurrence.occurrence_roots,
                        )
                    )

        if not candidate_groups:
            continue

        sorted_candidate_groups = sorted(
            candidate_groups.items(),
            key=lambda item: (
                -int(item[1]["occurrence_count"]),
                -(item[0][2]),
                item[0][1] is None,
                item[0][3],
                item[0][5],
            ),
        )
        candidate_limit = min(top_groups, len(sorted_candidate_groups))
        for candidate_key, candidate_group in sorted_candidate_groups[:candidate_limit]:
            slot_combo, grown_macro_kind, grown_cell_count, side_count, quantized_area_ratio, marked_signature = candidate_key
            inflation_estimate = math.sqrt(
                float(quantized_area_ratio) / resolved_group.summary.quantized_area_ratio
            )
            resolved_candidate_groups.append(
                _ResolvedInflationCandidateGroup(
                    summary=InflationCandidateGroup(
                    seed_macro_kind=resolved_group.summary.seed_macro_kind,
                    seed_cell_count=resolved_group.summary.seed_cell_count,
                    base_cell_count=resolved_group.summary.grown_cell_count,
                    grown_macro_kind=grown_macro_kind,
                    grown_cell_count=grown_cell_count,
                    occurrence_count=int(candidate_group["occurrence_count"]),
                    combo_size=len(slot_combo),
                    side_count=side_count,
                    quantized_area_ratio=float(quantized_area_ratio),
                    inflation_estimate=round(inflation_estimate, 3),
                    selected_slots=tuple(
                        _format_slot_key(slot_key) for slot_key in slot_combo
                    ),
                    boundary_direction_histogram=tuple(candidate_group["boundary_direction_histogram"]),
                    marked_cell_signature=marked_signature,
                    edge_length_signature=tuple(
                        float(value) for value in candidate_group["edge_length_signature"]
                    ),
                    angle_signature=tuple(
                        int(value) for value in candidate_group["angle_signature"]
                    ),
                    example_roots=tuple(sorted(int(root) for root in candidate_group["roots"])[:5]),
                    example_subsets=tuple(candidate_group["subsets"]),
                    ),
                    matched_occurrences=tuple(candidate_group["occurrences"]),
                    selected_slot_keys=slot_combo,
                )
            )

    resolved_candidate_groups.sort(
        key=lambda group: (
            -group.summary.occurrence_count,
            -group.summary.grown_cell_count,
            group.summary.grown_macro_kind is None,
            group.summary.side_count,
            group.summary.marked_cell_signature,
        )
    )
    return tuple(resolved_candidate_groups[:top_groups])


def mine_inflation_candidate_groups(
    cells: dict[int, SourceCell],
    grouped_macro_occurrences: dict[
        tuple[str, int, float, tuple[float, ...], tuple[int, ...]],
        list[tuple[tuple[int, ...], dict[str, Any]]],
    ],
    *,
    top_groups: int,
    max_combo_size: int = 5,
    growth_radius: int = 2,
    slot_support_ratio: float = 0.65,
) -> tuple[InflationCandidateGroup, ...]:
    resolved_groups = _resolve_inflation_candidate_groups(
        cells,
        grouped_macro_occurrences,
        top_groups=top_groups,
        max_combo_size=max_combo_size,
        growth_radius=growth_radius,
        slot_support_ratio=slot_support_ratio,
    )
    return tuple(group.summary for group in resolved_groups)


def _resolve_boundary_template_groups(
    cells: dict[int, SourceCell],
    grouped_macro_occurrences: dict[
        tuple[str, int, float, tuple[float, ...], tuple[int, ...]],
        list[tuple[tuple[int, ...], dict[str, Any]]],
    ],
    *,
    top_groups: int,
) -> tuple[_ResolvedBoundaryTemplateGroup, ...]:
    polygons = {
        index: Polygon(cell.vertices)
        for index, cell in cells.items()
    }
    resolved_inflation_groups = _resolve_inflation_candidate_groups(
        cells,
        grouped_macro_occurrences,
        top_groups=top_groups,
    )

    resolved_templates: list[_ResolvedBoundaryTemplateGroup] = []
    for resolved_group in resolved_inflation_groups:
        template_occurrence_counts: Counter[tuple[tuple[float, float], ...]] = Counter()
        template_examples: dict[tuple[tuple[float, float], ...], tuple[int, ...]] = {}
        template_occurrences: dict[
            tuple[tuple[float, float], ...],
            list[_ResolvedInflationOccurrence],
        ] = defaultdict(list)
        for occurrence in resolved_group.matched_occurrences:
            frame = _subset_frame(occurrence.grown_subset, polygons)
            boundary_result = _merged_boundary(occurrence.grown_subset, polygons)
            if frame is None or boundary_result is None:
                continue
            centroid, orientation, scale = frame
            _merged, boundary = boundary_result
            canonical_vertices = _canonicalize_boundary_template(
                boundary,
                centroid=centroid,
                orientation=orientation,
                scale=scale,
                macro_kind=resolved_group.summary.seed_macro_kind,
            )
            template_occurrence_counts[canonical_vertices] += 1
            template_examples.setdefault(canonical_vertices, occurrence.grown_subset)
            template_occurrences[canonical_vertices].append(occurrence)

        if not template_occurrence_counts:
            continue

        dominant_template, template_match_count = max(
            template_occurrence_counts.items(),
            key=lambda item: (item[1], len(item[0])),
        )
        line_families = _line_families_from_canonical_vertices(dominant_template)
        resolved_templates.append(
            _ResolvedBoundaryTemplateGroup(
                summary=BoundaryTemplateGroup(
                    seed_macro_kind=resolved_group.summary.seed_macro_kind,
                    base_cell_count=resolved_group.summary.base_cell_count,
                    candidate_cell_count=resolved_group.summary.grown_cell_count,
                    occurrence_count=resolved_group.summary.occurrence_count,
                    template_match_count=int(template_match_count),
                    template_variant_count=len(template_occurrence_counts),
                    side_count=resolved_group.summary.side_count,
                    quantized_area_ratio=resolved_group.summary.quantized_area_ratio,
                    inflation_estimate=resolved_group.summary.inflation_estimate,
                    selected_slots=resolved_group.summary.selected_slots,
                    canonical_vertices=dominant_template,
                    line_families=line_families,
                    marked_cell_signature=resolved_group.summary.marked_cell_signature,
                    example_roots=resolved_group.summary.example_roots,
                    example_subsets=resolved_group.summary.example_subsets,
                ),
                matched_occurrences=tuple(template_occurrences[dominant_template]),
            )
        )

    resolved_templates.sort(
        key=lambda group: (
            -group.summary.candidate_cell_count,
            -group.summary.template_match_count,
            group.summary.seed_macro_kind,
            group.summary.marked_cell_signature,
        )
    )
    return tuple(resolved_templates[:top_groups])


def mine_boundary_template_groups(
    cells: dict[int, SourceCell],
    grouped_macro_occurrences: dict[
        tuple[str, int, float, tuple[float, ...], tuple[int, ...]],
        list[tuple[tuple[int, ...], dict[str, Any]]],
    ],
    *,
    top_groups: int,
) -> tuple[BoundaryTemplateGroup, ...]:
    resolved_templates = _resolve_boundary_template_groups(
        cells,
        grouped_macro_occurrences,
        top_groups=top_groups,
    )
    return tuple(template.summary for template in resolved_templates)


def _resolve_template_occurrences(
    cells: dict[int, SourceCell],
    polygons: dict[int, Polygon],
    *,
    primitive_area: float,
    resolved_template: _ResolvedBoundaryTemplateGroup,
) -> tuple[_ResolvedTemplateOccurrence, ...]:
    resolved_occurrences: list[_ResolvedTemplateOccurrence] = []
    for occurrence in resolved_template.matched_occurrences:
        frame = _subset_frame(occurrence.grown_subset, polygons)
        if frame is None:
            continue
        centroid, orientation, scale = frame
        region_members: dict[tuple[int, ...], list[int]] = defaultdict(list)
        for cell_index in occurrence.grown_subset:
            polygon = polygons[cell_index]
            point = _normalize_point(
                (polygon.centroid.x, polygon.centroid.y),
                centroid=centroid,
                orientation=orientation,
                scale=scale,
            )
            region_signature_values: list[int] = []
            for family in resolved_template.summary.line_families:
                theta = math.radians(family.axis_angle)
                value = point[0] * math.cos(theta) + point[1] * math.sin(theta)
                interval_index = 0
                while interval_index < len(family.offsets) and value > family.offsets[interval_index]:
                    interval_index += 1
                region_signature_values.append(interval_index)
            region_members[tuple(region_signature_values)].append(cell_index)

        components: list[_ResolvedRegionComponent] = []
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
                evaluated = _evaluate_subset(
                    frozenset(component_subset),
                    polygons,
                    primitive_area=primitive_area,
                )
                if evaluated is None:
                    continue
                _, metrics = evaluated
                marked_signature = tuple(sorted(
                    Counter(
                        _short_cell_signature(cells[index])
                        for index in component_subset
                    ).items()
                ))
                components.append(
                    _ResolvedRegionComponent(
                        region_signature=region_signature,
                        subset=component_subset,
                        macro_kind=metrics["macro_kind"],
                        side_count=int(metrics["side_count"]),
                        quantized_area_ratio=round(float(metrics["area_ratio"]), 2),
                        marked_cell_signature=marked_signature,
                    )
                )
        resolved_occurrences.append(
            _ResolvedTemplateOccurrence(
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


def mine_supertile_decomposition_groups(
    cells: dict[int, SourceCell],
    grouped_macro_occurrences: dict[
        tuple[str, int, float, tuple[float, ...], tuple[int, ...]],
        list[tuple[tuple[int, ...], dict[str, Any]]],
    ],
    *,
    top_groups: int,
) -> tuple[SupertileDecompositionGroup, ...]:
    polygons = {
        index: Polygon(cell.vertices)
        for index, cell in cells.items()
    }
    primitive_area = next(
        polygons[index].area
        for index, cell in cells.items()
        if cell.kind.endswith("square")
    )
    resolved_templates = _resolve_boundary_template_groups(
        cells,
        grouped_macro_occurrences,
        top_groups=top_groups,
    )

    decomposition_groups: list[SupertileDecompositionGroup] = []
    for resolved_template in resolved_templates:
        resolved_occurrences = _resolve_template_occurrences(
            cells,
            polygons,
            primitive_area=primitive_area,
            resolved_template=resolved_template,
        )
        component_groups: dict[
            tuple[tuple[int, ...], str | None, int, int, float, tuple[tuple[str, int], ...]],
            dict[str, Any],
        ] = {}
        for resolved_occurrence in resolved_occurrences:
            for component in resolved_occurrence.components:
                component_key = (
                    component.region_signature,
                    component.macro_kind,
                    len(component.subset),
                    component.side_count,
                    component.quantized_area_ratio,
                    component.marked_cell_signature,
                )
                component_group = component_groups.setdefault(
                    component_key,
                    {
                        "occurrence_count": 0,
                        "roots": set(),
                        "subsets": [],
                    },
                )
                component_group["occurrence_count"] += 1
                component_group["roots"].update(resolved_occurrence.occurrence.occurrence_roots)
                if len(component_group["subsets"]) < 3:
                    component_group["subsets"].append(component.subset)

        sorted_components = sorted(
            component_groups.items(),
            key=lambda item: (
                -int(item[1]["occurrence_count"]),
                -item[0][2],
                item[0][1] is None,
                item[0][0],
            ),
        )
        component_summaries = tuple(
            DecompositionComponentGroup(
                region_signature=component_key[0],
                component_macro_kind=component_key[1],
                cell_count=component_key[2],
                occurrence_count=int(component_group["occurrence_count"]),
                side_count=component_key[3],
                quantized_area_ratio=float(component_key[4]),
                marked_cell_signature=component_key[5],
                example_roots=tuple(sorted(int(root) for root in component_group["roots"])[:5]),
                example_subsets=tuple(component_group["subsets"]),
            )
            for component_key, component_group in sorted_components[:top_groups]
        )
        decomposition_groups.append(
            SupertileDecompositionGroup(
                seed_macro_kind=resolved_template.summary.seed_macro_kind,
                base_cell_count=resolved_template.summary.base_cell_count,
                candidate_cell_count=resolved_template.summary.candidate_cell_count,
                template_match_count=resolved_template.summary.template_match_count,
                line_equations=_line_equations_from_line_families(
                    resolved_template.summary.line_families
                ),
                component_groups=component_summaries,
                canonical_vertices=resolved_template.summary.canonical_vertices,
                marked_cell_signature=resolved_template.summary.marked_cell_signature,
                example_roots=resolved_template.summary.example_roots,
                example_subsets=resolved_template.summary.example_subsets,
            )
        )

    decomposition_groups.sort(
        key=lambda group: (
            -group.candidate_cell_count,
            -group.template_match_count,
            group.seed_macro_kind,
            group.marked_cell_signature,
        )
    )
    return tuple(decomposition_groups[:top_groups])


def mine_macro_composition_groups(
    cells: dict[int, SourceCell],
    grouped_macro_occurrences: dict[
        tuple[str, int, float, tuple[float, ...], tuple[int, ...]],
        list[tuple[tuple[int, ...], dict[str, Any]]],
    ],
    *,
    top_groups: int,
    max_combo_size: int = 4,
    component_support_ratio: float = 0.6,
) -> tuple[MacroCompositionCandidateGroup, ...]:
    polygons = {
        index: Polygon(cell.vertices)
        for index, cell in cells.items()
    }
    primitive_area = next(
        polygons[index].area
        for index, cell in cells.items()
        if cell.kind.endswith("square")
    )
    resolved_templates = _resolve_boundary_template_groups(
        cells,
        grouped_macro_occurrences,
        top_groups=top_groups,
    )

    composition_groups: dict[
        tuple[
            str,
            int,
            int,
            tuple[tuple[int, ...], ...],
            str,
            int,
            int,
            float,
            tuple[tuple[str, int], ...],
        ],
        dict[str, Any],
    ] = {}
    for resolved_template in resolved_templates:
        resolved_occurrences = _resolve_template_occurrences(
            cells,
            polygons,
            primitive_area=primitive_area,
            resolved_template=resolved_template,
        )
        if not resolved_occurrences:
            continue

        signature_occurrence_counts: Counter[tuple[int, ...]] = Counter()
        occurrence_components: list[
            tuple[_ResolvedInflationOccurrence, dict[tuple[int, ...], _ResolvedRegionComponent]]
        ] = []
        for resolved_occurrence in resolved_occurrences:
            components_by_signature: dict[tuple[int, ...], list[_ResolvedRegionComponent]] = defaultdict(list)
            for component in resolved_occurrence.components:
                components_by_signature[component.region_signature].append(component)
            unique_components = {
                region_signature: signature_components[0]
                for region_signature, signature_components in components_by_signature.items()
                if len(signature_components) == 1
            }
            occurrence_components.append((resolved_occurrence.occurrence, unique_components))
            for region_signature in unique_components:
                signature_occurrence_counts[region_signature] += 1

        support_threshold = max(
            2,
            math.ceil(len(occurrence_components) * component_support_ratio),
        )
        stable_signatures = sorted(
            region_signature
            for region_signature, count in signature_occurrence_counts.items()
            if count >= support_threshold
        )
        if len(stable_signatures) < 2:
            continue

        max_effective_combo_size = min(max_combo_size, len(stable_signatures))
        for combo_size in range(2, max_effective_combo_size + 1):
            for region_combo in combinations(stable_signatures, combo_size):
                for occurrence, unique_components in occurrence_components:
                    if any(region_signature not in unique_components for region_signature in region_combo):
                        continue
                    selected_components = [
                        unique_components[region_signature]
                        for region_signature in region_combo
                    ]
                    composed_subset = tuple(sorted({
                        cell_index
                        for component in selected_components
                        for cell_index in component.subset
                    }))
                    if len(composed_subset) <= max(len(component.subset) for component in selected_components):
                        continue
                    evaluated = _evaluate_subset(
                        frozenset(composed_subset),
                        polygons,
                        primitive_area=primitive_area,
                    )
                    if evaluated is None:
                        continue
                    _, metrics = evaluated
                    if metrics["macro_kind"] not in {"square", "triangle"}:
                        continue
                    marked_signature = tuple(sorted(
                        Counter(
                            _short_cell_signature(cells[index])
                            for index in composed_subset
                        ).items()
                    ))
                    group_key = (
                        resolved_template.summary.seed_macro_kind,
                        resolved_template.summary.base_cell_count,
                        resolved_template.summary.candidate_cell_count,
                        tuple(region_combo),
                        str(metrics["macro_kind"]),
                        len(composed_subset),
                        int(metrics["side_count"]),
                        round(float(metrics["area_ratio"]), 2),
                        marked_signature,
                    )
                    composition_group = composition_groups.setdefault(
                        group_key,
                        {
                            "template_match_count": resolved_template.summary.template_match_count,
                            "occurrence_count": 0,
                            "roots": set(),
                            "subsets": [],
                        },
                    )
                    composition_group["occurrence_count"] += 1
                    composition_group["roots"].update(occurrence.occurrence_roots)
                    if len(composition_group["subsets"]) < 3:
                        composition_group["subsets"].append(composed_subset)

    sorted_compositions = sorted(
        composition_groups.items(),
        key=lambda item: (
            -int(item[1]["occurrence_count"]),
            -item[0][5],
            item[0][4],
            item[0][3],
        ),
    )
    return tuple(
        MacroCompositionCandidateGroup(
            seed_macro_kind=group_key[0],
            base_cell_count=group_key[1],
            candidate_cell_count=group_key[2],
            template_match_count=int(group["template_match_count"]),
            component_region_signatures=group_key[3],
            composition_macro_kind=group_key[4],
            composed_cell_count=group_key[5],
            occurrence_count=int(group["occurrence_count"]),
            side_count=group_key[6],
            quantized_area_ratio=float(group_key[7]),
            marked_cell_signature=group_key[8],
            example_roots=tuple(sorted(int(root) for root in group["roots"])[:5]),
            example_subsets=tuple(group["subsets"]),
        )
        for group_key, group in sorted_compositions[:top_groups]
    )


def build_mining_summary(
    *,
    max_source_depth: int,
    neighborhood_radius: int,
    region_radius: int,
    max_candidate_size: int,
    min_candidate_size: int,
    beam_width: int,
    top_groups: int,
) -> MiningSummary:
    cells, seed_index = load_source_cells()
    shell_distances = compute_shell_distances(cells, seed_index)
    local_labels = classify_local_neighborhoods(cells, neighborhood_radius)
    local_neighborhood_classes = summarize_local_neighborhood_classes(
        cells,
        shell_distances,
        local_labels,
        max_source_depth=max_source_depth,
        top_groups=top_groups,
    )
    grouped_macro_occurrences = collect_macro_occurrences(
        cells,
        shell_distances,
        local_labels,
        max_source_depth=max_source_depth,
        region_radius=region_radius,
        max_candidate_size=max_candidate_size,
        min_candidate_size=min_candidate_size,
        beam_width=beam_width,
    )
    macro_candidate_groups = summarize_macro_occurrences(
        grouped_macro_occurrences,
        top_groups=top_groups,
    )
    seeded_supertile_groups = mine_seeded_supertile_groups(
        cells,
        grouped_macro_occurrences,
        top_groups=top_groups,
    )
    inflation_candidate_groups = mine_inflation_candidate_groups(
        cells,
        grouped_macro_occurrences,
        top_groups=top_groups,
    )
    boundary_template_groups = mine_boundary_template_groups(
        cells,
        grouped_macro_occurrences,
        top_groups=top_groups,
    )
    supertile_decomposition_groups = mine_supertile_decomposition_groups(
        cells,
        grouped_macro_occurrences,
        top_groups=top_groups,
    )
    macro_composition_groups = mine_macro_composition_groups(
        cells,
        grouped_macro_occurrences,
        top_groups=top_groups,
    )
    return MiningSummary(
        source_cell_count=len(cells),
        seed_index=seed_index,
        max_available_depth=max(shell_distances.values()),
        analyzed_root_count=sum(
            1
            for depth in shell_distances.values()
            if depth <= max_source_depth
        ),
        neighborhood_radius=neighborhood_radius,
        region_radius=region_radius,
        max_candidate_size=max_candidate_size,
        min_candidate_size=min_candidate_size,
        beam_width=beam_width,
        local_neighborhood_classes=local_neighborhood_classes,
        macro_candidate_groups=macro_candidate_groups,
        seeded_supertile_groups=seeded_supertile_groups,
        inflation_candidate_groups=inflation_candidate_groups,
        boundary_template_groups=boundary_template_groups,
        supertile_decomposition_groups=supertile_decomposition_groups,
        macro_composition_groups=macro_composition_groups,
    )


def summary_to_payload(summary: MiningSummary) -> dict[str, Any]:
    return {
        "source_cell_count": summary.source_cell_count,
        "seed_index": summary.seed_index,
        "max_available_depth": summary.max_available_depth,
        "analyzed_root_count": summary.analyzed_root_count,
        "neighborhood_radius": summary.neighborhood_radius,
        "region_radius": summary.region_radius,
        "max_candidate_size": summary.max_candidate_size,
        "min_candidate_size": summary.min_candidate_size,
        "beam_width": summary.beam_width,
        "local_neighborhood_classes": [asdict(item) for item in summary.local_neighborhood_classes],
        "macro_candidate_groups": [asdict(item) for item in summary.macro_candidate_groups],
        "seeded_supertile_groups": [asdict(item) for item in summary.seeded_supertile_groups],
        "inflation_candidate_groups": [asdict(item) for item in summary.inflation_candidate_groups],
        "boundary_template_groups": [asdict(item) for item in summary.boundary_template_groups],
        "supertile_decomposition_groups": [asdict(item) for item in summary.supertile_decomposition_groups],
        "macro_composition_groups": [asdict(item) for item in summary.macro_composition_groups],
    }


def render_text_report(summary: MiningSummary) -> str:
    lines = [
        "Dodecagonal Square-Triangle Structure Mining",
        (
            f"source_cells={summary.source_cell_count} seed_index={summary.seed_index} "
            f"max_available_depth={summary.max_available_depth} analyzed_roots={summary.analyzed_root_count}"
        ),
        (
            f"neighborhood_radius={summary.neighborhood_radius} region_radius={summary.region_radius} "
            f"max_candidate_size={summary.max_candidate_size} min_candidate_size={summary.min_candidate_size} "
            f"beam_width={summary.beam_width}"
        ),
        "",
        "Top Local Neighborhood Classes",
    ]
    if not summary.local_neighborhood_classes:
        lines.append("  none")
    for neighborhood_class in summary.local_neighborhood_classes:
        lines.extend([
            (
                f"  signature={neighborhood_class.signature} count={neighborhood_class.count} "
                f"kinds={dict(neighborhood_class.kind_counts)} depths={dict(neighborhood_class.depth_histogram)}"
            ),
            f"    example_cells={list(neighborhood_class.example_cells)}",
        ])

    lines.extend(["", "Macro Candidate Groups"])
    if not summary.macro_candidate_groups:
        lines.append("  none")
    for macro_group in summary.macro_candidate_groups:
        lines.extend([
            (
                f"  macro_kind={macro_group.macro_kind} occurrence_count={macro_group.occurrence_count} "
                f"cell_count={macro_group.cell_count} side_count={macro_group.side_count} "
                f"area_ratio≈{macro_group.quantized_area_ratio}"
            ),
            (
                f"    edge_signature={list(macro_group.edge_length_signature)} "
                f"angle_signature={list(macro_group.angle_signature)}"
            ),
            f"    root_signatures={dict(macro_group.root_signature_counts)}",
            f"    example_roots={list(macro_group.example_roots)}",
            f"    example_subsets={[list(subset) for subset in macro_group.example_subsets]}",
        ])

    lines.extend(["", "Seeded Supertile Groups"])
    if not summary.seeded_supertile_groups:
        lines.append("  none")
    for supertile_group in summary.seeded_supertile_groups:
        lines.extend([
            (
                f"  seed_macro_kind={supertile_group.seed_macro_kind} seed_cell_count={supertile_group.seed_cell_count} "
                f"grown_macro_kind={supertile_group.grown_macro_kind} grown_cell_count={supertile_group.grown_cell_count} "
                f"occurrence_count={supertile_group.occurrence_count} side_count={supertile_group.side_count} "
                f"area_ratio≈{supertile_group.quantized_area_ratio}"
            ),
            (
                f"    selected_slots={list(supertile_group.selected_slots)} "
                f"line_families={dict(supertile_group.boundary_direction_histogram)} "
                f"marked_cells={dict(supertile_group.marked_cell_signature)}"
            ),
            (
                f"    edge_signature={list(supertile_group.edge_length_signature)} "
                f"angle_signature={list(supertile_group.angle_signature)}"
            ),
            f"    example_roots={list(supertile_group.example_roots)}",
            f"    example_subsets={[list(subset) for subset in supertile_group.example_subsets]}",
        ])

    lines.extend(["", "Inflation Candidate Groups"])
    if not summary.inflation_candidate_groups:
        lines.append("  none")
    for inflation_group in summary.inflation_candidate_groups:
        lines.extend([
            (
                f"  seed_macro_kind={inflation_group.seed_macro_kind} base_cell_count={inflation_group.base_cell_count} "
                f"grown_macro_kind={inflation_group.grown_macro_kind} grown_cell_count={inflation_group.grown_cell_count} "
                f"occurrence_count={inflation_group.occurrence_count} combo_size={inflation_group.combo_size} "
                f"side_count={inflation_group.side_count} area_ratio≈{inflation_group.quantized_area_ratio} "
                f"inflation≈{inflation_group.inflation_estimate}"
            ),
            (
                f"    selected_slots={list(inflation_group.selected_slots)} "
                f"line_families={dict(inflation_group.boundary_direction_histogram)} "
                f"marked_cells={dict(inflation_group.marked_cell_signature)}"
            ),
            (
                f"    edge_signature={list(inflation_group.edge_length_signature)} "
                f"angle_signature={list(inflation_group.angle_signature)}"
            ),
            f"    example_roots={list(inflation_group.example_roots)}",
            f"    example_subsets={[list(subset) for subset in inflation_group.example_subsets]}",
        ])

    lines.extend(["", "Boundary Template Groups"])
    if not summary.boundary_template_groups:
        lines.append("  none")
    for template_group in summary.boundary_template_groups:
        lines.extend([
            (
                f"  seed_macro_kind={template_group.seed_macro_kind} base_cell_count={template_group.base_cell_count} "
                f"candidate_cell_count={template_group.candidate_cell_count} occurrence_count={template_group.occurrence_count} "
                f"template_match_count={template_group.template_match_count} template_variants={template_group.template_variant_count} "
                f"side_count={template_group.side_count} area_ratio≈{template_group.quantized_area_ratio} "
                f"inflation≈{template_group.inflation_estimate}"
            ),
            (
                f"    selected_slots={list(template_group.selected_slots)} "
                f"line_families="
                f"{ {family.axis_angle: list(family.offsets) for family in template_group.line_families} } "
                f"marked_cells={dict(template_group.marked_cell_signature)}"
            ),
            f"    canonical_vertices={list(template_group.canonical_vertices)}",
            f"    example_roots={list(template_group.example_roots)}",
            f"    example_subsets={[list(subset) for subset in template_group.example_subsets]}",
        ])

    lines.extend(["", "Supertile Decomposition Groups"])
    if not summary.supertile_decomposition_groups:
        lines.append("  none")
    for decomposition_group in summary.supertile_decomposition_groups:
        lines.extend([
            (
                f"  seed_macro_kind={decomposition_group.seed_macro_kind} "
                f"base_cell_count={decomposition_group.base_cell_count} "
                f"candidate_cell_count={decomposition_group.candidate_cell_count} "
                f"template_match_count={decomposition_group.template_match_count}"
            ),
            f"    line_equations={[equation.equation for equation in decomposition_group.line_equations]}",
            f"    canonical_vertices={list(decomposition_group.canonical_vertices)}",
        ])
        for component_group in decomposition_group.component_groups:
            lines.extend([
                (
                    f"    region_signature={list(component_group.region_signature)} "
                    f"macro_kind={component_group.component_macro_kind} "
                    f"cell_count={component_group.cell_count} "
                    f"occurrence_count={component_group.occurrence_count} "
                    f"side_count={component_group.side_count} "
                    f"area_ratio≈{component_group.quantized_area_ratio}"
                ),
                f"      marked_cells={dict(component_group.marked_cell_signature)}",
                f"      example_roots={list(component_group.example_roots)}",
                f"      example_subsets={[list(subset) for subset in component_group.example_subsets]}",
            ])

    lines.extend(["", "Macro Composition Groups"])
    if not summary.macro_composition_groups:
        lines.append("  none")
    for composition_group in summary.macro_composition_groups:
        lines.extend([
            (
                f"  seed_macro_kind={composition_group.seed_macro_kind} "
                f"base_cell_count={composition_group.base_cell_count} "
                f"candidate_cell_count={composition_group.candidate_cell_count} "
                f"template_match_count={composition_group.template_match_count} "
                f"composition_macro_kind={composition_group.composition_macro_kind} "
                f"composed_cell_count={composition_group.composed_cell_count} "
                f"occurrence_count={composition_group.occurrence_count} "
                f"side_count={composition_group.side_count} "
                f"area_ratio≈{composition_group.quantized_area_ratio}"
            ),
            f"    component_region_signatures={[list(signature) for signature in composition_group.component_region_signatures]}",
            f"    marked_cells={dict(composition_group.marked_cell_signature)}",
            f"    example_roots={list(composition_group.example_roots)}",
            f"    example_subsets={[list(subset) for subset in composition_group.example_subsets]}",
        ])
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Classify local neighborhoods, mine repeated square/triangle "
            "macro-candidates, grow seeded supertile candidates, and probe "
            "inflation-style expansions, boundary templates, decomposition "
            "components, and macro-composition candidates in the "
            "literature-derived dodecagonal source patch."
        )
    )
    parser.add_argument("--max-source-depth", type=int, default=8)
    parser.add_argument("--neighborhood-radius", type=int, default=2)
    parser.add_argument("--region-radius", type=int, default=3)
    parser.add_argument("--max-candidate-size", type=int, default=8)
    parser.add_argument("--min-candidate-size", type=int, default=2)
    parser.add_argument("--beam-width", type=int, default=20)
    parser.add_argument("--top-groups", type=int, default=10)
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = build_mining_summary(
        max_source_depth=args.max_source_depth,
        neighborhood_radius=args.neighborhood_radius,
        region_radius=args.region_radius,
        max_candidate_size=args.max_candidate_size,
        min_candidate_size=args.min_candidate_size,
        beam_width=args.beam_width,
        top_groups=args.top_groups,
    )
    if args.json_output:
        print(json.dumps(summary_to_payload(summary), indent=2, sort_keys=True))
    else:
        print(render_text_report(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
