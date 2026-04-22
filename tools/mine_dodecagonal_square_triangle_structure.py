from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

from tools.tiling_template_analysis import (
    BoundaryLineEquation,
    BoundaryLineFamily,
    ResolvedTemplateOccurrence as _ResolvedTemplateOccurrence,
    TemplateRegionComponent as _ResolvedRegionComponent,
    boundary_direction_histogram as _boundary_direction_histogram,
    build_polygon_context as _build_polygon_context,
    canonical_slot_key as _canonical_slot_key,
    canonicalize_boundary_template as _canonicalize_boundary_template,
    edge_angle as _edge_angle,
    evaluate_subset as _evaluate_subset,
    format_slot_key as _format_slot_key,
    line_equations_from_line_families as _line_equations_from_line_families,
    line_families_from_canonical_vertices as _line_families_from_canonical_vertices,
    merged_boundary as _merged_boundary,
    multi_source_ball as _multi_source_ball,
    normalize_point as _normalize_point,
    resolve_template_occurrences as _resolve_template_occurrences_shared,
    rotate_vertices as _rotate_vertices,
    snap_angle as _snap_angle,
    subset_frame as _subset_frame,
)


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
    canonical_vertices: tuple[tuple[float, float], ...]
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
class RecoveredRuleChild:
    component_region_signatures: tuple[tuple[int, ...], ...]
    macro_kind: str
    cell_count: int
    occurrence_count: int
    verified_occurrence_count: int
    marked_cell_signature: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class RecoveredSubstitutionRule:
    seed_macro_kind: str
    base_cell_count: int
    candidate_cell_count: int
    template_match_count: int
    canonical_vertices: tuple[tuple[float, float], ...]
    line_equations: tuple[BoundaryLineEquation, ...]
    child_rules: tuple[RecoveredRuleChild, ...]
    residual_region_signatures: tuple[tuple[int, ...], ...]
    verification_max_source_depth: int
    verified_template_match_count: int
    verified_child_rule_count: int
    verified_rule_ratio: float
    example_roots: tuple[int, ...]
    example_subsets: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class RecoveredParentPiece:
    piece_kind: str
    component_region_signatures: tuple[tuple[int, ...], ...]
    macro_kind: str
    cell_count: int
    occurrence_count: int
    verified_occurrence_count: int
    marked_cell_signature: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class RecoveredParentDecomposition:
    seed_macro_kind: str
    base_cell_count: int
    candidate_cell_count: int
    template_match_count: int
    canonical_vertices: tuple[tuple[float, float], ...]
    line_equations: tuple[BoundaryLineEquation, ...]
    child_pieces: tuple[RecoveredParentPiece, ...]
    covered_region_signatures: tuple[tuple[int, ...], ...]
    uncovered_region_signatures: tuple[tuple[int, ...], ...]
    coverage_ratio: float
    verification_max_source_depth: int
    verified_template_match_count: int
    verified_piece_count: int
    verified_piece_ratio: float
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
    recovered_substitution_rules: tuple[RecoveredSubstitutionRule, ...]
    recovered_parent_decompositions: tuple[RecoveredParentDecomposition, ...]


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
    polygons, primitive_area = _build_polygon_context(cells)

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
    polygons, primitive_area = _build_polygon_context(cells)

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
                    centroid=centroid,
                    orientation=orientation,
                    scale=scale,
                    macro_kind=seed_macro_kind,
                    polygon=polygons[candidate_index],
                    cell_signature=_short_cell_signature(cells[candidate_index]),
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
    polygons, primitive_area = _build_polygon_context(cells)

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
                    centroid=occurrence.centroid,
                    orientation=occurrence.orientation,
                    scale=occurrence.scale,
                    macro_kind=resolved_group.summary.seed_macro_kind,
                    polygon=polygons[candidate_index],
                    cell_signature=_short_cell_signature(cells[candidate_index]),
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
    polygons, _primitive_area = _build_polygon_context(cells)
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
    polygons: dict[int, Any],
    *,
    primitive_area: float,
    resolved_template: _ResolvedBoundaryTemplateGroup,
) -> tuple[_ResolvedTemplateOccurrence, ...]:
    return _resolve_template_occurrences_shared(
        cells,
        polygons,
        primitive_area=primitive_area,
        line_families=resolved_template.summary.line_families,
        matched_occurrences=resolved_template.matched_occurrences,
        describe_cell=_short_cell_signature,
    )


def mine_supertile_decomposition_groups(
    cells: dict[int, SourceCell],
    grouped_macro_occurrences: dict[
        tuple[str, int, float, tuple[float, ...], tuple[int, ...]],
        list[tuple[tuple[int, ...], dict[str, Any]]],
    ],
    *,
    top_groups: int,
) -> tuple[SupertileDecompositionGroup, ...]:
    polygons, primitive_area = _build_polygon_context(cells)
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
    polygons, primitive_area = _build_polygon_context(cells)
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
            tuple[tuple[float, float], ...],
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
                        resolved_template.summary.canonical_vertices,
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
            -item[0][6],
            item[0][5],
            item[0][4],
        ),
    )
    return tuple(
        MacroCompositionCandidateGroup(
            seed_macro_kind=group_key[0],
            base_cell_count=group_key[1],
            candidate_cell_count=group_key[2],
            template_match_count=int(group["template_match_count"]),
            canonical_vertices=group_key[3],
            component_region_signatures=group_key[4],
            composition_macro_kind=group_key[5],
            composed_cell_count=group_key[6],
            occurrence_count=int(group["occurrence_count"]),
            side_count=group_key[7],
            quantized_area_ratio=float(group_key[8]),
            marked_cell_signature=group_key[9],
            example_roots=tuple(sorted(int(root) for root in group["roots"])[:5]),
            example_subsets=tuple(group["subsets"]),
        )
        for group_key, group in sorted_compositions[:top_groups]
    )


def recover_substitution_rules(
    *,
    decomposition_groups: tuple[SupertileDecompositionGroup, ...],
    macro_composition_groups: tuple[MacroCompositionCandidateGroup, ...],
    verification_boundary_templates: tuple[BoundaryTemplateGroup, ...],
    verification_macro_composition_groups: tuple[MacroCompositionCandidateGroup, ...],
    verification_max_source_depth: int,
    top_groups: int,
) -> tuple[RecoveredSubstitutionRule, ...]:
    composition_by_template: dict[
        tuple[str, int, tuple[tuple[float, float], ...]],
        list[MacroCompositionCandidateGroup],
    ] = defaultdict(list)
    for group in macro_composition_groups:
        composition_by_template[(
            group.seed_macro_kind,
            group.candidate_cell_count,
            group.canonical_vertices,
        )].append(group)

    verified_template_counts: dict[
        tuple[str, int, tuple[tuple[float, float], ...]],
        int,
    ] = {}
    for template in verification_boundary_templates:
        template_key = (
            template.seed_macro_kind,
            template.candidate_cell_count,
            template.canonical_vertices,
        )
        verified_template_counts[template_key] = max(
            verified_template_counts.get(template_key, 0),
            template.template_match_count,
        )

    verified_composition_counts: dict[
        tuple[
            tuple[str, int, tuple[tuple[float, float], ...]],
            tuple[tuple[int, ...], ...],
            str,
            int,
            tuple[tuple[str, int], ...],
        ],
        int,
    ] = {}
    for group in verification_macro_composition_groups:
        template_key = (
            group.seed_macro_kind,
            group.candidate_cell_count,
            group.canonical_vertices,
        )
        composition_key = (
            template_key,
            group.component_region_signatures,
            group.composition_macro_kind,
            group.composed_cell_count,
            group.marked_cell_signature,
        )
        verified_composition_counts[composition_key] = max(
            verified_composition_counts.get(composition_key, 0),
            group.occurrence_count,
        )

    recovered_rules: list[RecoveredSubstitutionRule] = []
    for decomposition_group in decomposition_groups:
        template_key = (
            decomposition_group.seed_macro_kind,
            decomposition_group.candidate_cell_count,
            decomposition_group.canonical_vertices,
        )
        candidate_children = sorted(
            composition_by_template.get(template_key, []),
            key=lambda group: (
                -group.occurrence_count,
                -group.composed_cell_count,
                group.component_region_signatures,
            ),
        )
        if not candidate_children:
            continue

        selected_children: list[RecoveredRuleChild] = []
        covered_region_signatures: set[tuple[int, ...]] = set()
        for child in candidate_children:
            child_signatures = set(child.component_region_signatures)
            if child_signatures & covered_region_signatures:
                continue
            covered_region_signatures.update(child_signatures)
            verification_key = (
                template_key,
                child.component_region_signatures,
                child.composition_macro_kind,
                child.composed_cell_count,
                child.marked_cell_signature,
            )
            selected_children.append(
                RecoveredRuleChild(
                    component_region_signatures=child.component_region_signatures,
                    macro_kind=child.composition_macro_kind,
                    cell_count=child.composed_cell_count,
                    occurrence_count=child.occurrence_count,
                    verified_occurrence_count=verified_composition_counts.get(verification_key, 0),
                    marked_cell_signature=child.marked_cell_signature,
                )
            )

        if not selected_children:
            continue

        residual_region_signatures = tuple(sorted(
            component.region_signature
            for component in decomposition_group.component_groups
            if component.region_signature not in covered_region_signatures
        ))
        verified_template_match_count = verified_template_counts.get(template_key, 0)
        verified_child_rule_count = sum(
            1
            for child in selected_children
            if child.verified_occurrence_count > 0
        )
        verified_rule_ratio = round(
            verified_child_rule_count / len(selected_children),
            2,
        )
        recovered_rules.append(
            RecoveredSubstitutionRule(
                seed_macro_kind=decomposition_group.seed_macro_kind,
                base_cell_count=decomposition_group.base_cell_count,
                candidate_cell_count=decomposition_group.candidate_cell_count,
                template_match_count=decomposition_group.template_match_count,
                canonical_vertices=decomposition_group.canonical_vertices,
                line_equations=decomposition_group.line_equations,
                child_rules=tuple(selected_children),
                residual_region_signatures=residual_region_signatures,
                verification_max_source_depth=verification_max_source_depth,
                verified_template_match_count=verified_template_match_count,
                verified_child_rule_count=verified_child_rule_count,
                verified_rule_ratio=verified_rule_ratio,
                example_roots=decomposition_group.example_roots,
                example_subsets=decomposition_group.example_subsets,
            )
        )

    recovered_rules.sort(
        key=lambda rule: (
            -rule.verified_child_rule_count,
            -rule.verified_template_match_count,
            -len(rule.child_rules),
            -rule.candidate_cell_count,
        )
    )
    return tuple(recovered_rules[:top_groups])


def _template_key(
    *,
    seed_macro_kind: str,
    candidate_cell_count: int,
    canonical_vertices: tuple[tuple[float, float], ...],
) -> tuple[str, int, tuple[tuple[float, float], ...]]:
    return (seed_macro_kind, candidate_cell_count, canonical_vertices)


def _component_verification_key(
    *,
    template_key: tuple[str, int, tuple[tuple[float, float], ...]],
    component: DecompositionComponentGroup,
) -> tuple[
    tuple[str, int, tuple[tuple[float, float], ...]],
    tuple[int, ...],
    str | None,
    int,
    tuple[tuple[str, int], ...],
]:
    return (
        template_key,
        component.region_signature,
        component.component_macro_kind,
        component.cell_count,
        component.marked_cell_signature,
    )


def recover_parent_decompositions(
    *,
    decomposition_groups: tuple[SupertileDecompositionGroup, ...],
    recovered_rules: tuple[RecoveredSubstitutionRule, ...],
    verification_decomposition_groups: tuple[SupertileDecompositionGroup, ...],
    verification_max_source_depth: int,
    top_groups: int,
) -> tuple[RecoveredParentDecomposition, ...]:
    decomposition_by_template = {
        _template_key(
            seed_macro_kind=group.seed_macro_kind,
            candidate_cell_count=group.candidate_cell_count,
            canonical_vertices=group.canonical_vertices,
        ): group
        for group in decomposition_groups
    }
    verified_template_counts: dict[
        tuple[str, int, tuple[tuple[float, float], ...]],
        int,
    ] = {}
    verified_component_counts: dict[
        tuple[
            tuple[str, int, tuple[tuple[float, float], ...]],
            tuple[int, ...],
            str | None,
            int,
            tuple[tuple[str, int], ...],
        ],
        int,
    ] = {}
    for group in verification_decomposition_groups:
        template_key = _template_key(
            seed_macro_kind=group.seed_macro_kind,
            candidate_cell_count=group.candidate_cell_count,
            canonical_vertices=group.canonical_vertices,
        )
        verified_template_counts[template_key] = max(
            verified_template_counts.get(template_key, 0),
            group.template_match_count,
        )
        for component in group.component_groups:
            verification_key = _component_verification_key(
                template_key=template_key,
                component=component,
            )
            verified_component_counts[verification_key] = max(
                verified_component_counts.get(verification_key, 0),
                component.occurrence_count,
            )

    recovered_decompositions: list[RecoveredParentDecomposition] = []
    for rule in recovered_rules:
        template_key = _template_key(
            seed_macro_kind=rule.seed_macro_kind,
            candidate_cell_count=rule.candidate_cell_count,
            canonical_vertices=rule.canonical_vertices,
        )
        decomposition_group = decomposition_by_template.get(template_key)
        if decomposition_group is None:
            continue

        covered_region_signatures: set[tuple[int, ...]] = set()
        child_pieces: list[RecoveredParentPiece] = []
        for child_rule in sorted(
            rule.child_rules,
            key=lambda child: (
                -child.verified_occurrence_count,
                -child.occurrence_count,
                -child.cell_count,
                child.component_region_signatures,
            ),
        ):
            child_signatures = set(child_rule.component_region_signatures)
            if child_signatures & covered_region_signatures:
                continue
            covered_region_signatures.update(child_signatures)
            child_pieces.append(
                RecoveredParentPiece(
                    piece_kind="composition",
                    component_region_signatures=child_rule.component_region_signatures,
                    macro_kind=child_rule.macro_kind,
                    cell_count=child_rule.cell_count,
                    occurrence_count=child_rule.occurrence_count,
                    verified_occurrence_count=child_rule.verified_occurrence_count,
                    marked_cell_signature=child_rule.marked_cell_signature,
                )
            )

        singleton_candidates = sorted(
            (
                component
                for component in decomposition_group.component_groups
                if component.component_macro_kind in {"square", "triangle"}
            ),
            key=lambda component: (
                -(component.occurrence_count),
                -(component.cell_count),
                component.component_macro_kind,
                component.region_signature,
            ),
        )
        for component in singleton_candidates:
            if component.region_signature in covered_region_signatures:
                continue
            covered_region_signatures.add(component.region_signature)
            verification_key = _component_verification_key(
                template_key=template_key,
                component=component,
            )
            child_pieces.append(
                RecoveredParentPiece(
                    piece_kind="component",
                    component_region_signatures=(component.region_signature,),
                    macro_kind=str(component.component_macro_kind),
                    cell_count=component.cell_count,
                    occurrence_count=component.occurrence_count,
                    verified_occurrence_count=verified_component_counts.get(verification_key, 0),
                    marked_cell_signature=component.marked_cell_signature,
                )
            )

        total_region_signatures = tuple(sorted({
            component.region_signature
            for component in decomposition_group.component_groups
        }))
        uncovered_region_signatures = tuple(
            region_signature
            for region_signature in total_region_signatures
            if region_signature not in covered_region_signatures
        )
        coverage_ratio = round(
            len(covered_region_signatures) / len(total_region_signatures),
            2,
        ) if total_region_signatures else 0.0
        verified_piece_count = sum(
            1
            for piece in child_pieces
            if piece.verified_occurrence_count > 0
        )
        verified_piece_ratio = round(
            verified_piece_count / len(child_pieces),
            2,
        ) if child_pieces else 0.0
        recovered_decompositions.append(
            RecoveredParentDecomposition(
                seed_macro_kind=rule.seed_macro_kind,
                base_cell_count=rule.base_cell_count,
                candidate_cell_count=rule.candidate_cell_count,
                template_match_count=rule.template_match_count,
                canonical_vertices=rule.canonical_vertices,
                line_equations=rule.line_equations,
                child_pieces=tuple(child_pieces),
                covered_region_signatures=tuple(sorted(covered_region_signatures)),
                uncovered_region_signatures=uncovered_region_signatures,
                coverage_ratio=coverage_ratio,
                verification_max_source_depth=verification_max_source_depth,
                verified_template_match_count=verified_template_counts.get(template_key, 0),
                verified_piece_count=verified_piece_count,
                verified_piece_ratio=verified_piece_ratio,
                example_roots=rule.example_roots,
                example_subsets=rule.example_subsets,
            )
        )

    recovered_decompositions.sort(
        key=lambda decomposition: (
            -decomposition.coverage_ratio,
            -decomposition.verified_piece_count,
            -decomposition.verified_template_match_count,
            -decomposition.candidate_cell_count,
        )
    )
    return tuple(recovered_decompositions[:top_groups])


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
    max_available_depth = max(shell_distances.values())
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
    rule_recovery_top_groups = max(top_groups * 3, 10)
    if rule_recovery_top_groups > top_groups:
        rule_recovery_decomposition_groups = mine_supertile_decomposition_groups(
            cells,
            grouped_macro_occurrences,
            top_groups=rule_recovery_top_groups,
        )
        rule_recovery_macro_composition_groups = mine_macro_composition_groups(
            cells,
            grouped_macro_occurrences,
            top_groups=rule_recovery_top_groups,
        )
    else:
        rule_recovery_decomposition_groups = supertile_decomposition_groups
        rule_recovery_macro_composition_groups = macro_composition_groups
    verification_max_source_depth = min(max_source_depth + 2, max_available_depth)
    if verification_max_source_depth > max_source_depth:
        verification_grouped_macro_occurrences = collect_macro_occurrences(
            cells,
            shell_distances,
            local_labels,
            max_source_depth=verification_max_source_depth,
            region_radius=region_radius,
            max_candidate_size=max_candidate_size,
            min_candidate_size=min_candidate_size,
            beam_width=beam_width,
        )
    else:
        verification_grouped_macro_occurrences = grouped_macro_occurrences
    verification_top_groups = max(top_groups * 3, top_groups)
    verification_boundary_templates = mine_boundary_template_groups(
        cells,
        verification_grouped_macro_occurrences,
        top_groups=verification_top_groups,
    )
    verification_decomposition_groups = mine_supertile_decomposition_groups(
        cells,
        verification_grouped_macro_occurrences,
        top_groups=verification_top_groups,
    )
    verification_macro_composition_groups = mine_macro_composition_groups(
        cells,
        verification_grouped_macro_occurrences,
        top_groups=verification_top_groups,
    )
    recovered_substitution_rules = recover_substitution_rules(
        decomposition_groups=rule_recovery_decomposition_groups,
        macro_composition_groups=rule_recovery_macro_composition_groups,
        verification_boundary_templates=verification_boundary_templates,
        verification_macro_composition_groups=verification_macro_composition_groups,
        verification_max_source_depth=verification_max_source_depth,
        top_groups=top_groups,
    )
    recovered_parent_decompositions = recover_parent_decompositions(
        decomposition_groups=rule_recovery_decomposition_groups,
        recovered_rules=recovered_substitution_rules,
        verification_decomposition_groups=verification_decomposition_groups,
        verification_max_source_depth=verification_max_source_depth,
        top_groups=top_groups,
    )
    return MiningSummary(
        source_cell_count=len(cells),
        seed_index=seed_index,
        max_available_depth=max_available_depth,
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
        recovered_substitution_rules=recovered_substitution_rules,
        recovered_parent_decompositions=recovered_parent_decompositions,
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
        "recovered_substitution_rules": [asdict(item) for item in summary.recovered_substitution_rules],
        "recovered_parent_decompositions": [asdict(item) for item in summary.recovered_parent_decompositions],
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

    lines.extend(["", "Recovered Substitution Rules"])
    if not summary.recovered_substitution_rules:
        lines.append("  none")
    for rule in summary.recovered_substitution_rules:
        lines.extend([
            (
                f"  seed_macro_kind={rule.seed_macro_kind} "
                f"base_cell_count={rule.base_cell_count} "
                f"candidate_cell_count={rule.candidate_cell_count} "
                f"template_match_count={rule.template_match_count} "
                f"verified_template_match_count={rule.verified_template_match_count} "
                f"verified_child_rule_count={rule.verified_child_rule_count} "
                f"verified_rule_ratio={rule.verified_rule_ratio}"
            ),
            f"    line_equations={[equation.equation for equation in rule.line_equations]}",
            f"    residual_region_signatures={[list(signature) for signature in rule.residual_region_signatures]}",
            f"    verification_max_source_depth={rule.verification_max_source_depth}",
            f"    example_roots={list(rule.example_roots)}",
            f"    example_subsets={[list(subset) for subset in rule.example_subsets]}",
        ])
        for child_rule in rule.child_rules:
            lines.extend([
                (
                    f"    child_macro_kind={child_rule.macro_kind} "
                    f"cell_count={child_rule.cell_count} "
                    f"occurrence_count={child_rule.occurrence_count} "
                    f"verified_occurrence_count={child_rule.verified_occurrence_count}"
                ),
                f"      component_region_signatures={[list(signature) for signature in child_rule.component_region_signatures]}",
                f"      marked_cells={dict(child_rule.marked_cell_signature)}",
            ])

    lines.extend(["", "Recovered Parent Decompositions"])
    if not summary.recovered_parent_decompositions:
        lines.append("  none")
    for decomposition in summary.recovered_parent_decompositions:
        lines.extend([
            (
                f"  seed_macro_kind={decomposition.seed_macro_kind} "
                f"base_cell_count={decomposition.base_cell_count} "
                f"candidate_cell_count={decomposition.candidate_cell_count} "
                f"template_match_count={decomposition.template_match_count} "
                f"verified_template_match_count={decomposition.verified_template_match_count} "
                f"coverage_ratio={decomposition.coverage_ratio} "
                f"verified_piece_count={decomposition.verified_piece_count} "
                f"verified_piece_ratio={decomposition.verified_piece_ratio}"
            ),
            f"    covered_region_signatures={[list(signature) for signature in decomposition.covered_region_signatures]}",
            f"    uncovered_region_signatures={[list(signature) for signature in decomposition.uncovered_region_signatures]}",
            f"    verification_max_source_depth={decomposition.verification_max_source_depth}",
            f"    example_roots={list(decomposition.example_roots)}",
            f"    example_subsets={[list(subset) for subset in decomposition.example_subsets]}",
        ])
        for piece in decomposition.child_pieces:
            lines.extend([
                (
                    f"    piece_kind={piece.piece_kind} "
                    f"macro_kind={piece.macro_kind} "
                    f"cell_count={piece.cell_count} "
                    f"occurrence_count={piece.occurrence_count} "
                    f"verified_occurrence_count={piece.verified_occurrence_count}"
                ),
                f"      component_region_signatures={[list(signature) for signature in piece.component_region_signatures]}",
                f"      marked_cells={dict(piece.marked_cell_signature)}",
            ])
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Classify local neighborhoods, mine repeated square/triangle "
            "macro-candidates, grow seeded supertile candidates, and probe "
            "inflation-style expansions, boundary templates, decomposition "
            "components, macro-composition candidates, and recovered "
            "substitution-style rules in the literature-derived "
            "dodecagonal source patch."
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
