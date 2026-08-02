from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Literal


class ApplicationCommand(StrEnum):
    STATE_GET = "state.get"
    RULES_LIST = "rules.list"
    COMPARE_RUN = "compare.run"
    FILMSTRIP_RUN = "filmstrip.run"
    TOPOLOGY_PREVIEW = "topology.preview"
    SIMULATION_START = "simulation.start"
    SIMULATION_PAUSE = "simulation.pause"
    SIMULATION_RESUME = "simulation.resume"
    SIMULATION_STEP = "simulation.step"
    SIMULATION_RESET = "simulation.reset"
    SIMULATION_CONFIGURE = "simulation.configure"
    CELL_TOGGLE = "cell.toggle"
    CELL_SET = "cell.set"
    CELLS_SET_MANY = "cells.set_many"


class CommandResultKind(StrEnum):
    SNAPSHOT = "snapshot"
    RULES = "rules"
    COMPARISON = "comparison"
    FILMSTRIP = "filmstrip"
    TOPOLOGY_PREVIEW = "topology_preview"
    CELL_DELTA = "cell_delta"


@dataclass(frozen=True)
class CommandResult:
    kind: CommandResultKind
    payload: Mapping[str, object]


@dataclass(frozen=True)
class CommandSpec:
    command: ApplicationCommand
    transport_path: str
    request: str
    result: CommandResultKind
    mutates_state: bool
    payload_requirement: Literal["none", "optional", "required"]


# This is the executable command inventory. Host-only operations deliberately
# do not appear here: Flask bootstrap/meta/session selection/background loops,
# and standalone initialization/restore/ticking/persistence emission.
COMMAND_SPECS: tuple[CommandSpec, ...] = (
    CommandSpec(
        ApplicationCommand.STATE_GET,
        "/api/state",
        "EmptyCommandRequestPayload",
        CommandResultKind.SNAPSHOT,
        False,
        "none",
    ),
    CommandSpec(
        ApplicationCommand.RULES_LIST,
        "/api/rules",
        "EmptyCommandRequestPayload",
        CommandResultKind.RULES,
        False,
        "none",
    ),
    CommandSpec(
        ApplicationCommand.COMPARE_RUN,
        "/api/compare",
        "CompareRequestPayload",
        CommandResultKind.COMPARISON,
        False,
        "required",
    ),
    CommandSpec(
        ApplicationCommand.FILMSTRIP_RUN,
        "/api/compare/filmstrip",
        "FilmstripRequestPayload",
        CommandResultKind.FILMSTRIP,
        False,
        "required",
    ),
    CommandSpec(
        ApplicationCommand.TOPOLOGY_PREVIEW,
        "/api/topology/preview",
        "TopologyPreviewRequestPayload",
        CommandResultKind.TOPOLOGY_PREVIEW,
        False,
        "required",
    ),
    CommandSpec(
        ApplicationCommand.SIMULATION_START,
        "/api/control/start",
        "EmptyCommandRequestPayload",
        CommandResultKind.SNAPSHOT,
        True,
        "none",
    ),
    CommandSpec(
        ApplicationCommand.SIMULATION_PAUSE,
        "/api/control/pause",
        "EmptyCommandRequestPayload",
        CommandResultKind.SNAPSHOT,
        True,
        "none",
    ),
    CommandSpec(
        ApplicationCommand.SIMULATION_RESUME,
        "/api/control/resume",
        "EmptyCommandRequestPayload",
        CommandResultKind.SNAPSHOT,
        True,
        "none",
    ),
    CommandSpec(
        ApplicationCommand.SIMULATION_STEP,
        "/api/control/step",
        "EmptyCommandRequestPayload",
        CommandResultKind.SNAPSHOT,
        True,
        "none",
    ),
    CommandSpec(
        ApplicationCommand.SIMULATION_RESET,
        "/api/control/reset",
        "ResetControlRequestPayload",
        CommandResultKind.SNAPSHOT,
        True,
        "optional",
    ),
    CommandSpec(
        ApplicationCommand.SIMULATION_CONFIGURE,
        "/api/config",
        "ConfigSyncRequestPayload",
        CommandResultKind.SNAPSHOT,
        True,
        "optional",
    ),
    CommandSpec(
        ApplicationCommand.CELL_TOGGLE,
        "/api/cells/toggle",
        "CellTargetPayload",
        CommandResultKind.CELL_DELTA,
        True,
        "required",
    ),
    CommandSpec(
        ApplicationCommand.CELL_SET,
        "/api/cells/set",
        "CellUpdatePayload",
        CommandResultKind.CELL_DELTA,
        True,
        "required",
    ),
    CommandSpec(
        ApplicationCommand.CELLS_SET_MANY,
        "/api/cells/set-many",
        "CellUpdatesRequestPayload",
        CommandResultKind.CELL_DELTA,
        True,
        "required",
    ),
)

COMMAND_BY_PATH = MappingProxyType({spec.transport_path: spec.command for spec in COMMAND_SPECS})
