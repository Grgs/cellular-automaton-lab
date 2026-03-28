from __future__ import annotations

from collections import OrderedDict, deque
from dataclasses import dataclass, field
from math import atan2, pi, sqrt
from collections.abc import Iterable, Iterator

from backend.simulation.topology import LatticeCell, LatticeTopology, SimulationBoard, parse_regular_cell_id
from backend.simulation.topology_catalog import EDGE_ADJACENCY, get_topology_variant_for_geometry

_ANGLE_EPSILON = 1e-9
_CLOCKWISE_START = pi / 2


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


_MAX_TOPOLOGY_FRAME_CACHE_SIZE = 32
_TOPOLOGY_FRAME_CACHE: OrderedDict[str, TopologyFrame] = OrderedDict()


def _normalize_angle(angle: float) -> float:
    while angle <= -pi:
        angle += 2 * pi
    while angle > pi:
        angle -= 2 * pi
    return angle


def _clockwise_sort_key(angle: float) -> float:
    return (_CLOCKWISE_START - angle) % (2 * pi)


def _triangle_vertices(x: int, y: int) -> tuple[tuple[float, float], ...]:
    side = 1.0
    height = (sqrt(3) * side) / 2.0
    horizontal_pitch = side / 2.0
    left_x = x * horizontal_pitch
    top_y = y * height
    if (x + y) % 2 == 0:
        return (
            (left_x, top_y + height),
            (left_x + (side / 2.0), top_y),
            (left_x + side, top_y + height),
        )
    return (
        (left_x, top_y),
        (left_x + side, top_y),
        (left_x + (side / 2.0), top_y + height),
    )


def _hex_center(x: int, y: int) -> tuple[float, float]:
    radius = 0.5
    hex_width = sqrt(3) * radius
    vertical_pitch = 0.75
    return (
        (x * hex_width) + ((y % 2) * (hex_width / 2.0)),
        y * vertical_pitch,
    )


def _hex_vertices(x: int, y: int) -> tuple[tuple[float, float], ...]:
    center_x, center_y = _hex_center(x, y)
    radius = 0.5
    half_width = (sqrt(3) * radius) / 2.0
    return (
        (center_x, center_y - radius),
        (center_x + half_width, center_y - (radius / 2.0)),
        (center_x + half_width, center_y + (radius / 2.0)),
        (center_x, center_y + radius),
        (center_x - half_width, center_y + (radius / 2.0)),
        (center_x - half_width, center_y - (radius / 2.0)),
    )


def _square_vertices(x: int, y: int) -> tuple[tuple[float, float], ...]:
    left = float(x)
    top = float(y)
    return (
        (left, top),
        (left + 1.0, top),
        (left + 1.0, top + 1.0),
        (left, top + 1.0),
    )


def _regular_kind(geometry: str, x: int, y: int) -> str:
    if geometry == "hex":
        return "hexagon"
    if geometry == "triangle":
        return "triangle-up" if (x + y) % 2 == 0 else "triangle-down"
    return "square"


def _regular_geometry(
    geometry: str,
    x: int,
    y: int,
) -> tuple[str, tuple[float, float], tuple[tuple[float, float], ...] | None]:
    if geometry == "hex":
        center = _hex_center(x, y)
        return _regular_kind(geometry, x, y), center, _hex_vertices(x, y)
    if geometry == "triangle":
        vertices = _triangle_vertices(x, y)
        center = (
            sum(vertex[0] for vertex in vertices) / 3.0,
            sum(vertex[1] for vertex in vertices) / 3.0,
        )
        return _regular_kind(geometry, x, y), center, vertices

    vertices = _square_vertices(x, y)
    center = (x + 0.5, y + 0.5)
    return _regular_kind(geometry, x, y), center, vertices


def _cell_regular_coordinates(cell: LatticeCell) -> tuple[int, int] | None:
    return parse_regular_cell_id(cell.id)


def _cell_geometry(topology: LatticeTopology, cell: LatticeCell) -> tuple[str, tuple[float, float], tuple[tuple[float, float], ...] | None]:
    regular_coordinates = _cell_regular_coordinates(cell)
    if cell.center is not None:
        return (
            (
                cell.kind
                if cell.kind != "cell" or regular_coordinates is None
                else _regular_kind(topology.geometry, regular_coordinates[0], regular_coordinates[1])
            ),
            cell.center,
            cell.vertices,
        )
    if regular_coordinates is None:
        raise ValueError(f"Cell {cell.id!r} is missing geometry metadata and is not a regular cell id.")
    return _regular_geometry(topology.geometry, regular_coordinates[0], regular_coordinates[1])


def _board_bounds(
    vertex_sets: Iterable[tuple[tuple[float, float], ...] | None],
    centers: Iterable[tuple[float, float]],
) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for vertices in vertex_sets:
        if not vertices:
            continue
        xs.extend(vertex[0] for vertex in vertices)
        ys.extend(vertex[1] for vertex in vertices)
    if not xs or not ys:
        centers_list = list(centers)
        xs = [center[0] for center in centers_list]
        ys = [center[1] for center in centers_list]
    return (
        min(xs, default=0.0),
        min(ys, default=0.0),
        max(xs, default=0.0),
        max(ys, default=0.0),
    )


def _topology_adjacency_mode(topology: LatticeTopology) -> str:
    try:
        return get_topology_variant_for_geometry(topology.geometry).adjacency_mode
    except KeyError:
        return EDGE_ADJACENCY


def topology_frame_for(topology: LatticeTopology) -> TopologyFrame:
    cached = _TOPOLOGY_FRAME_CACHE.get(topology.topology_revision)
    if cached is not None:
        _TOPOLOGY_FRAME_CACHE.move_to_end(topology.topology_revision)
        return cached

    cell_records = []
    for cell in topology.cells:
        kind, center, vertices = _cell_geometry(topology, cell)
        cell_records.append((cell, kind, center, vertices))

    centers = [record[2] for record in cell_records]
    if centers:
        board_center = (
            sum(center[0] for center in centers) / len(centers),
            sum(center[1] for center in centers) / len(centers),
        )
    else:
        board_center = (0.0, 0.0)

    bounds = _board_bounds((record[3] for record in cell_records), centers)
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
            unsorted_neighbors.append((_clockwise_sort_key(angle), distance, neighbor_index))

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

            angle_delta = _normalize_angle(polar_angles[neighbor_index] - polar_angles[index])
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
        adjacency_mode=_topology_adjacency_mode(topology),
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


@dataclass(frozen=True)
class NeighborSelection:
    id: str
    state: int
    kind: str
    radial: str
    turn: str
    radial_delta: float
    angle_delta: float
    clockwise_index: int
    shell_rank: int
    radial_ratio: float


class RuleContext:
    __slots__ = ("_frame", "_cell_states", "_index")

    def __init__(self, frame: TopologyFrame, cell_states: list[int], index: int) -> None:
        self._frame = frame
        self._cell_states = cell_states
        self._index = index

    @property
    def frame(self) -> TopologyFrame:
        return self._frame

    @property
    def current_state(self) -> int:
        return int(self._cell_states[self._index])

    @property
    def cell_id(self) -> str:
        return self._frame.cells[self._index].id

    @property
    def kind(self) -> str:
        return self._frame.cells[self._index].kind

    @property
    def degree(self) -> int:
        return self._frame.cells[self._index].degree

    @property
    def shell_rank(self) -> int:
        return self._frame.cells[self._index].shell_rank

    @property
    def radial_distance(self) -> float:
        return self._frame.cells[self._index].radial_distance

    @property
    def radial_ratio(self) -> float:
        return self._frame.cells[self._index].radial_ratio

    @property
    def polar_angle(self) -> float:
        return self._frame.cells[self._index].polar_angle

    @property
    def center(self) -> tuple[float, float]:
        return self._frame.cells[self._index].center

    @property
    def vertices(self) -> tuple[tuple[float, float], ...] | None:
        return self._frame.cells[self._index].vertices

    @property
    def board_center(self) -> tuple[float, float]:
        return self._frame.center

    @property
    def cell_count(self) -> int:
        return self._frame.cell_count

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return self._frame.bounds

    @property
    def topology_revision(self) -> str:
        return self._frame.topology_revision

    def for_cell_id(self, cell_id: str) -> "RuleContext":
        return RuleContext(self._frame, self._cell_states, self._frame.index_for(cell_id))

    def has_cell(self, cell_id: str) -> bool:
        return self._frame.has_cell(cell_id)

    def state_for(self, cell_id: str) -> int:
        return int(self._cell_states[self._frame.index_for(cell_id)])

    def kind_for(self, cell_id: str) -> str:
        return self._frame.cell_for(cell_id).kind

    def shell_rank_for(self, cell_id: str) -> int:
        return self._frame.cell_for(cell_id).shell_rank

    def radial_ratio_for(self, cell_id: str) -> float:
        return self._frame.cell_for(cell_id).radial_ratio

    def neighbor_ids(self, *, cell_id: str | None = None) -> tuple[str, ...]:
        resolved_index = self._index if cell_id is None else self._frame.index_for(cell_id)
        return tuple(
            self._frame.cells[neighbor.index].id
            for neighbor in self._frame.cells[resolved_index].neighbors
        )

    def neighbor_states(self, *, cell_id: str | None = None) -> tuple[int, ...]:
        resolved_index = self._index if cell_id is None else self._frame.index_for(cell_id)
        return tuple(
            int(self._cell_states[neighbor.index])
            for neighbor in self._frame.cells[resolved_index].neighbors
        )

    def count_neighbors(
        self,
        *states: int,
        radial: str | None = None,
        turn: str | None = None,
        cell_id: str | None = None,
    ) -> int:
        allowed = None if not states else set(states)
        return sum(
            1
            for selection in self._iter_neighbor_selections(cell_id=cell_id)
            if (allowed is None or selection.state in allowed)
            and (radial is None or selection.radial == radial)
            and (turn is None or selection.turn == turn)
        )

    def count_live_neighbors(
        self,
        *,
        radial: str | None = None,
        turn: str | None = None,
        cell_id: str | None = None,
    ) -> int:
        return self.count_neighbors(radial=radial, turn=turn, cell_id=cell_id) - self.count_neighbors(
            0,
            radial=radial,
            turn=turn,
            cell_id=cell_id,
        )

    def has_neighbor_state(
        self,
        *states: int,
        radial: str | None = None,
        turn: str | None = None,
        cell_id: str | None = None,
    ) -> bool:
        return any(
            True
            for _ in self._iter_neighbor_selections(
                states=states,
                radial=radial,
                turn=turn,
                cell_id=cell_id,
            )
        )

    def neighbor_ids_with(
        self,
        *states: int,
        radial: str | None = None,
        turn: str | None = None,
        cell_id: str | None = None,
    ) -> tuple[str, ...]:
        return tuple(
            selection.id
            for selection in self._iter_neighbor_selections(
                states=states,
                radial=radial,
                turn=turn,
                cell_id=cell_id,
            )
        )

    def directional_counts(self, *states: int, cell_id: str | None = None) -> dict[str, int]:
        return {
            "outward": self.count_neighbors(*states, radial="outward", cell_id=cell_id),
            "inward": self.count_neighbors(*states, radial="inward", cell_id=cell_id),
            "clockwise": self.count_neighbors(*states, turn="clockwise", cell_id=cell_id),
            "counterclockwise": self.count_neighbors(*states, turn="counterclockwise", cell_id=cell_id),
            "total": self.count_neighbors(*states, cell_id=cell_id),
        }

    def in_shell(self, *ranks: int) -> bool:
        return self.shell_rank in ranks

    def select_neighbor(
        self,
        *states: int,
        tiers: tuple[tuple[str | None, str | None], ...],
        cell_id: str | None = None,
    ) -> NeighborSelection | None:
        candidates: list[tuple[tuple[float, float, float, int], NeighborSelection]] = []
        for selection in self._iter_neighbor_selections(states=states, cell_id=cell_id):
            tier_index = next(
                (
                    index
                    for index, (radial, turn) in enumerate(tiers)
                    if (radial is None or selection.radial == radial)
                    and (turn is None or selection.turn == turn)
                ),
                None,
            )
            if tier_index is None:
                continue
            radial_score = max(0.0, -selection.radial_delta)
            turn_score = max(0.0, -selection.angle_delta) if selection.turn == "clockwise" else 0.0
            candidates.append(
                (
                    (
                        float(tier_index),
                        -radial_score,
                        -turn_score,
                        selection.clockwise_index,
                    ),
                    selection,
                )
            )
        if not candidates:
            return None
        return min(candidates, key=lambda candidate: candidate[0])[1]

    def select_neighbor_id(
        self,
        *states: int,
        tiers: tuple[tuple[str | None, str | None], ...],
        cell_id: str | None = None,
    ) -> str | None:
        selected = self.select_neighbor(*states, tiers=tiers, cell_id=cell_id)
        return None if selected is None else selected.id

    def _iter_neighbor_selections(
        self,
        *,
        states: tuple[int, ...] = (),
        radial: str | None = None,
        turn: str | None = None,
        cell_id: str | None = None,
    ) -> Iterator[NeighborSelection]:
        allowed = None if not states else set(states)
        resolved_index = self._index if cell_id is None else self._frame.index_for(cell_id)
        for neighbor in self._frame.cells[resolved_index].neighbors:
            frame_cell = self._frame.cells[neighbor.index]
            state = int(self._cell_states[neighbor.index])
            if allowed is not None and state not in allowed:
                continue
            if radial is not None and neighbor.radial != radial:
                continue
            if turn is not None and neighbor.turn != turn:
                continue
            yield NeighborSelection(
                id=frame_cell.id,
                state=state,
                kind=frame_cell.kind,
                radial=neighbor.radial,
                turn=neighbor.turn,
                radial_delta=neighbor.radial_delta,
                angle_delta=neighbor.angle_delta,
                clockwise_index=neighbor.clockwise_index,
                shell_rank=frame_cell.shell_rank,
                radial_ratio=frame_cell.radial_ratio,
            )


def build_rule_contexts_for_board(board: SimulationBoard) -> tuple[RuleContext, ...]:
    frame = topology_frame_for(board.topology)
    return tuple(
        RuleContext(frame, board.cell_states, index)
        for index in range(frame.cell_count)
    )
