from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha1
from importlib import import_module
import json
import math
import re
from typing import Literal

import networkx as nx

from backend.simulation.aperiodic_prototiles import build_aperiodic_patch
from backend.simulation.aperiodic_support import AperiodicPatch
from backend.simulation.literature_reference_specs import (
    REFERENCE_FAMILY_SPECS,
    STAGED_REFERENCE_WAIVERS,
    BuilderSignalExpectation,
    MetadataRequirement,
    PeriodicDescriptorExpectation,
    ReferenceDepthExpectation,
    ReferenceFamilySpec,
)
from backend.simulation.periodic_face_tilings import (
    PeriodicFaceCell,
    PeriodicFaceTilingDescriptor,
    get_periodic_face_tiling_descriptor,
    is_periodic_face_tiling,
)
from backend.simulation.topology import build_topology
from backend.simulation.topology_types import LatticeCell, LatticeTopology
from backend.simulation.topology_validation import build_topology_graph


VerificationStatus = Literal["PASS", "KNOWN_DEVIATION", "FAIL"]
_FLOAT_TOLERANCE = 1e-6


@dataclass(frozen=True)
class ReferenceCheckFailure:
    code: str
    message: str
    depth: int | None = None


@dataclass(frozen=True)
class ReferencePatchObservation:
    geometry: str
    sample_mode: str
    depth: int
    total_cells: int
    kind_counts: tuple[tuple[str, int], ...]
    degree_histogram: tuple[tuple[int, int], ...]
    connected_component_count: int
    disconnected_component_sizes: tuple[int, ...]
    largest_component_size: int
    isolated_cell_count: int
    unique_orientation_tokens: int
    unique_chirality_tokens: int
    chirality_adjacency_pairs: tuple[tuple[str, str], ...]
    three_opposite_chirality_neighbor_cells: int
    unique_polygon_areas_by_kind: tuple[tuple[str, int], ...]
    unique_decoration_variants_by_kind: tuple[tuple[str, int], ...]
    adjacency_pairs: tuple[tuple[str, str], ...]
    bounds_width: float
    bounds_height: float
    bounds_longest_span: float
    bounds_aspect_ratio: float
    signature: str


@dataclass(frozen=True)
class ReferenceVerificationResult:
    geometry: str
    display_name: str
    status: VerificationStatus
    blocking: bool
    waived: bool
    source_urls: tuple[str, ...]
    observations: tuple[ReferencePatchObservation, ...]
    failures: tuple[ReferenceCheckFailure, ...]

    @property
    def is_success(self) -> bool:
        return self.status != "FAIL"


def _topology_adjacency_pairs(topology: LatticeTopology) -> tuple[tuple[str, str], ...]:
    by_id = {cell.id: cell for cell in topology.cells}
    pairs: set[tuple[str, str]] = set()
    for cell in topology.cells:
        for neighbor_id in cell.neighbors:
            if neighbor_id not in by_id:
                continue
            left = cell.kind
            right = by_id[neighbor_id].kind
            pairs.add((left, right) if left <= right else (right, left))
    return tuple(sorted(pairs))


def _cells_bounds_aspect_ratio(cells: tuple[LatticeCell, ...]) -> float:
    all_x = [vertex[0] for cell in cells if cell.vertices is not None for vertex in cell.vertices]
    all_y = [vertex[1] for cell in cells if cell.vertices is not None for vertex in cell.vertices]
    if not all_x or not all_y:
        return 0.0
    width = max(all_x) - min(all_x)
    height = max(all_y) - min(all_y)
    shortest = min(width, height)
    if shortest <= 0.0:
        return float("inf")
    return max(width, height) / shortest


def _cells_bounds(cells: tuple[LatticeCell, ...]) -> tuple[float, float]:
    all_x = [vertex[0] for cell in cells if cell.vertices is not None for vertex in cell.vertices]
    all_y = [vertex[1] for cell in cells if cell.vertices is not None for vertex in cell.vertices]
    if not all_x or not all_y:
        return (0.0, 0.0)
    return (max(all_x) - min(all_x), max(all_y) - min(all_y))


def _topology_connectivity_stats(topology: LatticeTopology) -> tuple[int, tuple[int, ...], int, int]:
    graph = build_topology_graph(topology)
    if graph.number_of_nodes() == 0:
        return (0, (), 0, 0)
    component_sizes = tuple(
        sorted((len(component) for component in nx.connected_components(graph)), reverse=True)
    )
    largest_component_size = component_sizes[0] if component_sizes else 0
    isolated_cell_count = sum(1 for size in component_sizes if size == 1)
    disconnected_component_sizes = component_sizes if len(component_sizes) > 1 else ()
    return (
        len(component_sizes),
        disconnected_component_sizes,
        largest_component_size,
        isolated_cell_count,
    )


def _component_size_summary(component_sizes: tuple[int, ...], *, limit: int = 12) -> str:
    if not component_sizes:
        return "()"
    if len(component_sizes) <= limit:
        return repr(component_sizes)
    preview = ", ".join(str(size) for size in component_sizes[:limit])
    return f"({preview}, ...)"


def _polygon_area(vertices: tuple[tuple[float, float], ...]) -> float:
    total = 0.0
    for index, (x1, y1) in enumerate(vertices):
        x2, y2 = vertices[(index + 1) % len(vertices)]
        total += (x1 * y2) - (x2 * y1)
    return abs(total) / 2.0


def _topology_signature_payload(
    geometry: str,
    sample_mode: str,
    sample_key: int,
    topology: LatticeTopology,
) -> dict[str, object]:
    kind_counts = Counter(cell.kind for cell in topology.cells)
    orientation_counts = Counter(
        cell.orientation_token
        for cell in topology.cells
        if cell.orientation_token is not None
    )
    chirality_counts = Counter(
        cell.chirality_token
        for cell in topology.cells
        if cell.chirality_token is not None
    )
    degree_histogram = Counter(
        sum(1 for neighbor_id in cell.neighbors if neighbor_id is not None)
        for cell in topology.cells
    )
    return {
        "geometry": geometry,
        "sample_mode": sample_mode,
        "sample_key": sample_key,
        "kind_counts": sorted(kind_counts.items()),
        "orientation_counts": sorted(orientation_counts.items()),
        "chirality_counts": sorted(chirality_counts.items()),
        "adjacency_pairs": _topology_adjacency_pairs(topology),
        "degree_histogram": sorted(degree_histogram.items()),
        "bounds_aspect_ratio": round(_cells_bounds_aspect_ratio(topology.cells), 6),
    }


def _topology_signature(
    geometry: str,
    sample_mode: str,
    sample_key: int,
    topology: LatticeTopology,
) -> str:
    digest = sha1(
        json.dumps(
            _topology_signature_payload(geometry, sample_mode, sample_key, topology),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    return digest[:12]


def _build_reference_topology(spec: ReferenceFamilySpec, sample_key: int) -> LatticeTopology:
    if spec.sample_mode == "grid":
        return build_topology(spec.geometry, sample_key, sample_key, None)
    return build_topology(spec.geometry, 0, 0, sample_key)


def observe_reference_patch(geometry: str, depth: int) -> ReferencePatchObservation:
    spec = REFERENCE_FAMILY_SPECS[geometry]
    topology = _build_reference_topology(spec, depth)
    kind_counts = Counter(cell.kind for cell in topology.cells)
    area_classes_by_kind: dict[str, set[float]] = {}
    decoration_variants_by_kind: dict[str, set[tuple[str, ...]]] = {}
    chirality_adjacency_pairs: set[tuple[str, str]] = set()
    three_opposite_chirality_neighbor_cells = 0
    by_id = {cell.id: cell for cell in topology.cells}
    for cell in topology.cells:
        if cell.vertices is not None:
            area_classes_by_kind.setdefault(cell.kind, set()).add(round(_polygon_area(cell.vertices), 6))
        if cell.decoration_tokens is not None:
            decoration_variants_by_kind.setdefault(cell.kind, set()).add(tuple(cell.decoration_tokens))
        neighbor_chiralities = []
        for neighbor_id in cell.neighbors:
            if neighbor_id is None or cell.chirality_token is None:
                continue
            neighbor = by_id[neighbor_id]
            if neighbor.chirality_token is None:
                continue
            left = cell.chirality_token
            right = neighbor.chirality_token
            chirality_adjacency_pairs.add((left, right) if left <= right else (right, left))
            neighbor_chiralities.append(neighbor.chirality_token)
        if (
            cell.chirality_token is not None
            and len(neighbor_chiralities) == 3
            and all(chirality != cell.chirality_token for chirality in neighbor_chiralities)
        ):
            three_opposite_chirality_neighbor_cells += 1
    degree_histogram = Counter(
        sum(1 for neighbor_id in cell.neighbors if neighbor_id is not None)
        for cell in topology.cells
    )
    (
        connected_component_count,
        disconnected_component_sizes,
        largest_component_size,
        isolated_cell_count,
    ) = _topology_connectivity_stats(topology)
    unique_orientation_tokens = len(
        {
            cell.orientation_token
            for cell in topology.cells
            if cell.orientation_token is not None
        }
    )
    unique_chirality_tokens = len(
        {
            cell.chirality_token
            for cell in topology.cells
            if cell.chirality_token is not None
        }
    )
    bounds_width, bounds_height = _cells_bounds(topology.cells)
    return ReferencePatchObservation(
        geometry=geometry,
        sample_mode=spec.sample_mode,
        depth=int(depth),
        total_cells=len(topology.cells),
        kind_counts=tuple(sorted(kind_counts.items())),
        degree_histogram=tuple(sorted(degree_histogram.items())),
        connected_component_count=connected_component_count,
        disconnected_component_sizes=disconnected_component_sizes,
        largest_component_size=largest_component_size,
        isolated_cell_count=isolated_cell_count,
        unique_orientation_tokens=unique_orientation_tokens,
        unique_chirality_tokens=unique_chirality_tokens,
        chirality_adjacency_pairs=tuple(sorted(chirality_adjacency_pairs)),
        three_opposite_chirality_neighbor_cells=three_opposite_chirality_neighbor_cells,
        unique_polygon_areas_by_kind=tuple(
            sorted((kind, len(area_classes)) for kind, area_classes in area_classes_by_kind.items())
        ),
        unique_decoration_variants_by_kind=tuple(
            sorted((kind, len(variants)) for kind, variants in decoration_variants_by_kind.items())
        ),
        adjacency_pairs=_topology_adjacency_pairs(topology),
        bounds_width=round(bounds_width, 6),
        bounds_height=round(bounds_height, 6),
        bounds_longest_span=round(max(bounds_width, bounds_height), 6),
        bounds_aspect_ratio=round(_cells_bounds_aspect_ratio(topology.cells), 6),
        signature=_topology_signature(geometry, spec.sample_mode, depth, topology),
    )


def _metadata_failures(
    topology: LatticeTopology,
    requirement: MetadataRequirement,
) -> list[ReferenceCheckFailure]:
    failures: list[ReferenceCheckFailure] = []
    matching_cells = [cell for cell in topology.cells if cell.kind == requirement.kind]
    if not matching_cells:
        failures.append(
            ReferenceCheckFailure(
                code="missing-kind",
                message=f"Required kind '{requirement.kind}' is absent from the patch.",
            )
        )
        return failures
    for field_name in requirement.fields:
        if any(getattr(cell, field_name) is None for cell in matching_cells):
            failures.append(
                ReferenceCheckFailure(
                    code="missing-metadata",
                    message=f"Cells of kind '{requirement.kind}' are missing required metadata field '{field_name}'.",
                )
            )
    return failures


def _expectation_failures(
    observation: ReferencePatchObservation,
    expectation: ReferenceDepthExpectation,
) -> list[ReferenceCheckFailure]:
    failures: list[ReferenceCheckFailure] = []
    kind_counts = dict(observation.kind_counts)
    degree_histogram = dict(observation.degree_histogram)
    adjacency_pairs = set(observation.adjacency_pairs)
    chirality_adjacency_pairs = set(observation.chirality_adjacency_pairs)
    if (
        expectation.exact_total_cells is not None
        and observation.total_cells != expectation.exact_total_cells
    ):
        failures.append(
            ReferenceCheckFailure(
                code="unexpected-cell-count",
                message=(
                    f"Depth {observation.depth} expected exactly "
                    f"{expectation.exact_total_cells} cells but saw {observation.total_cells}."
                ),
                depth=observation.depth,
            )
        )
    if (
        expectation.minimum_total_cells is not None
        and observation.total_cells < expectation.minimum_total_cells
    ):
        failures.append(
            ReferenceCheckFailure(
                code="too-few-cells",
                message=(
                    f"Depth {observation.depth} expected at least "
                    f"{expectation.minimum_total_cells} cells but saw {observation.total_cells}."
                ),
                depth=observation.depth,
            )
        )
    if expectation.require_connected_graph and observation.connected_component_count != 1:
        failures.append(
            ReferenceCheckFailure(
                code="disconnected-topology-graph",
                message=(
                    f"Depth {observation.depth} expected a single connected topology component but saw "
                    f"{observation.connected_component_count} components with sizes "
                    f"{_component_size_summary(observation.disconnected_component_sizes)}."
                ),
                depth=observation.depth,
            )
        )
    if (
        expectation.expected_kind_counts is not None
        and observation.kind_counts != expectation.expected_kind_counts
    ):
        failures.append(
            ReferenceCheckFailure(
                code="unexpected-kind-counts",
                message=(
                    f"Depth {observation.depth} expected kind counts "
                    f"{expectation.expected_kind_counts!r} but saw {observation.kind_counts!r}."
                ),
                depth=observation.depth,
            )
        )
    for kind in expectation.required_kinds:
        if kind_counts.get(kind, 0) <= 0:
            failures.append(
                ReferenceCheckFailure(
                    code="missing-required-kind",
                    message=f"Depth {observation.depth} is missing required kind '{kind}'.",
                depth=observation.depth,
            )
        )
    if (
        expectation.expected_adjacency_pairs is not None
        and adjacency_pairs != set(expectation.expected_adjacency_pairs)
    ):
        failures.append(
            ReferenceCheckFailure(
                code="unexpected-adjacency-pairs",
                message=(
                    f"Depth {observation.depth} expected adjacency pairs "
                    f"{expectation.expected_adjacency_pairs!r} but saw {observation.adjacency_pairs!r}."
                ),
                depth=observation.depth,
            )
        )
    for pair in expectation.required_adjacency_pairs:
        normalized = pair if pair[0] <= pair[1] else (pair[1], pair[0])
        if normalized not in adjacency_pairs:
            failures.append(
                ReferenceCheckFailure(
                    code="missing-adjacency-pair",
                    message=(
                        f"Depth {observation.depth} is missing required adjacency pair "
                        f"{normalized[0]}/{normalized[1]}."
                ),
                depth=observation.depth,
            )
        )
    for pair in expectation.required_chirality_adjacency_pairs:
        normalized = pair if pair[0] <= pair[1] else (pair[1], pair[0])
        if normalized not in chirality_adjacency_pairs:
            failures.append(
                ReferenceCheckFailure(
                    code="missing-chirality-adjacency-pair",
                    message=(
                        f"Depth {observation.depth} is missing required chirality adjacency pair "
                        f"{normalized[0]}/{normalized[1]}."
                    ),
                    depth=observation.depth,
                )
            )
    if (
        expectation.expected_degree_histogram is not None
        and degree_histogram != dict(expectation.expected_degree_histogram)
    ):
        failures.append(
            ReferenceCheckFailure(
                code="unexpected-degree-histogram",
                message=(
                    f"Depth {observation.depth} expected degree histogram "
                    f"{expectation.expected_degree_histogram!r} but saw {observation.degree_histogram!r}."
                ),
                depth=observation.depth,
            )
        )
    if (
        expectation.min_unique_orientation_tokens is not None
        and observation.unique_orientation_tokens < expectation.min_unique_orientation_tokens
    ):
        failures.append(
            ReferenceCheckFailure(
                code="insufficient-orientation-diversity",
                message=(
                    f"Depth {observation.depth} expected at least "
                    f"{expectation.min_unique_orientation_tokens} unique orientation tokens "
                    f"but saw {observation.unique_orientation_tokens}."
                ),
                depth=observation.depth,
            )
        )
    if (
        expectation.min_three_opposite_chirality_neighbor_cells is not None
        and observation.three_opposite_chirality_neighbor_cells
        < expectation.min_three_opposite_chirality_neighbor_cells
    ):
        failures.append(
            ReferenceCheckFailure(
                code="insufficient-opposite-chirality-triplets",
                message=(
                    f"Depth {observation.depth} expected at least "
                    f"{expectation.min_three_opposite_chirality_neighbor_cells} cells whose three neighbors "
                    f"all have opposite chirality, but saw {observation.three_opposite_chirality_neighbor_cells}."
                ),
                depth=observation.depth,
            )
        )
    if (
        expectation.min_unique_chirality_tokens is not None
        and observation.unique_chirality_tokens < expectation.min_unique_chirality_tokens
    ):
        failures.append(
            ReferenceCheckFailure(
                code="insufficient-chirality-diversity",
                message=(
                    f"Depth {observation.depth} expected at least "
                    f"{expectation.min_unique_chirality_tokens} unique chirality tokens "
                    f"but saw {observation.unique_chirality_tokens}."
                ),
                depth=observation.depth,
            )
        )
    if expectation.min_unique_polygon_areas_by_kind is not None:
        observed_area_counts = dict(observation.unique_polygon_areas_by_kind)
        for kind, minimum_count in expectation.min_unique_polygon_areas_by_kind:
            if observed_area_counts.get(kind, 0) < minimum_count:
                failures.append(
                    ReferenceCheckFailure(
                        code="insufficient-area-classes",
                        message=(
                            f"Depth {observation.depth} expected at least {minimum_count} distinct polygon-area classes "
                            f"for kind '{kind}' but saw {observed_area_counts.get(kind, 0)}."
                        ),
                        depth=observation.depth,
                    )
                )
    if expectation.min_unique_decoration_variants_by_kind is not None:
        observed_decoration_counts = dict(observation.unique_decoration_variants_by_kind)
        for kind, minimum_count in expectation.min_unique_decoration_variants_by_kind:
            if observed_decoration_counts.get(kind, 0) < minimum_count:
                failures.append(
                    ReferenceCheckFailure(
                        code="insufficient-decoration-variants",
                        message=(
                            f"Depth {observation.depth} expected at least {minimum_count} distinct decoration-token variants "
                            f"for kind '{kind}' but saw {observed_decoration_counts.get(kind, 0)}."
                        ),
                        depth=observation.depth,
                    )
                )
    if (
        expectation.min_bounds_longest_span is not None
        and observation.bounds_longest_span < expectation.min_bounds_longest_span
    ):
        failures.append(
            ReferenceCheckFailure(
                code="insufficient-bounds-span",
                message=(
                    f"Depth {observation.depth} expected longest bounds span >= "
                    f"{expectation.min_bounds_longest_span} but saw {observation.bounds_longest_span}."
                ),
                depth=observation.depth,
            )
        )
    if (
        expectation.max_bounds_aspect_ratio is not None
        and observation.bounds_aspect_ratio > expectation.max_bounds_aspect_ratio
    ):
        failures.append(
            ReferenceCheckFailure(
                code="degenerate-bounds",
                message=(
                    f"Depth {observation.depth} expected bounds aspect ratio <= "
                    f"{expectation.max_bounds_aspect_ratio} but saw {observation.bounds_aspect_ratio}."
                ),
                depth=observation.depth,
            )
        )
    if (
        expectation.expected_signature is not None
        and observation.signature != expectation.expected_signature
    ):
        failures.append(
            ReferenceCheckFailure(
                code="unexpected-signature",
                message=(
                    f"Depth {observation.depth} expected signature "
                    f"{expectation.expected_signature} but saw {observation.signature}."
                ),
                depth=observation.depth,
            )
        )
    return failures


def _compile_periodic_face_id_pattern(id_pattern: str) -> re.Pattern[str]:
    token_patterns = {
        "prefix": r"(?P<prefix>[^:]+)",
        "slot": r"(?P<slot>[^:]+)",
        "x": r"(?P<x>\d+)",
        "y": r"(?P<y>\d+)",
    }
    parts: list[str] = []
    position = 0
    for match in re.finditer(r"\{(prefix|slot|x|y)\}", id_pattern):
        parts.append(re.escape(id_pattern[position:match.start()]))
        parts.append(token_patterns[match.group(1)])
        position = match.end()
    parts.append(re.escape(id_pattern[position:]))
    return re.compile("^" + "".join(parts) + "$")


def _parse_periodic_face_cell_id(
    descriptor: PeriodicFaceTilingDescriptor,
    cell_id: str,
) -> dict[str, str] | None:
    match = _compile_periodic_face_id_pattern(descriptor.id_pattern).fullmatch(cell_id)
    if match is None:
        return None
    return {key: value for key, value in match.groupdict().items() if value is not None}


def _verify_periodic_face_id_roundtrip(
    descriptor: PeriodicFaceTilingDescriptor,
    cell: PeriodicFaceCell,
) -> ReferenceCheckFailure | None:
    parsed = _parse_periodic_face_cell_id(descriptor, cell.id)
    if parsed is None:
        return ReferenceCheckFailure(
            code="descriptor-id-pattern-mismatch",
            message=f"{descriptor.geometry} cell id '{cell.id}' did not match descriptor pattern {descriptor.id_pattern!r}.",
        )
    if "slot" in parsed and parsed["slot"] != cell.slot:
        return ReferenceCheckFailure(
            code="descriptor-slot-roundtrip-mismatch",
            message=(
                f"{descriptor.geometry} cell id '{cell.id}' encoded slot {parsed['slot']!r} "
                f"but the generated cell slot was {cell.slot!r}."
            ),
        )
    if "x" not in parsed or "y" not in parsed:
        return ReferenceCheckFailure(
            code="descriptor-missing-grid-coordinates",
            message=f"{descriptor.geometry} descriptor id pattern must encode both x and y coordinates.",
        )
    reconstructed_id = descriptor.id_pattern.format(
        prefix=parsed.get("prefix", ""),
        slot=cell.slot or "",
        x=int(parsed["x"]),
        y=int(parsed["y"]),
    )
    if reconstructed_id != cell.id:
        return ReferenceCheckFailure(
            code="descriptor-id-roundtrip-mismatch",
            message=(
                f"{descriptor.geometry} cell id '{cell.id}' did not round-trip through the descriptor "
                f"pattern; reconstructed '{reconstructed_id}'."
            ),
        )
    return None


def _periodic_face_translation_failures(
    descriptor: PeriodicFaceTilingDescriptor,
    cells: tuple[PeriodicFaceCell, ...],
) -> list[ReferenceCheckFailure]:
    failures: list[ReferenceCheckFailure] = []
    cells_by_slot_and_grid: dict[tuple[str, int, int], PeriodicFaceCell] = {}
    for cell in cells:
        parsed = _parse_periodic_face_cell_id(descriptor, cell.id)
        if parsed is None or "x" not in parsed or "y" not in parsed or cell.slot is None:
            continue
        cells_by_slot_and_grid[(cell.slot, int(parsed["x"]), int(parsed["y"]))] = cell

    for (slot, logical_x, logical_y), cell in sorted(cells_by_slot_and_grid.items()):
        right = cells_by_slot_and_grid.get((slot, logical_x + 1, logical_y))
        if right is not None:
            delta_x = right.center[0] - cell.center[0]
            delta_y = right.center[1] - cell.center[1]
            if not math.isclose(delta_x, descriptor.unit_width, abs_tol=_FLOAT_TOLERANCE):
                failures.append(
                    ReferenceCheckFailure(
                        code="descriptor-x-translation-mismatch",
                        message=(
                            f"{descriptor.geometry} slot {slot!r} expected x translation {descriptor.unit_width} "
                            f"but saw {round(delta_x, 6)} between logical cells ({logical_x},{logical_y}) and ({logical_x + 1},{logical_y})."
                        ),
                    )
                )
            if not math.isclose(delta_y, 0.0, abs_tol=_FLOAT_TOLERANCE):
                failures.append(
                    ReferenceCheckFailure(
                        code="descriptor-x-translation-y-drift",
                        message=(
                            f"{descriptor.geometry} slot {slot!r} drifted in y by {round(delta_y, 6)} "
                            f"across x translation at logical row {logical_y}."
                        ),
                    )
                )

        below = cells_by_slot_and_grid.get((slot, logical_x, logical_y + 1))
        if below is not None:
            expected_delta_x = (
                descriptor.row_offset_x
                if (logical_y + 1) % 2 == 1
                else 0.0
            ) - (descriptor.row_offset_x if logical_y % 2 == 1 else 0.0)
            delta_x = below.center[0] - cell.center[0]
            delta_y = below.center[1] - cell.center[1]
            if not math.isclose(delta_y, descriptor.unit_height, abs_tol=_FLOAT_TOLERANCE):
                failures.append(
                    ReferenceCheckFailure(
                        code="descriptor-y-translation-mismatch",
                        message=(
                            f"{descriptor.geometry} slot {slot!r} expected y translation {descriptor.unit_height} "
                            f"but saw {round(delta_y, 6)} between logical rows {logical_y} and {logical_y + 1}."
                        ),
                    )
                )
            if not math.isclose(delta_x, expected_delta_x, abs_tol=_FLOAT_TOLERANCE):
                failures.append(
                    ReferenceCheckFailure(
                        code="descriptor-row-offset-mismatch",
                        message=(
                            f"{descriptor.geometry} slot {slot!r} expected row-offset delta {expected_delta_x} "
                            f"but saw {round(delta_x, 6)} between logical rows {logical_y} and {logical_y + 1}."
                        ),
                    )
                )
    return failures


def _periodic_face_descriptor_failures(spec: ReferenceFamilySpec) -> list[ReferenceCheckFailure]:
    if not is_periodic_face_tiling(spec.geometry):
        return []
    descriptor = get_periodic_face_tiling_descriptor(spec.geometry)
    failures: list[ReferenceCheckFailure] = []
    if descriptor.metric_model != "pattern":
        failures.append(
            ReferenceCheckFailure(
                code="unexpected-descriptor-metric-model",
                message=(
                    f"{spec.geometry} descriptor expected metric_model 'pattern' "
                    f"but saw {descriptor.metric_model!r}."
                ),
            )
        )
    if descriptor.cell_count_per_unit != descriptor.face_template_count:
        failures.append(
            ReferenceCheckFailure(
                code="descriptor-cell-count-mismatch",
                message=(
                    f"{spec.geometry} descriptor declared cell_count_per_unit "
                    f"{descriptor.cell_count_per_unit} but loaded {descriptor.face_template_count} face templates."
                ),
            )
        )
    if set(descriptor.face_kinds) != set(spec.allowed_public_cell_kinds):
        failures.append(
            ReferenceCheckFailure(
                code="descriptor-kind-vocabulary-mismatch",
                message=(
                    f"{spec.geometry} descriptor face kinds {descriptor.face_kinds!r} "
                    f"did not match the reference spec kinds {spec.allowed_public_cell_kinds!r}."
                ),
            )
        )
    periodic_descriptor = spec.periodic_descriptor
    if periodic_descriptor is None:
        return failures
    if descriptor.face_template_count != periodic_descriptor.face_template_count:
        failures.append(
            ReferenceCheckFailure(
                code="descriptor-face-template-count-mismatch",
                message=(
                    f"{spec.geometry} descriptor face template count {descriptor.face_template_count} "
                    f"did not match the reference expectation {periodic_descriptor.face_template_count}."
                ),
            )
        )
    if descriptor.face_slots != periodic_descriptor.slot_vocabulary:
        failures.append(
            ReferenceCheckFailure(
                code="descriptor-slot-vocabulary-mismatch",
                message=(
                    f"{spec.geometry} descriptor slots {descriptor.face_slots!r} "
                    f"did not match the reference expectation {periodic_descriptor.slot_vocabulary!r}."
                ),
            )
        )
    if descriptor.id_pattern != periodic_descriptor.id_pattern:
        failures.append(
            ReferenceCheckFailure(
                code="descriptor-id-pattern-mismatch",
                message=(
                    f"{spec.geometry} descriptor id pattern {descriptor.id_pattern!r} "
                    f"did not match the reference expectation {periodic_descriptor.id_pattern!r}."
                ),
            )
        )
    if not math.isclose(descriptor.row_offset_x, periodic_descriptor.row_offset_x, abs_tol=_FLOAT_TOLERANCE):
        failures.append(
            ReferenceCheckFailure(
                code="descriptor-row-offset-field-mismatch",
                message=(
                    f"{spec.geometry} descriptor row_offset_x {descriptor.row_offset_x} "
                    f"did not match the reference expectation {periodic_descriptor.row_offset_x}."
                ),
            )
        )
    sample_cells = descriptor.build_faces(3, 3)
    for cell in sample_cells:
        failure = _verify_periodic_face_id_roundtrip(descriptor, cell)
        if failure is not None:
            failures.append(failure)
    failures.extend(_periodic_face_translation_failures(descriptor, sample_cells))
    return failures


def _builder_signal_failures(
    expectations: tuple[BuilderSignalExpectation, ...],
) -> list[ReferenceCheckFailure]:
    failures: list[ReferenceCheckFailure] = []
    for expectation in expectations:
        module = import_module(expectation.module)
        value = getattr(module, expectation.attribute, None)
        if value != expectation.expected_value:
            failures.append(
                ReferenceCheckFailure(
                    code="builder-signal-mismatch",
                    message=(
                        f"{expectation.module}.{expectation.attribute} expected "
                        f"{expectation.expected_value!r} but saw {value!r}."
                    ),
                )
            )
    return failures


def _pinwheel_exact_path_failures() -> list[ReferenceCheckFailure]:
    from backend.simulation.aperiodic_pinwheel import collect_pinwheel_exact_records

    failures: list[ReferenceCheckFailure] = []
    for depth in range(4):
        patch = build_aperiodic_patch("pinwheel", depth)
        exact_records = collect_pinwheel_exact_records(depth)
        if len(exact_records) != len(patch.cells):
            failures.append(
                ReferenceCheckFailure(
                    code="pinwheel-exact-record-mismatch",
                    message=(
                        f"Depth {depth} exact record count {len(exact_records)} "
                        f"did not match patch cell count {len(patch.cells)}."
                    ),
                    depth=depth,
                )
            )
        exact_ids = tuple(sorted(record["id"] for record in exact_records))
        patch_ids = tuple(sorted(cell.id for cell in patch.cells))
        if exact_ids != patch_ids:
            failures.append(
                ReferenceCheckFailure(
                    code="pinwheel-exact-id-mismatch",
                    message=f"Depth {depth} exact-record ids did not match patch ids.",
                    depth=depth,
                )
            )
    return failures


def _verify_spec(spec: ReferenceFamilySpec) -> ReferenceVerificationResult:
    observations = tuple(
        observe_reference_patch(spec.geometry, depth)
        for depth in sorted(spec.depth_expectations)
    )
    failures: list[ReferenceCheckFailure] = []
    deepest_topology = _build_reference_topology(spec, max(spec.depth_expectations, default=0))
    observed_kinds = {cell.kind for cell in deepest_topology.cells}
    unexpected_kinds = observed_kinds.difference(spec.allowed_public_cell_kinds)
    if unexpected_kinds:
        failures.append(
            ReferenceCheckFailure(
                code="unexpected-kind",
                message=(
                    f"Observed unexpected public kinds for {spec.geometry}: "
                    + ", ".join(sorted(unexpected_kinds))
                ),
            )
        )
    for requirement in spec.required_metadata:
        failures.extend(_metadata_failures(deepest_topology, requirement))
    failures.extend(_periodic_face_descriptor_failures(spec))
    failures.extend(_builder_signal_failures(spec.builder_signals))
    if spec.exact_reference_mode == "pinwheel_exact":
        failures.extend(_pinwheel_exact_path_failures())
    for observation in observations:
        expectation = spec.depth_expectations[observation.depth]
        failures.extend(_expectation_failures(observation, expectation))

    waived = spec.geometry in STAGED_REFERENCE_WAIVERS
    status: VerificationStatus
    if failures:
        status = "KNOWN_DEVIATION" if waived else "FAIL"
    else:
        status = "PASS"
    return ReferenceVerificationResult(
        geometry=spec.geometry,
        display_name=spec.display_name,
        status=status,
        blocking=status == "FAIL",
        waived=waived,
        source_urls=spec.source_urls,
        observations=observations,
        failures=tuple(failures),
    )


def verify_reference_family(geometry: str) -> ReferenceVerificationResult:
    try:
        spec = REFERENCE_FAMILY_SPECS[geometry]
    except KeyError as error:
        raise ValueError(f"Unsupported reference verification geometry '{geometry}'.") from error
    return _verify_spec(spec)


def verify_all_reference_families() -> tuple[ReferenceVerificationResult, ...]:
    return tuple(
        _verify_spec(spec)
        for _, spec in sorted(REFERENCE_FAMILY_SPECS.items())
    )
