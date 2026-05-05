from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from backend.simulation.rule_context_frames import TopologyFrame, topology_frame_for
from backend.simulation.topology_types import SimulationBoard


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
        return self.count_neighbors(
            radial=radial, turn=turn, cell_id=cell_id
        ) - self.count_neighbors(
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
            "counterclockwise": self.count_neighbors(
                *states, turn="counterclockwise", cell_id=cell_id
            ),
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
    return tuple(RuleContext(frame, board.cell_states, index) for index in range(frame.cell_count))
