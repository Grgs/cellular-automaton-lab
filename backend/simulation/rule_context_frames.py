from __future__ import annotations

from collections import OrderedDict, deque
from dataclasses import dataclass, field
from math import atan2

from backend.simulation.rule_context_geometry import (
    board_bounds,
    cell_geometry,
    clockwise_sort_key,
    normalize_angle,
    topology_adjacency_mode,
)
from backend.simulation.topology_types import LatticeTopology

_ANGLE_EPSILON = 1e-9
_MAX_TOPOLOGY_FRAME_CACHE_SIZE = 32
_TOPOLOGY_FRAME_CACHE: OrderedDict[str, "TopologyFrame"] = OrderedDict()


@dataclass(frozen=True)
class TopologyNeighborFrame:
    index: int
    radial: str
    turn: str
    radial_delta: float
    angle_delta: float
    clockwise_index: int


@dataclass(frozen=True)
class TopologyCellFrame:
    id: str
    kind: str
    center: tuple[float, float]
    vertices: tuple[tuple[float, float], ...] | None
    degree: int
    shell_rank: int
    radial_distance: float
    radial_ratio: float
    polar_angle: float
    neighbors: tuple[TopologyNeighborFrame, ...]


@dataclass(frozen=True)
class TopologyFrame:
    adjacency_mode: str
    topology_revision: str
    center: tuple[float, float]
    cell_count: int
    bounds: tuple[float, float, float, float]
    max_shell_rank: int
    max_radial_distance: float
    cells: tuple[TopologyCellFrame, ...]
    _index_by_id: dict[str, int] = field(repr=False, compare=False)

    def has_cell(self, cell_id: str) -> bool:
        return cell_id in self._index_by_id

    def index_for(self, cell_id: str) -> int:
        return self._index_by_id[cell_id]

    def cell_for(self, cell_id: str) -> TopologyCellFrame:
        return self.cells[self.index_for(cell_id)]


def topology_frame_for(topology: LatticeTopology) -> TopologyFrame:
    cached = _TOPOLOGY_FRAME_CACHE.get(topology.topology_revision)
    if cached is not None:
        _TOPOLOGY_FRAME_CACHE.move_to_end(topology.topology_revision)
        return cached

    cell_records = []
    for cell in topology.cells:
        kind, center, vertices = cell_geometry(topology, cell)
        cell_records.append((cell, kind, center, vertices))

    centers = [record[2] for record in cell_records]
    if centers:
        board_center = (
            sum(center[0] for center in centers) / len(centers),
            sum(center[1] for center in centers) / len(centers),
        )
    else:
        board_center = (0.0, 0.0)

    bounds = board_bounds((record[3] for record in cell_records), centers)
    radial_distances = [
        ((center[0] - board_center[0]) ** 2 + (center[1] - board_center[1]) ** 2) ** 0.5
        for _, _, center, _ in cell_records
    ]
    max_radial_distance = max(radial_distances, default=0.0)
    polar_angles = [
        atan2(-(center[1] - board_center[1]), center[0] - board_center[0])
        for _, _, center, _ in cell_records
    ]

    if radial_distances:
        min_distance = min(radial_distances)
        root_indexes = [
            index
            for index, distance in enumerate(radial_distances)
            if abs(distance - min_distance) <= _ANGLE_EPSILON
        ]
    else:
        root_indexes = []

    shell_ranks = [-1] * len(cell_records)
    queue = deque(root_indexes)
    for root_index in root_indexes:
        shell_ranks[root_index] = 0
    while queue:
        current_index = queue.popleft()
        next_rank = shell_ranks[current_index] + 1
        for neighbor_index in topology.neighbor_indexes_for(current_index):
            if neighbor_index < 0 or shell_ranks[neighbor_index] >= 0:
                continue
            shell_ranks[neighbor_index] = next_rank
            queue.append(neighbor_index)
    for index, rank in enumerate(shell_ranks):
        if rank < 0:
            shell_ranks[index] = 0

    max_shell_rank = max(shell_ranks, default=0)
    frame_cells: list[TopologyCellFrame] = []
    for index, (cell, kind, center, vertices) in enumerate(cell_records):
        unsorted_neighbors: list[tuple[float, float, int]] = []
        for neighbor_index in topology.neighbor_indexes_for(index):
            if neighbor_index < 0:
                continue
            neighbor_center = cell_records[neighbor_index][2]
            angle = atan2(-(neighbor_center[1] - center[1]), neighbor_center[0] - center[0])
            distance = ((neighbor_center[0] - center[0]) ** 2 + (neighbor_center[1] - center[1]) ** 2) ** 0.5
            unsorted_neighbors.append((clockwise_sort_key(angle), distance, neighbor_index))

        ordered_neighbors: list[TopologyNeighborFrame] = []
        for clockwise_index, (_, _distance, neighbor_index) in enumerate(sorted(unsorted_neighbors)):
            neighbor_radius = radial_distances[neighbor_index] if neighbor_index < len(radial_distances) else 0.0
            radial_delta = (
                0.0
                if max_radial_distance <= 0.0
                else (neighbor_radius - radial_distances[index]) / max_radial_distance
            )
            if shell_ranks[neighbor_index] < shell_ranks[index]:
                radial = "inward"
            elif shell_ranks[neighbor_index] > shell_ranks[index]:
                radial = "outward"
            else:
                radial = "level"

            angle_delta = normalize_angle(polar_angles[neighbor_index] - polar_angles[index])
            if abs(angle_delta) <= _ANGLE_EPSILON:
                turn = "aligned"
            elif angle_delta < 0:
                turn = "clockwise"
            else:
                turn = "counterclockwise"

            ordered_neighbors.append(
                TopologyNeighborFrame(
                    index=neighbor_index,
                    radial=radial,
                    turn=turn,
                    radial_delta=radial_delta,
                    angle_delta=angle_delta,
                    clockwise_index=clockwise_index,
                )
            )

        radial_ratio = 0.0 if max_radial_distance <= 0.0 else radial_distances[index] / max_radial_distance
        frame_cells.append(
            TopologyCellFrame(
                id=cell.id,
                kind=kind,
                center=center,
                vertices=vertices,
                degree=len(ordered_neighbors),
                shell_rank=shell_ranks[index],
                radial_distance=radial_distances[index],
                radial_ratio=radial_ratio,
                polar_angle=polar_angles[index],
                neighbors=tuple(ordered_neighbors),
            )
        )

    frame = TopologyFrame(
        adjacency_mode=topology_adjacency_mode(topology),
        topology_revision=topology.topology_revision,
        center=board_center,
        cell_count=len(frame_cells),
        bounds=bounds,
        max_shell_rank=max_shell_rank,
        max_radial_distance=max_radial_distance,
        cells=tuple(frame_cells),
        _index_by_id={frame_cell.id: index for index, frame_cell in enumerate(frame_cells)},
    )
    _TOPOLOGY_FRAME_CACHE[topology.topology_revision] = frame
    _TOPOLOGY_FRAME_CACHE.move_to_end(topology.topology_revision)
    while len(_TOPOLOGY_FRAME_CACHE) > _MAX_TOPOLOGY_FRAME_CACHE_SIZE:
        _TOPOLOGY_FRAME_CACHE.popitem(last=False)
    return frame
