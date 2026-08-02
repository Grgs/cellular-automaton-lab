from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from typing import Any, Literal

from backend.application_commands import (
    COMMAND_BY_PATH,
    ApplicationCommandDispatcher,
    CommandResult,
    CommandResultKind,
    ServiceCommandTarget,
)
from backend.contract_validation import validate_persisted_snapshot_payload
from backend.payload_types import PersistedSimulationSnapshotInput
from backend.public_errors import PublicApiError
from backend.rules import RuleRegistry
from backend.simulation.persistence import SimulationStateStore
from backend.simulation.service import SimulationService
from backend.simulation.state_restore import SimulationStateRestorer


class NoopLock:
    def __enter__(self) -> NoopLock:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> Literal[False]:
        return False


def _response_payload(
    snapshot: object, persisted_snapshot: object | None = None, *, rules: object | None = None
) -> str:
    payload: dict[str, object] = {"ok": True}
    if snapshot is not None:
        payload["snapshot"] = snapshot
    if rules is not None:
        payload["rules"] = rules
    if persisted_snapshot is not None:
        payload["persisted_snapshot"] = persisted_snapshot
    return json.dumps(payload)


def _error_payload(error: str | PublicApiError) -> str:
    payload = error.to_payload() if isinstance(error, PublicApiError) else {"error": error}
    return json.dumps({"ok": False, **payload})


@dataclass
class BrowserSimulationRuntime:
    rule_registry: RuleRegistry
    service: SimulationService
    state_restorer: SimulationStateRestorer

    @classmethod
    def create(cls) -> BrowserSimulationRuntime:
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
        result = self.command_dispatcher.dispatch(COMMAND_BY_PATH["/api/state"])
        return self._command_response(result)

    def get_rules_response(self) -> str:
        result = self.command_dispatcher.dispatch(COMMAND_BY_PATH["/api/rules"])
        return self._command_response(result)

    @property
    def command_dispatcher(self) -> ApplicationCommandDispatcher:
        return ApplicationCommandDispatcher(ServiceCommandTarget(self.service, self.rule_registry))

    def _command_response(self, result: CommandResult) -> str:
        if result.kind is CommandResultKind.SNAPSHOT:
            snapshot = self.service.get_state()
            return _response_payload(
                result.payload,
                SimulationStateStore.serialize_snapshot(snapshot),
            )
        if result.kind is CommandResultKind.RULES:
            return _response_payload(None, rules=result.payload["rules"])
        return json.dumps({"ok": True, **result.payload})

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
            command = COMMAND_BY_PATH.get(path)
            if command is None:
                raise PublicApiError(f"Unknown command '{path}'.")
            result = self.command_dispatcher.dispatch(command, request_payload)
            return self._command_response(result)
        except PublicApiError as exc:
            return _error_payload(exc)


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
