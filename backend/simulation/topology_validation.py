from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import networkx as nx
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.validation import explain_validity

from backend.simulation.aperiodic_family_manifest import APERIODIC_FAMILY_MANIFEST
from backend.simulation.topology import LatticeTopology


# Snap-to-grid precision for periodic-face tilings. 6 decimals reconciles
# JSON-stored coordinates (which round to 6 places) with math-derived ones
# (e.g. 52*sqrt(3) at full float64). For non-edge-to-edge tilings with
# irrational coordinates (Stein-14 and friends), this snap alone isn't
# enough to make T-junction vertices land bit-exactly on edge midpoints;
# those geometries opt into a looser polygon-overlap tolerance below.
_COORDINATE_PRECISION = 6
_AREA_TOLERANCE = 1e-7
_SURFACE_HOLE_AREA_TOLERANCE = 2e-7

# Tilings that combine T-junctions with irrational vertex coordinates can't
# enforce exact midpoint alignment in float arithmetic (the midpoint of two
# stored-at-8-decimals endpoints generally differs from the stored 8-decimal
# T-junction vertex by O(1e-9), producing polygon intersections of O(1e-5)
# that aren't real overlaps). For these geometries we use a looser overlap
# tolerance proportional to the polygon size. All other geometries (edge-to-
# edge tilings, or T-junction tilings with rational coordinates) keep the
# strict 1e-7 tolerance.
_NON_EDGE_TO_EDGE_IRRATIONAL_GEOMETRIES: frozenset[str] = frozenset(
    {
        "stein-14-pentagonal",
    }
)
_NON_EDGE_TO_EDGE_AREA_TOLERANCE = 1e-3
_NON_EDGE_TO_EDGE_SURFACE_HOLE_TOLERANCE = 1e-2


def _overlap_area_tolerance(geometry: str | None) -> float:
    if geometry in _NON_EDGE_TO_EDGE_IRRATIONAL_GEOMETRIES:
        return _NON_EDGE_TO_EDGE_AREA_TOLERANCE
    return _AREA_TOLERANCE


def _surface_hole_area_tolerance(geometry: str | None) -> float:
    if geometry in _NON_EDGE_TO_EDGE_IRRATIONAL_GEOMETRIES:
        return _NON_EDGE_TO_EDGE_SURFACE_HOLE_TOLERANCE
    return _SURFACE_HOLE_AREA_TOLERANCE


@dataclass(frozen=True)
class PolygonIssue:
    cell_id: str
    reason: str


@dataclass(frozen=True)
class EdgeMultiplicityIssue:
    edge: tuple[tuple[float, float], tuple[float, float]]
    multiplicity: int
    owners: tuple[str, ...]


@dataclass(frozen=True)
class OverlapAreaPair:
    left_id: str
    right_id: str
    area: float


@dataclass(frozen=True)
class TopologyOverlapAreaDiagnostics:
    pair_count: int
    max_area: float
    top_pairs: tuple[OverlapAreaPair, ...] = ()


@dataclass(frozen=True)
class TopologyValidationResult:
    geometry: str
    checked_cell_count: int
    polygon_issues: tuple[PolygonIssue, ...] = ()
    overlapping_pairs: tuple[tuple[str, str], ...] = ()
    missing_neighbor_cells: tuple[tuple[str, str], ...] = ()
    asymmetric_neighbor_links: tuple[tuple[str, str], ...] = ()
    duplicate_neighbor_cells: tuple[str, ...] = ()
    disconnected_components: tuple[tuple[str, ...], ...] = ()
    edge_multiplicity_issues: tuple[EdgeMultiplicityIssue, ...] = ()
    surface_component_count: int | None = None
    hole_count: int = 0

    @property
    def is_valid(self) -> bool:
        has_surface_issue = (
            self.surface_component_count is not None and self.surface_component_count != 1
        )
        return not any(
            (
                self.polygon_issues,
                self.overlapping_pairs,
                self.missing_neighbor_cells,
                self.asymmetric_neighbor_links,
                self.duplicate_neighbor_cells,
                self.disconnected_components,
                self.edge_multiplicity_issues,
                self.hole_count,
                has_surface_issue,
            )
        )

    def summary_lines(self) -> tuple[str, ...]:
        lines = [
            f"{self.geometry}: {'PASS' if self.is_valid else 'FAIL'} ({self.checked_cell_count} cells)"
        ]
        if self.polygon_issues:
            lines.append(
                "polygon issues: "
                + ", ".join(
                    f"{issue.cell_id} ({issue.reason})" for issue in self.polygon_issues[:5]
                )
            )
        if self.overlapping_pairs:
            lines.append(
                "overlaps: "
                + ", ".join(f"{left}/{right}" for left, right in self.overlapping_pairs[:5])
            )
        if self.missing_neighbor_cells:
            lines.append(
                "missing neighbor refs: "
                + ", ".join(
                    f"{cell}->{neighbor}" for cell, neighbor in self.missing_neighbor_cells[:5]
                )
            )
        if self.asymmetric_neighbor_links:
            lines.append(
                "asymmetric links: "
                + ", ".join(
                    f"{left}<->{right}" for left, right in self.asymmetric_neighbor_links[:5]
                )
            )
        if self.duplicate_neighbor_cells:
            lines.append("duplicate neighbor ids: " + ", ".join(self.duplicate_neighbor_cells[:5]))
        if self.disconnected_components:
            component_sizes = ", ".join(
                str(len(component)) for component in self.disconnected_components
            )
            lines.append(f"disconnected graph components: {component_sizes}")
        if self.edge_multiplicity_issues:
            lines.append(
                "edge multiplicity issues: "
                + ", ".join(
                    f"{issue.owners} x{issue.multiplicity}"
                    for issue in self.edge_multiplicity_issues[:5]
                )
            )
        if self.surface_component_count is not None and self.surface_component_count != 1:
            lines.append(f"surface components: {self.surface_component_count}")
        if self.hole_count:
            lines.append(f"surface holes: {self.hole_count}")
        return tuple(lines)


def _canonical_edge(
    left: tuple[float, float],
    right: tuple[float, float],
) -> tuple[tuple[float, float], tuple[float, float]]:
    normalized_left = (
        round(left[0], _COORDINATE_PRECISION),
        round(left[1], _COORDINATE_PRECISION),
    )
    normalized_right = (
        round(right[0], _COORDINATE_PRECISION),
        round(right[1], _COORDINATE_PRECISION),
    )
    return (
        (normalized_left, normalized_right)
        if normalized_left <= normalized_right
        else (normalized_right, normalized_left)
    )


def _canonical_cell_pair(left: str, right: str) -> tuple[str, str]:
    return (left, right) if left <= right else (right, left)


def topology_polygons(topology: LatticeTopology) -> dict[str, Polygon]:
    # For periodic-face tilings, snap each vertex to _COORDINATE_PRECISION
    # (6 decimals) before constructing the Shapely polygon. Without this,
    # two cells whose shared edge endpoint was computed by different float
    # paths (e.g. one used the rounded JSON value 90.066642 and another
    # used the unrounded 52*sqrt(3) = 90.06664199358...) can end up with
    # the shared edge offset by ~1e-7, which Shapely reports as a tiny
    # intersection area and the overlap validator flags as a real overlap.
    # The edge-key path in periodic_face_tilings._edge_key already rounds
    # to the same precision, so snapping here just brings the validator in
    # line with the builder.
    #
    # Aperiodic substitution families intentionally use sub-1e-6 precision
    # for their irrational vertex coordinates (golden ratio, sqrt(3)/3
    # etc.) and snap-to-6-decimals breaks their surface-union analysis, so
    # we scope the snap to periodic-face geometries.
    from backend.simulation.periodic_face_tilings import is_periodic_face_tiling

    snap = is_periodic_face_tiling(topology.geometry)
    polygons: dict[str, Polygon] = {}
    for cell in topology.cells:
        if cell.vertices is None:
            continue
        if snap:
            vertices = tuple(
                (round(x, _COORDINATE_PRECISION), round(y, _COORDINATE_PRECISION))
                for x, y in cell.vertices
            )
            polygons[cell.id] = Polygon(vertices)
        else:
            polygons[cell.id] = Polygon(cell.vertices)
    return polygons


def analyze_topology_overlap_areas(
    topology: LatticeTopology,
    *,
    top_limit: int = 10,
) -> TopologyOverlapAreaDiagnostics:
    polygons = topology_polygons(topology)
    overlap_tolerance = _overlap_area_tolerance(topology.geometry)
    overlap_pairs: list[OverlapAreaPair] = []
    cell_ids = tuple(sorted(polygons))
    for left_id, right_id in combinations(cell_ids, 2):
        left_polygon = polygons[left_id]
        right_polygon = polygons[right_id]
        if not _bounds_overlap(left_polygon, right_polygon):
            continue
        area = left_polygon.intersection(right_polygon).area
        if area <= overlap_tolerance:
            continue
        overlap_pairs.append(
            OverlapAreaPair(
                left_id=left_id,
                right_id=right_id,
                area=float(area),
            )
        )
    overlap_pairs.sort(key=lambda pair: (-pair.area, pair.left_id, pair.right_id))
    return TopologyOverlapAreaDiagnostics(
        pair_count=len(overlap_pairs),
        max_area=(overlap_pairs[0].area if overlap_pairs else 0.0),
        top_pairs=tuple(overlap_pairs[: max(0, int(top_limit))]),
    )


def _bounds_overlap(left: Polygon, right: Polygon) -> bool:
    left_min_x, left_min_y, left_max_x, left_max_y = left.bounds
    right_min_x, right_min_y, right_max_x, right_max_y = right.bounds
    return not (
        left_max_x < right_min_x
        or right_max_x < left_min_x
        or left_max_y < right_min_y
        or right_max_y < left_min_y
    )


def _significant_surface_hole_count(
    surfaces: tuple[Polygon, ...],
    geometry: str | None = None,
) -> int:
    tolerance = _surface_hole_area_tolerance(geometry)
    count = 0
    for surface in surfaces:
        for interior in surface.interiors:
            if Polygon(interior).area > tolerance:
                count += 1
    return count


def build_topology_graph(topology: LatticeTopology) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(cell.id for cell in topology.cells)
    for cell in topology.cells:
        for neighbor_id in cell.neighbors:
            if neighbor_id is None or not topology.has_cell(neighbor_id):
                continue
            graph.add_edge(cell.id, neighbor_id)
    return graph


def recommended_validation_options(geometry: str) -> dict[str, bool]:
    # ``check_surface`` is driven by the aperiodic family manifest's
    # ``polygon_surface_check`` field: families whose substitution
    # inherently produces T-junctions and point-only cell contacts (e.g.
    # pinwheel-2-1) disable it because Shapely's polygon-union surface
    # check sees depth-specific disconnections even though the
    # cell-adjacency graph is connected. The other validation modes apply
    # to every geometry; see docs/TILING_KNOWN_DEVIATIONS.md for the
    # full rationale for any family that turns it off.
    manifest_entry = APERIODIC_FAMILY_MANIFEST.get(geometry)
    check_surface = manifest_entry.polygon_surface_check if manifest_entry is not None else True
    return {
        "check_surface": check_surface,
        "check_overlaps": True,
        "check_edge_multiplicity": True,
        "check_graph_connectivity": True,
    }


def validate_topology(
    topology: LatticeTopology,
    *,
    check_surface: bool = True,
    check_overlaps: bool = True,
    check_edge_multiplicity: bool = True,
    check_graph_connectivity: bool = True,
) -> TopologyValidationResult:
    polygons = topology_polygons(topology)
    polygon_issues: list[PolygonIssue] = []
    overlaps: set[tuple[str, str]] = set()
    missing_neighbors: set[tuple[str, str]] = set()
    asymmetric_links: set[tuple[str, str]] = set()
    duplicate_neighbor_cells: list[str] = []
    edge_map: dict[tuple[tuple[float, float], tuple[float, float]], list[str]] = {}

    for cell in topology.cells:
        filtered_neighbors = tuple(
            neighbor_id for neighbor_id in cell.neighbors if neighbor_id is not None
        )
        if len(filtered_neighbors) != len(set(filtered_neighbors)):
            duplicate_neighbor_cells.append(cell.id)

        for neighbor_id in filtered_neighbors:
            if not topology.has_cell(neighbor_id):
                missing_neighbors.add((cell.id, neighbor_id))
                continue
            if cell.id not in topology.get_cell(neighbor_id).neighbors:
                asymmetric_links.add(_canonical_cell_pair(cell.id, neighbor_id))

        if cell.vertices is None:
            continue

        polygon = polygons[cell.id]
        if not polygon.is_valid:
            polygon_issues.append(PolygonIssue(cell.id, explain_validity(polygon)))
        if polygon.area <= _AREA_TOLERANCE:
            polygon_issues.append(PolygonIssue(cell.id, "non-positive area"))

        for index, left in enumerate(cell.vertices):
            right = cell.vertices[(index + 1) % len(cell.vertices)]
            edge_map.setdefault(_canonical_edge(left, right), []).append(cell.id)

    if check_overlaps:
        overlap_tolerance = _overlap_area_tolerance(topology.geometry)
        cell_ids = tuple(sorted(polygons))
        for left_id, right_id in combinations(cell_ids, 2):
            left_polygon = polygons[left_id]
            right_polygon = polygons[right_id]
            if not _bounds_overlap(left_polygon, right_polygon):
                continue
            if left_polygon.intersection(right_polygon).area > overlap_tolerance:
                overlaps.add((left_id, right_id))

    edge_multiplicity_issues: tuple[EdgeMultiplicityIssue, ...] = ()
    if check_edge_multiplicity:
        edge_multiplicity_issues = tuple(
            EdgeMultiplicityIssue(
                edge=edge,
                multiplicity=len(unique_owners),
                owners=unique_owners,
            )
            for edge, owners in sorted(edge_map.items())
            for unique_owners in (tuple(dict.fromkeys(owners)),)
            if len(unique_owners) not in {1, 2}
        )

    graph = build_topology_graph(topology)
    disconnected_components: tuple[tuple[str, ...], ...] = ()
    if check_graph_connectivity and graph.number_of_nodes() > 0:
        components = tuple(tuple(sorted(component)) for component in nx.connected_components(graph))
        if len(components) > 1:
            disconnected_components = components

    surface_component_count: int | None = None
    hole_count = 0
    if polygons and check_surface:
        merged_surface = unary_union(list(polygons.values()))
        if merged_surface.geom_type == "Polygon":
            surfaces = (merged_surface,)
        else:
            surfaces = tuple(
                geometry
                for geometry in getattr(merged_surface, "geoms", ())
                if geometry.geom_type == "Polygon"
            )
        surface_component_count = len(surfaces)
        hole_count = _significant_surface_hole_count(surfaces, topology.geometry)

    return TopologyValidationResult(
        geometry=topology.geometry,
        checked_cell_count=topology.cell_count,
        polygon_issues=tuple(polygon_issues),
        overlapping_pairs=tuple(sorted(overlaps)),
        missing_neighbor_cells=tuple(sorted(missing_neighbors)),
        asymmetric_neighbor_links=tuple(sorted(asymmetric_links)),
        duplicate_neighbor_cells=tuple(sorted(duplicate_neighbor_cells)),
        disconnected_components=disconnected_components,
        edge_multiplicity_issues=edge_multiplicity_issues,
        surface_component_count=surface_component_count,
        hole_count=hole_count,
    )
