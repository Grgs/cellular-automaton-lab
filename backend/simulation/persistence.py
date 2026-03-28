from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.simulation.models import SimulationSnapshot


SNAPSHOT_VERSION = 5


class SimulationStateStore:
    """Persists simulation snapshots as versioned JSON on disk."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None

        with self.path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if not isinstance(payload, dict):
            raise ValueError("Persisted simulation state must be a JSON object.")
        version = payload.get("version")
        if version == SNAPSHOT_VERSION:
            return payload
        raise ValueError("Persisted simulation state version is unsupported.")

    def save(self, snapshot: SimulationSnapshot) -> None:
        payload = self.serialize_snapshot(snapshot)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        temp_path.replace(self.path)

    @staticmethod
    def serialize_snapshot(snapshot: SimulationSnapshot) -> dict[str, Any]:
        payload = {
            "version": SNAPSHOT_VERSION,
            "topology_spec": snapshot.config.topology_spec.to_dict(),
            "speed": snapshot.config.speed,
            "running": snapshot.running,
            "generation": snapshot.generation,
            "rule": snapshot.rule.name,
            "cells_by_id": snapshot.cells_by_id,
        }
        return payload
