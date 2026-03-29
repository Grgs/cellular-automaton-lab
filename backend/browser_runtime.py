from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from backend.payload_types import RawJsonObject
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
    ) -> bool:
        return False


def _require_object(value: object, message: str) -> RawJsonObject:
    if not isinstance(value, dict):
        raise ValueError(message)
    return value


def _coerce_int(value: object, message: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (str, bytes, bytearray, int, float)):
        raise ValueError(message)
    return int(value)


def _coerce_float(value: object, message: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (str, bytes, bytearray, int, float)):
        raise ValueError(message)
    return float(value)


def _optional_int(payload: Mapping[str, object], key: str) -> int | None:
    value = payload.get(key)
    if value in (None, ""):
        return None
    return _coerce_int(value, f"'{key}' must be an integer.")


def _optional_float(payload: Mapping[str, object], key: str) -> float | None:
    value = payload.get(key)
    if value in (None, ""):
        return None
    return _coerce_float(value, f"'{key}' must be a number.")


def _optional_rule_name(payload: Mapping[str, object], rule_registry: RuleRegistry) -> str | None:
    value = payload.get("rule")
    if value in (None, ""):
        return None
    if not isinstance(value, str) or not rule_registry.has(value):
        raise ValueError("'rule' must reference a known rule module.")
    return value


def _cell_id(payload: Mapping[str, object], key: str = "id") -> str:
    value = payload.get(key)
    if value in (None, ""):
        raise ValueError(f"Missing required field '{key}'.")
    if not isinstance(value, str):
        raise ValueError(f"'{key}' must be a string.")
    return value


def _state_value(
    payload: Mapping[str, object],
    allowed_states: set[int],
    *,
    rule_name: str,
    key: str = "state",
) -> int:
    if key not in payload:
        raise ValueError(f"Missing required field '{key}'.")
    state = _coerce_int(payload[key], f"'{key}' must be a valid state value.")
    if state not in allowed_states:
        raise ValueError(f"'{key}' must be one of the states supported by rule '{rule_name}'.")
    return state


def _normalize_reset_topology_spec(payload: Mapping[str, object]) -> RawJsonObject | None:
    if payload.get("geometry") not in (None, ""):
        raise ValueError("'geometry' must be provided through 'topology_spec'.")
    if payload.get("width") not in (None, "") or payload.get("height") not in (None, ""):
        raise ValueError("'width' and 'height' must be provided through 'topology_spec'.")
    if payload.get("patch_depth") not in (None, ""):
        raise ValueError("'patch_depth' must be provided through 'topology_spec'.")
    topology_spec = payload.get("topology_spec")
    if topology_spec in (None, ""):
        return None
    mapping = _require_object(topology_spec, "'topology_spec' must be an object.")
    normalized: RawJsonObject = {}
    for key in ("tiling_family", "adjacency_mode", "sizing_mode"):
        value = mapping.get(key)
        if value not in (None, ""):
            normalized[key] = str(value)
    for key in ("width", "height", "patch_depth"):
        value = _optional_int(mapping, key)
        if value is not None:
            normalized[key] = value
    return normalized


def _normalize_config_topology_patch(payload: Mapping[str, object]) -> RawJsonObject | None:
    if payload.get("geometry") not in (None, ""):
        raise ValueError("'geometry' can only be changed through reset.")
    if payload.get("width") not in (None, "") or payload.get("height") not in (None, ""):
        raise ValueError("'width' and 'height' must be provided through 'topology_spec'.")
    if payload.get("patch_depth") not in (None, ""):
        raise ValueError("'patch_depth' can only be changed through reset.")
    topology_spec = payload.get("topology_spec")
    if topology_spec is None:
        return None
    mapping = _require_object(topology_spec, "'topology_spec' must be an object.")
    disallowed_keys = {"tiling_family", "adjacency_mode", "sizing_mode", "patch_depth"} & set(mapping.keys())
    if disallowed_keys:
        disallowed = ", ".join(sorted(disallowed_keys))
        raise ValueError(f"'{disallowed}' can only be changed through reset.")
    normalized: RawJsonObject = {}
    width = _optional_int(mapping, "width")
    height = _optional_int(mapping, "height")
    if width is not None:
        normalized["width"] = width
    if height is not None:
        normalized["height"] = height
    return normalized


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
            service=SimulationService(rule_registry=rule_registry, lock=NoopLock()),
            state_restorer=SimulationStateRestorer(rule_registry),
        )

    def restore_state(self, payload: object) -> None:
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
                    topology_spec=_normalize_reset_topology_spec(request_payload),
                    rule_name=_optional_rule_name(request_payload, self.rule_registry),
                    speed=_optional_float(request_payload, "speed"),
                    randomize=bool(request_payload.get("randomize", False)),
                )
            elif path == "/api/config":
                self.service.update_config(
                    topology_spec=_normalize_config_topology_patch(request_payload),
                    speed=_optional_float(request_payload, "speed"),
                    rule_name=_optional_rule_name(request_payload, self.rule_registry),
                )
            elif path == "/api/cells/toggle":
                self.service.toggle_cell_by_id(_cell_id(request_payload))
            elif path == "/api/cells/set":
                current_rule = self.service.state.rule
                state_value = _state_value(
                    request_payload,
                    current_rule.state_values(),
                    rule_name=current_rule.name,
                )
                self.service.set_cell_state_by_id(_cell_id(request_payload), state_value)
            elif path == "/api/cells/set-many":
                raw_cells = request_payload.get("cells")
                if not isinstance(raw_cells, list) or len(raw_cells) == 0:
                    raise ValueError("'cells' must be a non-empty list.")
                current_rule = self.service.state.rule
                allowed_states = current_rule.state_values()
                cells: list[tuple[str, int]] = []
                for index, cell in enumerate(raw_cells):
                    cell_payload = _require_object(cell, f"'cells[{index}]' must be an object.")
                    cell_id = _cell_id(cell_payload)
                    state_value = _state_value(cell_payload, allowed_states, rule_name=current_rule.name)
                    cells.append((cell_id, state_value))
                self.service.set_cells_by_id(cells)
            else:
                raise ValueError(f"Unknown command '{path}'.")
        except (SimulationOperationError, ValueError) as exc:
            return _error_payload(str(exc))

        snapshot = self.service.get_state()
        return _response_payload(snapshot.to_dict(), SimulationStateStore.serialize_snapshot(snapshot))


_RUNTIME: BrowserSimulationRuntime | None = None


def initialize_runtime(persisted_snapshot_json: str | None = None) -> str:
    global _RUNTIME
    _RUNTIME = BrowserSimulationRuntime.create()
    if persisted_snapshot_json:
        try:
            _RUNTIME.restore_state(json.loads(persisted_snapshot_json))
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
