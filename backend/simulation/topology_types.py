from __future__ import annotations

import json
from dataclasses import dataclass, field
from hashlib import sha1
from typing import Any

from backend.payload_types import PointPayload, TopologyCellPayload, TopologyPayload
from backend.simulation.topology_catalog import topology_spec_payload

REGULAR_CELL_KIND = "cell"

# Length of the short hex digest returned by ``topology_content_revision``.
# Eight hex chars = 32 bits of namespace, ample for a per-fixture identifier
# while staying readable in checked-in JSON.
CONTENT_REVISION_HASH_LENGTH = 8


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
    """Cheap input-spec hash used as the runtime ``topology_revision``.

    Derived from the topology *inputs* (geometry key + dimensions + patch
    depth), not from the serialized cell stream. Used as a cache key in
    the frontend canvas renderer and as a state-equality token in editor
    history. Cheap to compute on every ``build_topology()`` call.

    For "did the serialized topology change?" — e.g. drift detection on a
    checked-in fixture, where a builder fix would change cells without
    changing inputs — use ``topology_content_revision`` instead.
    """
    digest = sha1(
        f"{geometry}:{width}:{height}:{patch_depth if patch_depth is not None else '-'}:graph-v1".encode()
    ).hexdigest()
    return digest[:12]


def _normalize_negative_zero(value: Any) -> Any:
    """Recursively normalize ``-0.0`` to ``0.0`` in a JSON-shaped payload.

    Some geometry builders (notably ``aperiodic_taylor_socolar``) compute
    centers / vertices via libm trig that produces ``-0.0`` on one
    platform and ``0.0`` on another for the same input. Python treats
    ``-0.0 == 0.0`` as True, so dict-equality drift checks don't notice,
    but ``json.dumps`` serializes them differently (``"-0.0"`` vs
    ``"0.0"``) and the content hash would diverge across platforms.
    Normalizing the sign keeps the hash deterministic across libm
    implementations without changing the rendered output.
    """
    if isinstance(value, float):
        return 0.0 if value == 0.0 else value
    if isinstance(value, dict):
        return {key: _normalize_negative_zero(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_negative_zero(item) for item in value]
    return value


def topology_content_revision(topology_payload: dict[str, Any]) -> str:
    """Derive a stable revision string from a topology payload's content.

    Hashes every field in the topology payload **except** the
    ``topology_revision`` field itself, so the result is determined by
    the cells + spec and is invariant to whatever revision string was
    previously stamped onto the payload. Use this where the goal is
    drift detection on a serialized topology (e.g. checked-in fixture
    JSON), so a builder change that mutates cells without changing
    inputs is reflected in the revision.

    Distinct from ``topology_revision`` (input-spec hash):

    - ``topology_revision``: cheap, computed at runtime, suitable for
      cache keys; doesn't move when the cell stream changes for a
      fixed input spec.
    - ``topology_content_revision``: scans the full cell stream,
      suitable for on-disk drift detection; moves when any cell field
      changes.

    Negative zero is normalized so the digest stays deterministic
    across libm implementations whose ``sin(pi)`` etc. round to
    different signs.
    """
    content_for_hash = _normalize_negative_zero(
        {key: value for key, value in topology_payload.items() if key != "topology_revision"}
    )
    canonical_json = json.dumps(content_for_hash, sort_keys=True, separators=(",", ":"))
    return sha1(canonical_json.encode("utf-8")).hexdigest()[:CONTENT_REVISION_HASH_LENGTH]


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
                PointPayload(x=vertex[0], y=vertex[1]) for vertex in self.vertices
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
                tuple(
                    -1 if neighbor_id is None else index_by_id[neighbor_id]
                    for neighbor_id in cell.neighbors
                )
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

    def clone(self) -> SimulationBoard:
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
