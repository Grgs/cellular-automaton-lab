from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass
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
    marked_cell_signature: tuple[tuple[str, int], ...]
    edge_length_signature: tuple[float, ...]
    angle_signature: tuple[int, ...]
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

    summaries: list[SeededSupertileGroup] = []
    candidate_group_limit = max(top_groups * 3, top_groups)
    for group_key, members in sorted_seed_groups[:candidate_group_limit]:
        seed_macro_kind, seed_cell_count, _, _, _ = group_key
        if seed_macro_kind not in {"square", "triangle"}:
            continue
        if seed_cell_count > max_seed_cell_count:
            continue
        if len(members) < 3:
            continue
        if len(summaries) >= max_seed_groups:
            break

        slot_occurrence_counts: Counter[tuple[float, float, str]] = Counter()
        per_occurrence_slots: list[
            tuple[tuple[int, ...], tuple[int, ...], dict[tuple[float, float, str], list[int]]]
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
        for subset_key, occurrence_roots, slot_to_cells in per_occurrence_slots:
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
                },
            )
            grown_group["occurrence_count"] += 1
            grown_group["roots"].update(occurrence_roots)
            if len(grown_group["subsets"]) < 3:
                grown_group["subsets"].append(grown_tuple)

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
        summaries.append(
            SeededSupertileGroup(
                seed_macro_kind=seed_macro_kind,
                seed_cell_count=seed_cell_count,
                grown_macro_kind=grown_macro_kind,
                grown_cell_count=grown_cell_count,
                occurrence_count=int(best_group["occurrence_count"]),
                side_count=int(best_group["side_count"]),
                quantized_area_ratio=float(quantized_area_ratio),
                selected_slot_count=len(selected_slots),
                selected_slots=tuple(sorted(_format_slot_key(slot_key) for slot_key in selected_slots)),
                marked_cell_signature=marked_signature,
                edge_length_signature=tuple(float(value) for value in best_group["edge_length_signature"]),
                angle_signature=tuple(int(value) for value in best_group["angle_signature"]),
                example_roots=tuple(sorted(int(root) for root in best_group["roots"])[:5]),
                example_subsets=tuple(best_group["subsets"]),
            )
        )

    summaries.sort(
        key=lambda summary: (
            -summary.occurrence_count,
            -summary.grown_cell_count,
            summary.seed_macro_kind,
            summary.marked_cell_signature,
        )
    )
    return tuple(summaries[:top_groups])


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
                f"marked_cells={dict(supertile_group.marked_cell_signature)}"
            ),
            (
                f"    edge_signature={list(supertile_group.edge_length_signature)} "
                f"angle_signature={list(supertile_group.angle_signature)}"
            ),
            f"    example_roots={list(supertile_group.example_roots)}",
            f"    example_subsets={[list(subset) for subset in supertile_group.example_subsets]}",
        ])
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Classify local neighborhoods, mine repeated square/triangle "
            "macro-candidates, and grow seeded supertile candidates in the "
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
