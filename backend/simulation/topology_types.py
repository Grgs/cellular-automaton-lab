from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha1

from backend.payload_types import PointPayload, TopologyCellPayload, TopologyPayload
from backend.simulation.topology_catalog import topology_spec_payload

REGULAR_CELL_KIND = "cell"


def regular_cell_id(x: int, y: int) -> str:
    return f"c:{x}:{y}"


def parse_regular_cell_id(cell_id: str) -> tuple[int, int] | None:
    parts = str(cell_id).split(":")
    if len(parts) != 3 or parts[0] != "c":
        return None
    try:
        return int(parts[1]), int(parts[2])
    except ValueError:
        return None


def topology_revision(
    geometry: str,
    width: int,
    height: int,
    patch_depth: int | None = None,
) -> str:
    digest = sha1(
        f"{geometry}:{width}:{height}:{patch_depth if patch_depth is not None else '-'}:graph-v1".encode("utf-8")
    ).hexdigest()
    return digest[:12]


@dataclass(frozen=True)
class LatticeCell:
    id: str
    kind: str
    neighbors: tuple[str | None, ...]
    slot: str | None = None
    center: tuple[float, float] | None = None
    vertices: tuple[tuple[float, float], ...] | None = None
    tile_family: str | None = None
    orientation_token: str | None = None
    chirality_token: str | None = None
    decoration_tokens: tuple[str, ...] | None = None

    def to_dict(self) -> TopologyCellPayload:
        payload: TopologyCellPayload = {
            "id": self.id,
            "kind": self.kind,
            "neighbors": list(self.neighbors),
        }
        if self.slot is not None:
            payload["slot"] = self.slot
        if self.center is not None:
            payload["center"] = PointPayload(x=self.center[0], y=self.center[1])
        if self.vertices is not None:
            payload["vertices"] = [
                PointPayload(x=vertex[0], y=vertex[1])
                for vertex in self.vertices
            ]
        if self.tile_family is not None:
            payload["tile_family"] = self.tile_family
        if self.orientation_token is not None:
            payload["orientation_token"] = self.orientation_token
        if self.chirality_token is not None:
            payload["chirality_token"] = self.chirality_token
        if self.decoration_tokens is not None:
            payload["decoration_tokens"] = list(self.decoration_tokens)
        return payload


@dataclass(frozen=True)
class LatticeTopology:
    geometry: str
    width: int
    height: int
    cells: tuple[LatticeCell, ...]
    topology_revision: str
    patch_depth: int | None = None
    _index_by_id: dict[str, int] = field(init=False, repr=False, compare=False)
    _cell_by_id: dict[str, LatticeCell] = field(init=False, repr=False, compare=False)
    _neighbor_indexes_by_cell: tuple[tuple[int, ...], ...] = field(
        init=False,
        repr=False,
        compare=False,
    )
    _payload: TopologyPayload | None = field(
        default=None,
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        index_by_id = {cell.id: index for index, cell in enumerate(self.cells)}
        object.__setattr__(self, "_index_by_id", index_by_id)
        object.__setattr__(self, "_cell_by_id", {cell.id: cell for cell in self.cells})
        object.__setattr__(
            self,
            "_neighbor_indexes_by_cell",
            tuple(
                tuple(-1 if neighbor_id is None else index_by_id[neighbor_id] for neighbor_id in cell.neighbors)
                for cell in self.cells
            ),
        )

    @property
    def cell_count(self) -> int:
        return len(self.cells)

    def index_for(self, cell_id: str) -> int:
        return self._index_by_id[cell_id]

    def get_cell(self, cell_id: str) -> LatticeCell:
        return self._cell_by_id[cell_id]

    def has_cell(self, cell_id: str) -> bool:
        return cell_id in self._index_by_id

    def neighbor_indexes_for(self, index: int) -> tuple[int, ...]:
        return self._neighbor_indexes_by_cell[index]

    def to_dict(self) -> TopologyPayload:
        if self._payload is None:
            payload: TopologyPayload = {
                "topology_spec": topology_spec_payload(
                    self.geometry,
                    width=self.width,
                    height=self.height,
                    patch_depth=self.patch_depth,
                ),
                "topology_revision": self.topology_revision,
                "cells": [cell.to_dict() for cell in self.cells],
            }
            object.__setattr__(self, "_payload", payload)
        if self._payload is None:
            raise RuntimeError("Topology payload cache was not initialized.")
        return self._payload


@dataclass
class SimulationBoard:
    topology: LatticeTopology
    cell_states: list[int]

    def clone(self) -> "SimulationBoard":
        return SimulationBoard(
            topology=self.topology,
            cell_states=self.cell_states.copy(),
        )

    def state_for(self, cell_id: str) -> int:
        return self.cell_states[self.topology.index_for(cell_id)]

    def set_state_for(self, cell_id: str, state: int) -> None:
        self.cell_states[self.topology.index_for(cell_id)] = state

    def states_by_id(self, *, omit_zero: bool = False) -> dict[str, int]:
        states_by_id: dict[str, int] = {}
        for index, cell in enumerate(self.topology.cells):
            state = int(self.cell_states[index])
            if omit_zero and state == 0:
                continue
            states_by_id[cell.id] = state
        return states_by_id
