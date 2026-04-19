from __future__ import annotations

from collections import Counter
from hashlib import sha1
import json

import networkx as nx

from backend.simulation.literature_reference_specs import REFERENCE_FAMILY_SPECS, ReferenceFamilySpec
from backend.simulation.topology import build_topology
from backend.simulation.topology_types import LatticeCell, LatticeTopology
from backend.simulation.topology_validation import build_topology_graph, validate_topology

from .types import ReferencePatchObservation


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


def observe_topology(
    *,
    geometry: str,
    sample_mode: str,
    depth: int,
    topology: LatticeTopology,
) -> ReferencePatchObservation:
    return _observe_reference_topology(
        geometry=geometry,
        sample_mode=sample_mode,
        depth=depth,
        topology=topology,
    )


def observe_reference_patch(geometry: str, depth: int) -> ReferencePatchObservation:
    spec = REFERENCE_FAMILY_SPECS[geometry]
    topology = _build_reference_topology(spec, depth)
    return observe_topology(
        geometry=geometry,
        sample_mode=spec.sample_mode,
        depth=depth,
        topology=topology,
    )
