from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from backend.simulation.rule_context_frames import RuleFrame, topology_frame_for
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

    def __init__(self, frame: RuleFrame, cell_states: list[int], index: int) -> None:
        self._frame = frame
        self._cell_states = cell_states
        self._index = index

    @property
    def frame(self) -> RuleFrame:
        return self._frame

    @property
    def current_state(self) -> int:
        return int(self._cell_states[self._index])

    @property
    def cell_id(self) -> str:
        return self._frame.cell_id_for(self._index)

    @property
    def kind(self) -> str:
        return self._frame.cell_kind_for(self._index)

    @property
    def degree(self) -> int:
        return self._frame.degree_for(self._index)

    @property
    def shell_rank(self) -> int:
        return self._frame.shell_rank_for(self._index)

    @property
    def radial_distance(self) -> float:
        return self._frame.radial_distance_for(self._index)

    @property
    def radial_ratio(self) -> float:
        return self._frame.radial_ratio_for(self._index)

    @property
    def polar_angle(self) -> float:
        return self._frame.polar_angle_for(self._index)

    @property
    def center(self) -> tuple[float, float]:
        return self._frame.center_for(self._index)

    @property
    def vertices(self) -> tuple[tuple[float, float], ...] | None:
        return self._frame.vertices_for(self._index)

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

    def has_cell(self, cell_id: str) -> bool:
        return self._frame.has_cell(cell_id)

    def state_for(self, cell_id: str) -> int:
        return int(self._cell_states[self._frame.index_for(cell_id)])

    def shell_rank_for(self, cell_id: str) -> int:
        return self._frame.shell_rank_for(self._frame.index_for(cell_id))

    def radial_ratio_for(self, cell_id: str) -> float:
        return self._frame.radial_ratio_for(self._frame.index_for(cell_id))

    def neighbor_ids(self, *, cell_id: str | None = None) -> tuple[str, ...]:
        resolved_index = self._index if cell_id is None else self._frame.index_for(cell_id)
        return tuple(
            self._frame.cell_id_for(neighbor_index)
            for neighbor_index in self._frame.neighbor_indexes_for(resolved_index)
        )

    def neighbor_states(self, *, cell_id: str | None = None) -> tuple[int, ...]:
        resolved_index = self._index if cell_id is None else self._frame.index_for(cell_id)
        return tuple(
            int(self._cell_states[neighbor_index])
            for neighbor_index in self._frame.neighbor_indexes_for(resolved_index)
        )

    def count_neighbors(
        self,
        *states: int,
        radial: str | None = None,
        turn: str | None = None,
        cell_id: str | None = None,
    ) -> int:
        # Hot path: count over raw neighbor frames + cell states directly, without
        # materialising a NeighborSelection per neighbor (radial/turn live on the
        # neighbor frame). This is the dominant cost when stepping Life-like rules.
        allowed = states or None
        resolved_index = self._index if cell_id is None else self._frame.index_for(cell_id)
        cell_states = self._cell_states
        if radial is None and turn is None:
            return sum(
                allowed is None or int(cell_states[neighbor_index]) in allowed
                for neighbor_index in self._frame.neighbor_indexes_for(resolved_index)
            )
        count = 0
        for neighbor in self._frame.neighbor_frames_for(resolved_index):
            if radial is not None and neighbor.radial != radial:
                continue
            if turn is not None and neighbor.turn != turn:
                continue
            if allowed is None or int(cell_states[neighbor.index]) in allowed:
                count += 1
        return count

    def count_live_neighbors(
        self,
        *,
        radial: str | None = None,
        turn: str | None = None,
        cell_id: str | None = None,
    ) -> int:
        # Single pass counting non-zero neighbours (no two count_neighbors calls).
        resolved_index = self._index if cell_id is None else self._frame.index_for(cell_id)
        cell_states = self._cell_states
        if radial is None and turn is None:
            return sum(
                cell_states[neighbor_index] != 0
                for neighbor_index in self._frame.neighbor_indexes_for(resolved_index)
            )
        count = 0
        for neighbor in self._frame.neighbor_frames_for(resolved_index):
            if radial is not None and neighbor.radial != radial:
                continue
            if turn is not None and neighbor.turn != turn:
                continue
            if cell_states[neighbor.index] != 0:
                count += 1
        return count

    def has_neighbor_state(
        self,
        *states: int,
        radial: str | None = None,
        turn: str | None = None,
        cell_id: str | None = None,
    ) -> bool:
        allowed = states or None
        resolved_index = self._index if cell_id is None else self._frame.index_for(cell_id)
        cell_states = self._cell_states
        if radial is None and turn is None:
            return any(
                allowed is None or cell_states[neighbor_index] in allowed
                for neighbor_index in self._frame.neighbor_indexes_for(resolved_index)
            )
        for neighbor in self._frame.neighbor_frames_for(resolved_index):
            if radial is not None and neighbor.radial != radial:
                continue
            if turn is not None and neighbor.turn != turn:
                continue
            if allowed is None or cell_states[neighbor.index] in allowed:
                return True
        return False

    def neighbor_ids_with(
        self,
        *states: int,
        radial: str | None = None,
        turn: str | None = None,
        cell_id: str | None = None,
    ) -> tuple[str, ...]:
        allowed = states or None
        resolved_index = self._index if cell_id is None else self._frame.index_for(cell_id)
        cell_states = self._cell_states
        if radial is None and turn is None:
            return tuple(
                self._frame.cell_id_for(neighbor_index)
                for neighbor_index in self._frame.neighbor_indexes_for(resolved_index)
                if allowed is None or cell_states[neighbor_index] in allowed
            )
        return tuple(
            self._frame.cell_id_for(neighbor.index)
            for neighbor in self._frame.neighbor_frames_for(resolved_index)
            if (radial is None or neighbor.radial == radial)
            and (turn is None or neighbor.turn == turn)
            and (allowed is None or cell_states[neighbor.index] in allowed)
        )

    def directional_counts(self, *states: int, cell_id: str | None = None) -> dict[str, int]:
        allowed = states or None
        resolved_index = self._index if cell_id is None else self._frame.index_for(cell_id)
        cell_states = self._cell_states
        outward = inward = clockwise = counterclockwise = total = 0
        for neighbor in self._frame.neighbor_frames_for(resolved_index):
            if allowed is not None and cell_states[neighbor.index] not in allowed:
                continue
            total += 1
            if neighbor.radial == "outward":
                outward += 1
            elif neighbor.radial == "inward":
                inward += 1
            if neighbor.turn == "clockwise":
                clockwise += 1
            elif neighbor.turn == "counterclockwise":
                counterclockwise += 1
        return {
            "outward": outward,
            "inward": inward,
            "clockwise": clockwise,
            "counterclockwise": counterclockwise,
            "total": total,
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
        allowed = states or None
        resolved_index = self._index if cell_id is None else self._frame.index_for(cell_id)
        for neighbor in self._frame.neighbor_frames_for(resolved_index):
            state = int(self._cell_states[neighbor.index])
            if allowed is not None and state not in allowed:
                continue
            if radial is not None and neighbor.radial != radial:
                continue
            if turn is not None and neighbor.turn != turn:
                continue
            yield NeighborSelection(
                id=self._frame.cell_id_for(neighbor.index),
                state=state,
                kind=self._frame.cell_kind_for(neighbor.index),
                radial=neighbor.radial,
                turn=neighbor.turn,
                radial_delta=neighbor.radial_delta,
                angle_delta=neighbor.angle_delta,
                clockwise_index=neighbor.clockwise_index,
                shell_rank=self._frame.shell_rank_for(neighbor.index),
                radial_ratio=self._frame.radial_ratio_for(neighbor.index),
            )


def build_rule_contexts_for_board(board: SimulationBoard) -> tuple[RuleContext, ...]:
    frame = topology_frame_for(board.topology)
    return tuple(RuleContext(frame, board.cell_states, index) for index in range(frame.cell_count))
