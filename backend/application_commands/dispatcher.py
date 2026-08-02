from __future__ import annotations

from collections.abc import Callable

from backend.application_commands.contracts import (
    ApplicationCommand,
    CommandResult,
    CommandResultKind,
)
from backend.application_commands.targets import ApplicationCommandTarget
from backend.contract_validation import (
    normalize_config_topology_patch,
    normalize_reset_topology_spec,
    parse_cell_id,
    parse_cell_updates,
    parse_optional_float,
    parse_rule_name,
    parse_state_value,
)
from backend.payload_types import RawJsonObject
from backend.simulation.seeding import run_compare_request, run_filmstrip_request
from backend.simulation.topology_preview import build_topology_preview


class ApplicationCommandDispatcher:
    """Decode and execute domain commands independently of their transport."""

    def __init__(self, target: ApplicationCommandTarget) -> None:
        self.target = target
        self._handlers: dict[ApplicationCommand, Callable[[RawJsonObject], CommandResult]] = {
            ApplicationCommand.STATE_GET: self._get_state,
            ApplicationCommand.RULES_LIST: self._list_rules,
            ApplicationCommand.COMPARE_RUN: self._run_compare,
            ApplicationCommand.FILMSTRIP_RUN: self._run_filmstrip,
            ApplicationCommand.TOPOLOGY_PREVIEW: self._preview_topology,
            ApplicationCommand.SIMULATION_START: self._start,
            ApplicationCommand.SIMULATION_PAUSE: self._pause,
            ApplicationCommand.SIMULATION_RESUME: self._resume,
            ApplicationCommand.SIMULATION_STEP: self._step,
            ApplicationCommand.SIMULATION_RESET: self._reset,
            ApplicationCommand.SIMULATION_CONFIGURE: self._configure,
            ApplicationCommand.CELL_TOGGLE: self._toggle_cell,
            ApplicationCommand.CELL_SET: self._set_cell,
            ApplicationCommand.CELLS_SET_MANY: self._set_cells,
        }

    def dispatch(
        self,
        command: ApplicationCommand,
        payload: RawJsonObject | None = None,
    ) -> CommandResult:
        return self._handlers[command](payload or {})

    def _snapshot_result(self) -> CommandResult:
        return CommandResult(CommandResultKind.SNAPSHOT, self.target.get_state().to_dict())

    def _get_state(self, _payload: RawJsonObject) -> CommandResult:
        return self._snapshot_result()

    def _list_rules(self, _payload: RawJsonObject) -> CommandResult:
        return CommandResult(
            CommandResultKind.RULES,
            {"rules": self.target.rules.describe_rules()},
        )

    def _run_compare(self, payload: RawJsonObject) -> CommandResult:
        return CommandResult(
            CommandResultKind.COMPARISON,
            {"comparison": run_compare_request(payload)},
        )

    def _run_filmstrip(self, payload: RawJsonObject) -> CommandResult:
        return CommandResult(
            CommandResultKind.FILMSTRIP,
            {"filmstrip": run_filmstrip_request(payload)},
        )

    def _preview_topology(self, payload: RawJsonObject) -> CommandResult:
        return CommandResult(
            CommandResultKind.TOPOLOGY_PREVIEW,
            {"topology_preview": build_topology_preview(payload)},
        )

    def _start(self, _payload: RawJsonObject) -> CommandResult:
        self.target.start()
        return self._snapshot_result()

    def _pause(self, _payload: RawJsonObject) -> CommandResult:
        self.target.pause()
        return self._snapshot_result()

    def _resume(self, _payload: RawJsonObject) -> CommandResult:
        self.target.resume()
        return self._snapshot_result()

    def _step(self, _payload: RawJsonObject) -> CommandResult:
        self.target.step()
        return self._snapshot_result()

    def _reset(self, payload: RawJsonObject) -> CommandResult:
        self.target.reset(
            topology_spec=normalize_reset_topology_spec(payload),
            rule_name=parse_rule_name(payload, self.target.rules),
            speed=parse_optional_float(payload, "speed"),
            randomize=bool(payload.get("randomize", False)),
        )
        return self._snapshot_result()

    def _configure(self, payload: RawJsonObject) -> CommandResult:
        self.target.update_config(
            topology_spec=normalize_config_topology_patch(payload),
            speed=parse_optional_float(payload, "speed"),
            rule_name=parse_rule_name(payload, self.target.rules),
        )
        return self._snapshot_result()

    def _toggle_cell(self, payload: RawJsonObject) -> CommandResult:
        delta = self.target.toggle_cell_by_id(parse_cell_id(payload))
        return CommandResult(CommandResultKind.CELL_DELTA, delta.to_dict())

    def _set_cell(self, payload: RawJsonObject) -> CommandResult:
        delta = self.target.set_cell_state_by_id(
            parse_cell_id(payload),
            parse_state_value(payload, self.target.get_rule()),
        )
        return CommandResult(CommandResultKind.CELL_DELTA, delta.to_dict())

    def _set_cells(self, payload: RawJsonObject) -> CommandResult:
        cells = parse_cell_updates(payload, self.target.get_rule())
        delta = self.target.set_cells_by_id([(cell["id"], cell["state"]) for cell in cells])
        return CommandResult(CommandResultKind.CELL_DELTA, delta.to_dict())
