from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from backend.payload_types import PersistedSimulationSnapshotV5, SparseCellsByIdPayload
from backend.simulation.models import SimulationSnapshot, TopologySpec


SNAPSHOT_VERSION = 5


class SimulationStateStore:
    """Persists simulation snapshots as versioned JSON on disk."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> PersistedSimulationSnapshotV5 | None:
        if not self.path.exists():
            return None

        with self.path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        return self._validate_payload(payload)

    def save(self, snapshot: SimulationSnapshot) -> None:
        payload = self.serialize_snapshot(snapshot)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        temp_path.replace(self.path)

    @staticmethod
    def serialize_snapshot(snapshot: SimulationSnapshot) -> PersistedSimulationSnapshotV5:
        payload: PersistedSimulationSnapshotV5 = {
            "version": 5,
            "topology_spec": snapshot.config.topology_spec.to_dict(),
            "speed": snapshot.config.speed,
            "running": snapshot.running,
            "generation": snapshot.generation,
            "rule": snapshot.rule.name,
            "cells_by_id": snapshot.cells_by_id,
        }
        return payload

    @staticmethod
    def _validate_payload(payload: object) -> PersistedSimulationSnapshotV5:
        if not isinstance(payload, dict):
            raise ValueError("Persisted simulation state must be a JSON object.")
        payload_mapping = payload

        version = payload_mapping.get("version")
        if version != SNAPSHOT_VERSION:
            raise ValueError("Persisted simulation state version is unsupported.")

        topology_spec_payload = payload_mapping.get("topology_spec")
        if not isinstance(topology_spec_payload, dict):
            raise ValueError("Persisted simulation state topology spec is invalid.")
        topology_spec_mapping = topology_spec_payload
        topology_spec = TopologySpec.from_values(
            tiling_family=str(topology_spec_mapping.get("tiling_family") or ""),
            adjacency_mode=str(topology_spec_mapping.get("adjacency_mode") or ""),
            width=SimulationStateStore._coerce_int(topology_spec_mapping, "width"),
            height=SimulationStateStore._coerce_int(topology_spec_mapping, "height"),
            patch_depth=SimulationStateStore._coerce_int(topology_spec_mapping, "patch_depth"),
        )

        running = payload_mapping.get("running")
        if not isinstance(running, bool):
            raise ValueError("Persisted simulation running state is invalid.")

        rule_name = payload_mapping.get("rule")
        if not isinstance(rule_name, str) or not rule_name:
            raise ValueError("Persisted simulation rule is invalid.")

        cells_by_id_payload = payload_mapping.get("cells_by_id")
        if not isinstance(cells_by_id_payload, dict):
            raise ValueError("Persisted simulation cells_by_id payload is invalid.")
        normalized_cells_by_id: SparseCellsByIdPayload = {}
        for cell_id, cell_state in cells_by_id_payload.items():
            if not isinstance(cell_id, str) or not cell_id:
                raise ValueError("Persisted simulation cells_by_id payload is invalid.")
            try:
                normalized_cells_by_id[cell_id] = int(cell_state)
            except (TypeError, ValueError) as exc:
                raise ValueError("Persisted simulation cells_by_id payload is invalid.") from exc

        try:
            speed = SimulationStateStore._coerce_float(payload_mapping, "speed")
            generation = SimulationStateStore._coerce_int(payload_mapping, "generation")
        except (TypeError, ValueError) as exc:
            raise ValueError("Persisted simulation state numeric fields are invalid.") from exc

        validated_payload: PersistedSimulationSnapshotV5 = {
            "version": 5,
            "topology_spec": topology_spec.to_dict(),
            "speed": speed,
            "running": running,
            "generation": generation,
            "rule": rule_name,
            "cells_by_id": normalized_cells_by_id,
        }
        return validated_payload

    @staticmethod
    def _coerce_int(mapping: Mapping[str, object], key: str) -> int:
        value = mapping.get(key)
        if isinstance(value, (str, bytes, bytearray, int, float)):
            return int(value)
        raise ValueError(f"Persisted simulation field '{key}' is invalid.")

    @staticmethod
    def _coerce_float(mapping: Mapping[str, object], key: str) -> float:
        value = mapping.get(key)
        if isinstance(value, (str, bytes, bytearray, int, float)):
            return float(value)
        raise ValueError(f"Persisted simulation field '{key}' is invalid.")
