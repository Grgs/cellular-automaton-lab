from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from typing import Any, Literal

from backend.contract_validation import (
    ContractValidationError,
    normalize_config_topology_patch,
    normalize_reset_topology_spec,
    parse_cell_id,
    parse_cell_updates,
    parse_optional_float,
    parse_rule_name,
    parse_state_value,
    validate_persisted_snapshot_payload,
)
from backend.payload_types import PersistedSimulationSnapshotInput
from backend.rules import RuleRegistry
from backend.simulation.persistence import SimulationStateStore
from backend.simulation.service import SimulationOperationError, SimulationService
from backend.simulation.state_restore import SimulationStateRestorer


class NoopLock:
    def __enter__(self) -> "NoopLock":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> Literal[False]:
        return False


def _response_payload(snapshot: object, persisted_snapshot: object | None = None, *, rules: object | None = None) -> str:
    payload: dict[str, object] = {"ok": True}
    if snapshot is not None:
        payload["snapshot"] = snapshot
    if rules is not None:
        payload["rules"] = rules
    if persisted_snapshot is not None:
        payload["persisted_snapshot"] = persisted_snapshot
    return json.dumps(payload)


def _error_payload(message: str) -> str:
    return json.dumps({"ok": False, "error": message})


@dataclass
class BrowserSimulationRuntime:
    rule_registry: RuleRegistry
    service: SimulationService
    state_restorer: SimulationStateRestorer

    @classmethod
    def create(cls) -> "BrowserSimulationRuntime":
        rule_registry = RuleRegistry()
        return cls(
            rule_registry=rule_registry,
            service=SimulationService(rule_registry=rule_registry, lock=threading.Lock()),
            state_restorer=SimulationStateRestorer(rule_registry),
        )

    def restore_state(self, payload: PersistedSimulationSnapshotInput) -> None:
        next_state = self.state_restorer.restore(payload, fallback_state=self.service.state)
        self.service.replace_state(next_state)

    def get_state_response(self) -> str:
        snapshot = self.service.get_state()
        return _response_payload(snapshot.to_dict(), SimulationStateStore.serialize_snapshot(snapshot))

    def get_rules_response(self) -> str:
        return _response_payload(None, rules=self.rule_registry.describe_rules())

    def tick_running(self) -> str:
        if not self.service.step_if_running():
            return json.dumps({"ok": True, "stepped": False})
        snapshot = self.service.get_state()
        return json.dumps(
            {
                "ok": True,
                "stepped": True,
                "snapshot": snapshot.to_dict(),
                "persisted_snapshot": SimulationStateStore.serialize_snapshot(snapshot),
            }
        )

    def handle_command(self, path: str, payload: object | None = None) -> str:
        request_payload = payload if isinstance(payload, dict) else {}
        try:
            if path == "/api/state":
                return self.get_state_response()
            if path == "/api/rules":
                return self.get_rules_response()
            if path == "/api/control/start":
                self.service.start()
            elif path == "/api/control/pause":
                self.service.pause()
            elif path == "/api/control/resume":
                self.service.resume()
            elif path == "/api/control/step":
                self.service.step()
            elif path == "/api/control/reset":
                self.service.reset(
                    topology_spec=normalize_reset_topology_spec(request_payload),
                    rule_name=parse_rule_name(request_payload, self.rule_registry),
                    speed=parse_optional_float(request_payload, "speed"),
                    randomize=bool(request_payload.get("randomize", False)),
                )
            elif path == "/api/config":
                self.service.update_config(
                    topology_spec=normalize_config_topology_patch(request_payload),
                    speed=parse_optional_float(request_payload, "speed"),
                    rule_name=parse_rule_name(request_payload, self.rule_registry),
                )
            elif path == "/api/cells/toggle":
                self.service.toggle_cell_by_id(parse_cell_id(request_payload))
            elif path == "/api/cells/set":
                current_rule = self.service.state.rule
                self.service.set_cell_state_by_id(
                    parse_cell_id(request_payload),
                    parse_state_value(request_payload, current_rule),
                )
            elif path == "/api/cells/set-many":
                cells = parse_cell_updates(request_payload, self.service.state.rule)
                self.service.set_cells_by_id([(cell["id"], cell["state"]) for cell in cells])
            else:
                raise ValueError(f"Unknown command '{path}'.")
        except (ContractValidationError, SimulationOperationError, ValueError) as exc:
            return _error_payload(str(exc))

        snapshot = self.service.get_state()
        return _response_payload(snapshot.to_dict(), SimulationStateStore.serialize_snapshot(snapshot))


_RUNTIME: BrowserSimulationRuntime | None = None


def initialize_runtime(persisted_snapshot_json: str | None = None) -> str:
    global _RUNTIME
    _RUNTIME = BrowserSimulationRuntime.create()
    if persisted_snapshot_json:
        try:
            _RUNTIME.restore_state(
                validate_persisted_snapshot_payload(json.loads(persisted_snapshot_json))
            )
        except Exception:
            pass
    return _RUNTIME.get_state_response()


def handle_request(path: str, payload_json: str | None = None) -> str:
    if _RUNTIME is None:
        return _error_payload("Standalone runtime has not been initialized.")
    payload: Any = None
    if payload_json:
        payload = json.loads(payload_json)
    return _RUNTIME.handle_command(path, payload)


def tick_running() -> str:
    if _RUNTIME is None:
        return _error_payload("Standalone runtime has not been initialized.")
    return _RUNTIME.tick_running()
