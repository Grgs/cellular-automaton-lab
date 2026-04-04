from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha1
from importlib import import_module
import json
import math
from pathlib import Path
import re
from typing import Literal, TypedDict

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
from backend.simulation.topology_validation import build_topology_graph, validate_topology


VerificationStatus = Literal["PASS", "KNOWN_DEVIATION", "FAIL"]
_FLOAT_TOLERANCE = 1e-6
_LOCAL_REFERENCE_FIXTURE_PATH = Path(__file__).with_name("data") / "reference_patch_local_fixtures.json"


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
    orientation_token_counts: tuple[tuple[str, int], ...]
    degree_histogram: tuple[tuple[int, int], ...]
    connected_component_count: int
    disconnected_component_sizes: tuple[int, ...]
    largest_component_size: int
    isolated_cell_count: int
    surface_component_count: int | None
    hole_count: int
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


class _LocalReferencePayload(TypedDict):
    kind: str
    orientation_token: str | None
    chirality_token: str | None
    decoration_tokens: list[str] | None
    area: float


class _LocalReferenceRootPayload(_LocalReferencePayload):
    degree: int


class _LocalReferenceNeighborPayload(_LocalReferencePayload):
    delta: list[float]


class _LocalReferenceAnchorPayload(TypedDict):
    root: _LocalReferenceRootPayload
    neighbors: list[_LocalReferenceNeighborPayload]


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


def _periodic_face_sample_size(
    spec: ReferenceFamilySpec,
    sample_key: int,
) -> tuple[int, int]:
    periodic_descriptor = spec.periodic_descriptor
    if periodic_descriptor is None or periodic_descriptor.canonical_grid_size is None:
        return (sample_key, sample_key)
    return periodic_descriptor.canonical_grid_size


def _build_reference_topology(spec: ReferenceFamilySpec, sample_key: int) -> LatticeTopology:
    if spec.sample_mode == "grid":
        width, height = _periodic_face_sample_size(spec, sample_key)
        return build_topology(spec.geometry, width, height, None)
    return build_topology(spec.geometry, 0, 0, sample_key)


def _polygon_area_frequencies_by_kind(
    topology: LatticeTopology,
) -> tuple[tuple[str, tuple[tuple[float, int], ...]], ...]:
    frequencies_by_kind: dict[str, Counter[float]] = {}
    for cell in topology.cells:
        if cell.vertices is None:
            continue
        frequencies_by_kind.setdefault(cell.kind, Counter())[round(_polygon_area(cell.vertices), 6)] += 1
    return tuple(
        sorted(
            (
                kind,
                tuple(sorted(counter.items())),
            )
            for kind, counter in frequencies_by_kind.items()
        )
    )


def _load_local_reference_fixtures() -> dict[str, dict[str, dict[str, object]]]:
    return json.loads(_LOCAL_REFERENCE_FIXTURE_PATH.read_text(encoding="utf-8"))


def _cell_local_reference_payload(
    topology: LatticeTopology,
    anchor_id: str,
) -> _LocalReferenceAnchorPayload | None:
    if not topology.has_cell(anchor_id):
        return None
    anchor = topology.get_cell(anchor_id)
    if anchor.vertices is None or anchor.center is None:
        return None
    cells_by_id = {cell.id: cell for cell in topology.cells}
    center_x, center_y = anchor.center

    def _payload(cell: LatticeCell) -> _LocalReferencePayload:
        vertices = cell.vertices
        if vertices is None:
            raise ValueError("Local reference payloads require polygon vertices.")
        return {
            "kind": cell.kind,
            "orientation_token": cell.orientation_token,
            "chirality_token": cell.chirality_token,
            "decoration_tokens": list(cell.decoration_tokens) if cell.decoration_tokens is not None else None,
            "area": round(_polygon_area(vertices), 6),
        }

    neighbors: list[_LocalReferenceNeighborPayload] = []
    for neighbor_id in sorted(neighbor_id for neighbor_id in anchor.neighbors if neighbor_id is not None):
        neighbor = cells_by_id.get(neighbor_id)
        if neighbor is None or neighbor.vertices is None or neighbor.center is None:
            continue
        payload = _payload(neighbor)
        neighbors.append(
            {
                **payload,
                "delta": [
                    round(neighbor.center[0] - center_x, 6),
                    round(neighbor.center[1] - center_y, 6),
                ],
            }
        )

    ordered_neighbors = sorted(
        neighbors,
        key=lambda item: (
            item["kind"],
            item["orientation_token"] or "",
            item["chirality_token"] or "",
            tuple(item["decoration_tokens"] or []),
            item["delta"][0],
            item["delta"][1],
            item["area"],
        ),
    )
    return {
        "root": {
            **_payload(anchor),
            "degree": len(tuple(neighbor_id for neighbor_id in anchor.neighbors if neighbor_id is not None)),
        },
        "neighbors": ordered_neighbors,
    }


def _local_reference_fixture_failures(
    geometry: str,
    depth: int,
    topology: LatticeTopology,
) -> list[ReferenceCheckFailure]:
    fixtures = _load_local_reference_fixtures()
    geometry_fixtures = fixtures.get(geometry, {})
    depth_fixtures = geometry_fixtures.get(str(depth))
    if not isinstance(depth_fixtures, dict):
        return []
    failures: list[ReferenceCheckFailure] = []
    for anchor_id, expected_payload in sorted(depth_fixtures.items()):
        observed_payload = _cell_local_reference_payload(topology, anchor_id)
        if observed_payload is None:
            failures.append(
                ReferenceCheckFailure(
                    code="missing-local-reference-anchor",
                    message=(
                        f"Depth {depth} expected local reference anchor {anchor_id!r} "
                        f"for {geometry} but that cell was absent."
                    ),
                    depth=depth,
                )
            )
            continue
        if observed_payload != expected_payload:
            failures.append(
                ReferenceCheckFailure(
                    code="local-reference-fixture-mismatch",
                    message=(
                        f"Depth {depth} local reference payload for {geometry} anchor {anchor_id!r} "
                        "did not match the checked-in canonical fixture."
                    ),
                    depth=depth,
                )
            )
    return failures


def _observe_reference_topology(
    *,
    geometry: str,
    sample_mode: str,
    depth: int,
    topology: LatticeTopology,
) -> ReferencePatchObservation:
    kind_counts = Counter(cell.kind for cell in topology.cells)
    orientation_token_counts = Counter(
        cell.orientation_token
        for cell in topology.cells
        if cell.orientation_token is not None
    )
    area_classes_by_kind: dict[str, set[float]] = {}
    decoration_variants_by_kind: dict[str, set[tuple[str, ...]]] = {}
    chirality_adjacency_pairs: set[tuple[str, str]] = set()
    three_opposite_chirality_neighbor_cells = 0
    by_id = {cell.id: cell for cell in topology.cells}
    for cell in topology.cells:
        if cell.vertices is not None:
            area_classes_by_kind.setdefault(cell.kind, set()).add(
                round(_polygon_area(cell.vertices), 6)
            )
        if cell.decoration_tokens is not None:
            decoration_variants_by_kind.setdefault(cell.kind, set()).add(
                tuple(cell.decoration_tokens)
            )
        neighbor_chiralities = []
        for neighbor_id in cell.neighbors:
            if neighbor_id is None or cell.chirality_token is None:
                continue
            neighbor = by_id[neighbor_id]
            if neighbor.chirality_token is None:
                continue
            left = cell.chirality_token
            right = neighbor.chirality_token
            chirality_adjacency_pairs.add(
                (left, right) if left <= right else (right, left)
            )
            neighbor_chiralities.append(neighbor.chirality_token)
        if (
            cell.chirality_token is not None
            and len(neighbor_chiralities) == 3
            and all(
                chirality != cell.chirality_token for chirality in neighbor_chiralities
            )
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
    surface_validation = validate_topology(
        topology,
        check_surface=True,
        check_overlaps=False,
        check_edge_multiplicity=False,
        check_graph_connectivity=False,
    )
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
        sample_mode=sample_mode,
        depth=int(depth),
        total_cells=len(topology.cells),
        kind_counts=tuple(sorted(kind_counts.items())),
        orientation_token_counts=tuple(sorted(orientation_token_counts.items())),
        degree_histogram=tuple(sorted(degree_histogram.items())),
        connected_component_count=connected_component_count,
        disconnected_component_sizes=disconnected_component_sizes,
        largest_component_size=largest_component_size,
        isolated_cell_count=isolated_cell_count,
        surface_component_count=surface_validation.surface_component_count,
        hole_count=surface_validation.hole_count,
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
        signature=_topology_signature(geometry, sample_mode, depth, topology),
    )


def observe_reference_patch(geometry: str, depth: int) -> ReferencePatchObservation:
    spec = REFERENCE_FAMILY_SPECS[geometry]
    topology = _build_reference_topology(spec, depth)
    return _observe_reference_topology(
        geometry=geometry,
        sample_mode=spec.sample_mode,
        depth=depth,
        topology=topology,
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
    if expectation.require_hole_free_surface and observation.hole_count != 0:
        failures.append(
            ReferenceCheckFailure(
                code="surface-holes",
                message=(
                    f"Depth {observation.depth} expected a hole-free surface but saw "
                    f"{observation.hole_count} enclosed gap(s)."
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
    if (
        expectation.expected_orientation_token_counts is not None
        and observation.orientation_token_counts != expectation.expected_orientation_token_counts
    ):
        failures.append(
            ReferenceCheckFailure(
                code="unexpected-orientation-token-counts",
                message=(
                    f"Depth {observation.depth} expected orientation-token counts "
                    f"{expectation.expected_orientation_token_counts!r} but saw "
                    f"{observation.orientation_token_counts!r}."
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


def _depth_topology_expectation_failures(
    *,
    geometry: str,
    depth: int,
    topology: LatticeTopology,
    expectation: ReferenceDepthExpectation,
    observation: ReferencePatchObservation | None = None,
) -> list[ReferenceCheckFailure]:
    active_observation = observation
    if active_observation is None:
        active_observation = _observe_reference_topology(
            geometry=geometry,
            sample_mode=REFERENCE_FAMILY_SPECS[geometry].sample_mode,
            depth=depth,
            topology=topology,
        )

    failures: list[ReferenceCheckFailure] = list(
        _expectation_failures(active_observation, expectation)
    )
    if expectation.expected_polygon_area_frequencies_by_kind is not None:
        observed = _polygon_area_frequencies_by_kind(topology)
        if observed != expectation.expected_polygon_area_frequencies_by_kind:
            failures.append(
                ReferenceCheckFailure(
                    code="unexpected-polygon-area-frequencies",
                    message=(
                        f"Depth {depth} expected polygon-area frequencies "
                        f"{expectation.expected_polygon_area_frequencies_by_kind!r} "
                        f"but saw {observed!r}."
                    ),
                    depth=depth,
                )
            )
    failures.extend(_local_reference_fixture_failures(geometry, depth, topology))
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


def _canonicalize_vertex_configuration(configuration: tuple[str, ...]) -> tuple[str, ...]:
    if not configuration:
        return ()
    candidates: list[tuple[str, ...]] = []
    for direction in (configuration, tuple(reversed(configuration))):
        for index in range(len(direction)):
            candidates.append(direction[index:] + direction[:index])
    return min(candidates)


def _periodic_face_interior_vertex_configuration_occurrences(
    cells: tuple[PeriodicFaceCell, ...],
) -> tuple[tuple[str, ...], ...]:
    def _matching_group_id(
        groups: list[list[tuple[float, float]]],
        point: tuple[float, float],
    ) -> int | None:
        for group_id, group in enumerate(groups):
            representative = group[0]
            if (
                math.isclose(representative[0], point[0], abs_tol=_FLOAT_TOLERANCE)
                and math.isclose(representative[1], point[1], abs_tol=_FLOAT_TOLERANCE)
            ):
                return group_id
        return None

    vertex_groups: list[list[tuple[float, float]]] = []
    vertex_group_by_cell_vertex: dict[tuple[int, int], int] = {}
    incident_cells_by_group: dict[int, set[str]] = {}
    cells_by_id = {cell.id: cell for cell in cells}

    for cell_index, cell in enumerate(cells):
        for vertex_index, point in enumerate(cell.vertices):
            group_id = _matching_group_id(vertex_groups, point)
            if group_id is None:
                group_id = len(vertex_groups)
                vertex_groups.append([point])
            else:
                vertex_groups[group_id].append(point)
            vertex_group_by_cell_vertex[(cell_index, vertex_index)] = group_id
            incident_cells_by_group.setdefault(group_id, set()).add(cell.id)

    if not vertex_groups:
        return ()

    representative_points: dict[int, tuple[float, float]] = {}
    for group_id, group in enumerate(vertex_groups):
        representative_points[group_id] = (
            sum(point[0] for point in group) / len(group),
            sum(point[1] for point in group) / len(group),
        )

    edge_counts: Counter[tuple[int, int]] = Counter()
    for cell_index, cell in enumerate(cells):
        for vertex_index in range(len(cell.vertices)):
            left_group = vertex_group_by_cell_vertex[(cell_index, vertex_index)]
            right_group = vertex_group_by_cell_vertex[
                (cell_index, (vertex_index + 1) % len(cell.vertices))
            ]
            if left_group == right_group:
                continue
            edge = (
                (left_group, right_group)
                if left_group <= right_group
                else (right_group, left_group)
            )
            edge_counts[edge] += 1

    boundary_vertex_groups = {
        group_id
        for edge, count in edge_counts.items()
        if count == 1
        for group_id in edge
    }

    all_x = [point[0] for point in representative_points.values()]
    all_y = [point[1] for point in representative_points.values()]
    min_x = min(all_x)
    max_x = max(all_x)
    min_y = min(all_y)
    max_y = max(all_y)
    for group_id, point in representative_points.items():
        if (
            math.isclose(point[0], min_x, abs_tol=_FLOAT_TOLERANCE)
            or math.isclose(point[0], max_x, abs_tol=_FLOAT_TOLERANCE)
            or math.isclose(point[1], min_y, abs_tol=_FLOAT_TOLERANCE)
            or math.isclose(point[1], max_y, abs_tol=_FLOAT_TOLERANCE)
        ):
            boundary_vertex_groups.add(group_id)

    configurations: list[tuple[str, ...]] = []
    for group_id, cell_ids in incident_cells_by_group.items():
        if group_id in boundary_vertex_groups:
            continue
        point = representative_points[group_id]
        incident_cells = [cells_by_id[cell_id] for cell_id in cell_ids]
        ordered_cells = sorted(
            incident_cells,
            key=lambda cell: math.atan2(
                cell.center[1] - point[1],
                cell.center[0] - point[0],
            ),
        )
        configurations.append(
            _canonicalize_vertex_configuration(
                tuple(cell.kind for cell in ordered_cells)
            )
        )
    return tuple(sorted(configurations))


def _periodic_face_interior_vertex_configurations(
    cells: tuple[PeriodicFaceCell, ...],
) -> tuple[tuple[str, ...], ...]:
    return tuple(
        sorted(set(_periodic_face_interior_vertex_configuration_occurrences(cells)))
    )


def _periodic_face_interior_vertex_configuration_frequencies(
    cells: tuple[PeriodicFaceCell, ...],
) -> tuple[tuple[tuple[str, ...], int], ...]:
    return tuple(
        sorted(
            Counter(
                _periodic_face_interior_vertex_configuration_occurrences(cells)
            ).items()
        )
    )


def _periodic_face_unique_polygon_side_counts(
    cells: tuple[PeriodicFaceCell, ...],
) -> tuple[int, ...]:
    return tuple(sorted({len(cell.vertices) for cell in cells}))


def _periodic_face_dual_structure_failure(
    *,
    geometry: str,
    periodic_descriptor: PeriodicDescriptorExpectation,
    sample_cells: tuple[PeriodicFaceCell, ...],
    observed_vertex_configurations: tuple[tuple[str, ...], ...],
) -> ReferenceCheckFailure | None:
    dual_geometry = periodic_descriptor.expected_dual_geometry
    if dual_geometry is None:
        return None
    dual_spec = REFERENCE_FAMILY_SPECS.get(dual_geometry)
    if dual_spec is None or dual_spec.periodic_descriptor is None or not is_periodic_face_tiling(dual_geometry):
        return ReferenceCheckFailure(
            code="descriptor-dual-geometry-missing",
            message=(
                f"{geometry} expected periodic dual geometry {dual_geometry!r}, "
                "but no matching periodic reference spec was available."
            ),
        )
    if dual_spec.periodic_descriptor.expected_dual_geometry != geometry:
        return ReferenceCheckFailure(
            code="descriptor-dual-geometry-not-reciprocal",
            message=(
                f"{geometry} expected reciprocal dual geometry {dual_geometry!r}, "
                f"but that spec pointed to {dual_spec.periodic_descriptor.expected_dual_geometry!r}."
            ),
        )

    dual_width, dual_height = _periodic_face_sample_size(
        dual_spec,
        max(dual_spec.depth_expectations, default=3),
    )
    dual_cells = get_periodic_face_tiling_descriptor(dual_geometry).build_faces(
        dual_width,
        dual_height,
    )
    observed_side_counts = _periodic_face_unique_polygon_side_counts(sample_cells)
    observed_vertex_valences = tuple(sorted({len(configuration) for configuration in observed_vertex_configurations}))
    dual_side_counts = _periodic_face_unique_polygon_side_counts(dual_cells)
    dual_vertex_valences = tuple(
        sorted(
            {
                len(configuration)
                for configuration in _periodic_face_interior_vertex_configurations(dual_cells)
            }
        )
    )
    if observed_side_counts != dual_vertex_valences or dual_side_counts != observed_vertex_valences:
        return ReferenceCheckFailure(
            code="descriptor-dual-structure-mismatch",
            message=(
                f"{geometry} expected reciprocal dual structure with {dual_geometry}: "
                f"face side counts {observed_side_counts!r} vs dual interior vertex valences {dual_vertex_valences!r}, "
                f"and interior vertex valences {observed_vertex_valences!r} vs dual face side counts {dual_side_counts!r}."
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
    sample_width, sample_height = _periodic_face_sample_size(
        spec,
        max(spec.depth_expectations, default=3),
    )
    sample_cells = descriptor.build_faces(sample_width, sample_height)
    for cell in sample_cells:
        failure = _verify_periodic_face_id_roundtrip(descriptor, cell)
        if failure is not None:
            failures.append(failure)
    observed_vertex_configurations = _periodic_face_interior_vertex_configurations(sample_cells)
    observed_vertex_configuration_frequencies = _periodic_face_interior_vertex_configuration_frequencies(sample_cells)
    if (
        observed_vertex_configurations
        != periodic_descriptor.expected_interior_vertex_configurations
    ):
        failures.append(
            ReferenceCheckFailure(
                code="descriptor-interior-vertex-configurations-mismatch",
                message=(
                    f"{spec.geometry} interior vertex configurations "
                    f"{observed_vertex_configurations!r} did not match the reference expectation "
                    f"{periodic_descriptor.expected_interior_vertex_configurations!r}."
                ),
            )
        )
    if (
        observed_vertex_configuration_frequencies
        != periodic_descriptor.expected_interior_vertex_configuration_frequencies
    ):
        failures.append(
            ReferenceCheckFailure(
                code="descriptor-interior-vertex-configuration-frequencies-mismatch",
                message=(
                    f"{spec.geometry} interior vertex configuration frequencies "
                    f"{observed_vertex_configuration_frequencies!r} did not match the reference expectation "
                    f"{periodic_descriptor.expected_interior_vertex_configuration_frequencies!r}."
                ),
            )
        )
    dual_failure = _periodic_face_dual_structure_failure(
        geometry=spec.geometry,
        periodic_descriptor=periodic_descriptor,
        sample_cells=sample_cells,
        observed_vertex_configurations=observed_vertex_configurations,
    )
    if dual_failure is not None:
        failures.append(dual_failure)
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
        depth_topology = _build_reference_topology(spec, observation.depth)
        failures.extend(
            _depth_topology_expectation_failures(
                geometry=spec.geometry,
                depth=observation.depth,
                topology=depth_topology,
                expectation=expectation,
                observation=observation,
            )
        )

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
