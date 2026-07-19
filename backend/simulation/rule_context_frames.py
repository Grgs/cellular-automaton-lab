from __future__ import annotations

from collections import OrderedDict, deque
from dataclasses import dataclass, field
from math import atan2
from typing import Protocol, overload

from backend.simulation.rule_context_geometry import (
    board_bounds,
    cell_geometry,
    clockwise_sort_key,
    normalize_angle,
    topology_adjacency_mode,
)
from backend.simulation.rule_frame_capabilities import (
    DIRECTIONAL_FRAME_CAPABILITIES,
    RuleFrameCapabilities,
)
from backend.simulation.topology_types import LatticeTopology

_ANGLE_EPSILON = 1e-9
# Sized to comfortably hold every shipped tiling's frame at once, so a
# cross-topology comparison sweep (and repeated sweeps) never thrash the LRU and
# rebuild frames it just evicted. The live app only ever touches a handful.
_MAX_TOPOLOGY_FRAME_CACHE_SIZE = 128


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


class RuleFrame(Protocol):
    @property
    def adjacency_mode(self) -> str: ...

    @property
    def topology_revision(self) -> str: ...

    @property
    def center(self) -> tuple[float, float]: ...

    @property
    def cell_count(self) -> int: ...

    @property
    def bounds(self) -> tuple[float, float, float, float]: ...

    @property
    def max_shell_rank(self) -> int: ...

    @property
    def max_radial_distance(self) -> float: ...

    @property
    def cells(self) -> tuple[TopologyCellFrame, ...]: ...

    def has_cell(self, cell_id: str) -> bool: ...

    def index_for(self, cell_id: str) -> int: ...

    def cell_for(self, cell_id: str) -> TopologyCellFrame: ...

    def cell_id_for(self, index: int) -> str: ...

    def cell_kind_for(self, index: int) -> str: ...

    def degree_for(self, index: int) -> int: ...

    def shell_rank_for(self, index: int) -> int: ...

    def radial_distance_for(self, index: int) -> float: ...

    def radial_ratio_for(self, index: int) -> float: ...

    def polar_angle_for(self, index: int) -> float: ...

    def center_for(self, index: int) -> tuple[float, float]: ...

    def vertices_for(self, index: int) -> tuple[tuple[float, float], ...] | None: ...

    def neighbor_indexes_for(self, index: int) -> tuple[int, ...]: ...

    def neighbor_frames_for(self, index: int) -> tuple[TopologyNeighborFrame, ...]: ...


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

    def cell_id_for(self, index: int) -> str:
        return self.cells[index].id

    def cell_kind_for(self, index: int) -> str:
        return self.cells[index].kind

    def degree_for(self, index: int) -> int:
        return self.cells[index].degree

    def shell_rank_for(self, index: int) -> int:
        return self.cells[index].shell_rank

    def radial_distance_for(self, index: int) -> float:
        return self.cells[index].radial_distance

    def radial_ratio_for(self, index: int) -> float:
        return self.cells[index].radial_ratio

    def polar_angle_for(self, index: int) -> float:
        return self.cells[index].polar_angle

    def center_for(self, index: int) -> tuple[float, float]:
        return self.cells[index].center

    def vertices_for(self, index: int) -> tuple[tuple[float, float], ...] | None:
        return self.cells[index].vertices

    def neighbor_indexes_for(self, index: int) -> tuple[int, ...]:
        return tuple(neighbor.index for neighbor in self.cells[index].neighbors)

    def neighbor_frames_for(self, index: int) -> tuple[TopologyNeighborFrame, ...]:
        return self.cells[index].neighbors


class AdjacencyTopologyFrame:
    """Compact frame for rules that need only cell identity and adjacency.

    The legacy ``cells`` view is retained lazily for custom rules that explicitly
    opt into adjacency-only capabilities but still inspect the historical frame
    surface. Built-in batch rules use the raw accessors and never pay that cost.
    """

    __slots__ = (
        "_cell_ids",
        "_cell_kinds",
        "_index_by_id",
        "_legacy_cells",
        "_neighbor_indexes",
        "adjacency_mode",
        "bounds",
        "cell_count",
        "center",
        "max_radial_distance",
        "max_shell_rank",
        "topology_revision",
    )

    def __init__(
        self,
        *,
        adjacency_mode: str,
        topology_revision: str,
        cell_ids: tuple[str, ...],
        cell_kinds: tuple[str, ...],
        neighbor_indexes: tuple[tuple[int, ...], ...],
    ) -> None:
        self.adjacency_mode = adjacency_mode
        self.topology_revision = topology_revision
        self.center = (0.0, 0.0)
        self.cell_count = len(cell_ids)
        self.bounds = (0.0, 0.0, 0.0, 0.0)
        self.max_shell_rank = 0
        self.max_radial_distance = 0.0
        self._cell_ids = cell_ids
        self._cell_kinds = cell_kinds
        self._neighbor_indexes = neighbor_indexes
        self._index_by_id = {cell_id: index for index, cell_id in enumerate(cell_ids)}
        self._legacy_cells: tuple[TopologyCellFrame, ...] | None = None

    @property
    def cells(self) -> tuple[TopologyCellFrame, ...]:
        cells = self._legacy_cells
        if cells is None:
            cells = tuple(
                TopologyCellFrame(
                    id=cell_id,
                    kind=self._cell_kinds[index],
                    center=(0.0, 0.0),
                    vertices=None,
                    degree=len(self._neighbor_indexes[index]),
                    shell_rank=0,
                    radial_distance=0.0,
                    radial_ratio=0.0,
                    polar_angle=0.0,
                    neighbors=self.neighbor_frames_for(index),
                )
                for index, cell_id in enumerate(self._cell_ids)
            )
            self._legacy_cells = cells
        return cells

    @property
    def legacy_cells_materialized(self) -> bool:
        return self._legacy_cells is not None

    def has_cell(self, cell_id: str) -> bool:
        return cell_id in self._index_by_id

    def index_for(self, cell_id: str) -> int:
        return self._index_by_id[cell_id]

    def cell_for(self, cell_id: str) -> TopologyCellFrame:
        return self.cells[self.index_for(cell_id)]

    def cell_id_for(self, index: int) -> str:
        return self._cell_ids[index]

    def cell_kind_for(self, index: int) -> str:
        return self._cell_kinds[index]

    def degree_for(self, index: int) -> int:
        return len(self._neighbor_indexes[index])

    def shell_rank_for(self, index: int) -> int:
        return 0

    def radial_distance_for(self, index: int) -> float:
        return 0.0

    def radial_ratio_for(self, index: int) -> float:
        return 0.0

    def polar_angle_for(self, index: int) -> float:
        return 0.0

    def center_for(self, index: int) -> tuple[float, float]:
        return (0.0, 0.0)

    def vertices_for(self, index: int) -> tuple[tuple[float, float], ...] | None:
        return None

    def neighbor_indexes_for(self, index: int) -> tuple[int, ...]:
        return self._neighbor_indexes[index]

    def neighbor_frames_for(self, index: int) -> tuple[TopologyNeighborFrame, ...]:
        return tuple(
            TopologyNeighborFrame(
                index=neighbor_index,
                radial="level",
                turn="aligned",
                radial_delta=0.0,
                angle_delta=0.0,
                clockwise_index=clockwise_index,
            )
            for clockwise_index, neighbor_index in enumerate(self._neighbor_indexes[index])
        )


_TOPOLOGY_FRAME_CACHE: OrderedDict[tuple[str, RuleFrameCapabilities], RuleFrame] = OrderedDict()


def _adjacency_frame_for(topology: LatticeTopology) -> AdjacencyTopologyFrame:
    return AdjacencyTopologyFrame(
        adjacency_mode=topology_adjacency_mode(topology),
        topology_revision=topology.topology_revision,
        cell_ids=tuple(cell.id for cell in topology.cells),
        cell_kinds=tuple(cell.kind for cell in topology.cells),
        neighbor_indexes=tuple(
            tuple(
                neighbor_index
                for neighbor_index in topology.neighbor_indexes_for(cell_index)
                if neighbor_index >= 0
            )
            for cell_index in range(topology.cell_count)
        ),
    )


@overload
def topology_frame_for(topology: LatticeTopology) -> TopologyFrame: ...


@overload
def topology_frame_for(
    topology: LatticeTopology,
    capabilities: RuleFrameCapabilities,
) -> RuleFrame: ...


def topology_frame_for(
    topology: LatticeTopology,
    capabilities: RuleFrameCapabilities | None = None,
) -> RuleFrame:
    capabilities = capabilities or DIRECTIONAL_FRAME_CAPABILITIES
    cache_key = (topology.topology_revision, capabilities)
    cached = _TOPOLOGY_FRAME_CACHE.get(cache_key)
    if cached is not None:
        _TOPOLOGY_FRAME_CACHE.move_to_end(cache_key)
        return cached

    if not capabilities.spatial and not capabilities.directional:
        adjacency_frame = _adjacency_frame_for(topology)
        _TOPOLOGY_FRAME_CACHE[cache_key] = adjacency_frame
        _TOPOLOGY_FRAME_CACHE.move_to_end(cache_key)
        while len(_TOPOLOGY_FRAME_CACHE) > _MAX_TOPOLOGY_FRAME_CACHE_SIZE:
            _TOPOLOGY_FRAME_CACHE.popitem(last=False)
        return adjacency_frame

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
            distance = (
                (neighbor_center[0] - center[0]) ** 2 + (neighbor_center[1] - center[1]) ** 2
            ) ** 0.5
            unsorted_neighbors.append((clockwise_sort_key(angle), distance, neighbor_index))

        ordered_neighbors: list[TopologyNeighborFrame] = []
        for clockwise_index, (_, _distance, neighbor_index) in enumerate(
            sorted(unsorted_neighbors)
        ):
            neighbor_radius = (
                radial_distances[neighbor_index] if neighbor_index < len(radial_distances) else 0.0
            )
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

        radial_ratio = (
            0.0 if max_radial_distance <= 0.0 else radial_distances[index] / max_radial_distance
        )
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

    topology_frame = TopologyFrame(
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
    _TOPOLOGY_FRAME_CACHE[cache_key] = topology_frame
    _TOPOLOGY_FRAME_CACHE.move_to_end(cache_key)
    while len(_TOPOLOGY_FRAME_CACHE) > _MAX_TOPOLOGY_FRAME_CACHE_SIZE:
        _TOPOLOGY_FRAME_CACHE.popitem(last=False)
    return topology_frame
