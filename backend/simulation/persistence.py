from __future__ import annotations

import json
from pathlib import Path

from backend.contract_validation import SNAPSHOT_VERSION, validate_persisted_snapshot_payload
from backend.payload_types import PersistedSimulationSnapshotV5
from backend.simulation.models import SimulationSnapshot

__all__ = ["SNAPSHOT_VERSION", "SimulationStateStore"]


class SimulationStateStore:
    """Persists simulation snapshots as versioned JSON on disk."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> PersistedSimulationSnapshotV5 | None:
        if not self.path.exists():
            return None

        with self.path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        return validate_persisted_snapshot_payload(payload)

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
            "version": SNAPSHOT_VERSION,
            "topology_spec": snapshot.config.topology_spec.to_dict(),
            "speed": snapshot.config.speed,
            "running": snapshot.running,
            "generation": snapshot.generation,
            "rule": snapshot.rule.name,
            "cells_by_id": snapshot.cells_by_id,
        }
        return payload
