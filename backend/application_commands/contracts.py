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
    http_method: Literal["GET", "POST"]
    request: str
    result: CommandResultKind
    mutates_state: bool
    payload_requirement: Literal["none", "optional", "required"]
    frontend_request: str
    frontend_result: str


# The generator for frontend/application-command-contract.ts resolves every
# capitalized type named by a command through this inventory. Keeping the type
# expression and its import source next to the executable registry makes a new
# command one coordinated change instead of another hand-maintained mirror.
TYPESCRIPT_TYPE_MODULES = MappingProxyType(
    {
        "CellMutationDelta": "./types/domain.js",
        "CellTargetRequest": "./types/controller-api.js",
        "CellUpdateRequest": "./types/controller-api.js",
        "CellUpdatesRequest": "./types/controller-api.js",
        "CompareRequest": "./types/domain.js",
        "ConfigSyncBody": "./types/controller-api.js",
        "FilmstripRequest": "./types/domain.js",
        "ResetControlBody": "./types/controller-api.js",
        "RuleDefinition": "./types/domain.js",
        "SeedComparisonResult": "./types/domain.js",
        "SeedFilmstripResult": "./types/domain.js",
        "SimulationSnapshot": "./types/domain.js",
        "TopologyPreview": "./types/domain.js",
        "TopologyPreviewRequest": "./types/domain.js",
    }
)


# This is the executable command inventory. Host-only operations deliberately
# do not appear here: Flask bootstrap/meta/session selection/background loops,
# and standalone initialization/restore/ticking/persistence emission.
COMMAND_SPECS: tuple[CommandSpec, ...] = (
    CommandSpec(
        ApplicationCommand.STATE_GET,
        "/api/state",
        "GET",
        "EmptyCommandRequestPayload",
        CommandResultKind.SNAPSHOT,
        False,
        "none",
        "undefined",
        "SimulationSnapshot",
    ),
    CommandSpec(
        ApplicationCommand.RULES_LIST,
        "/api/rules",
        "GET",
        "EmptyCommandRequestPayload",
        CommandResultKind.RULES,
        False,
        "none",
        "undefined",
        "{ rules: RuleDefinition[] }",
    ),
    CommandSpec(
        ApplicationCommand.COMPARE_RUN,
        "/api/compare",
        "POST",
        "CompareRequestPayload",
        CommandResultKind.COMPARISON,
        False,
        "required",
        "CompareRequest",
        "{ comparison: SeedComparisonResult }",
    ),
    CommandSpec(
        ApplicationCommand.FILMSTRIP_RUN,
        "/api/compare/filmstrip",
        "POST",
        "FilmstripRequestPayload",
        CommandResultKind.FILMSTRIP,
        False,
        "required",
        "FilmstripRequest",
        "{ filmstrip: SeedFilmstripResult }",
    ),
    CommandSpec(
        ApplicationCommand.TOPOLOGY_PREVIEW,
        "/api/topology/preview",
        "POST",
        "TopologyPreviewRequestPayload",
        CommandResultKind.TOPOLOGY_PREVIEW,
        False,
        "required",
        "TopologyPreviewRequest",
        "{ topology_preview: TopologyPreview }",
    ),
    CommandSpec(
        ApplicationCommand.SIMULATION_START,
        "/api/control/start",
        "POST",
        "EmptyCommandRequestPayload",
        CommandResultKind.SNAPSHOT,
        True,
        "none",
        "undefined",
        "SimulationSnapshot",
    ),
    CommandSpec(
        ApplicationCommand.SIMULATION_PAUSE,
        "/api/control/pause",
        "POST",
        "EmptyCommandRequestPayload",
        CommandResultKind.SNAPSHOT,
        True,
        "none",
        "undefined",
        "SimulationSnapshot",
    ),
    CommandSpec(
        ApplicationCommand.SIMULATION_RESUME,
        "/api/control/resume",
        "POST",
        "EmptyCommandRequestPayload",
        CommandResultKind.SNAPSHOT,
        True,
        "none",
        "undefined",
        "SimulationSnapshot",
    ),
    CommandSpec(
        ApplicationCommand.SIMULATION_STEP,
        "/api/control/step",
        "POST",
        "EmptyCommandRequestPayload",
        CommandResultKind.SNAPSHOT,
        True,
        "none",
        "undefined",
        "SimulationSnapshot",
    ),
    CommandSpec(
        ApplicationCommand.SIMULATION_RESET,
        "/api/control/reset",
        "POST",
        "ResetControlRequestPayload",
        CommandResultKind.SNAPSHOT,
        True,
        "optional",
        "ResetControlBody | undefined",
        "SimulationSnapshot",
    ),
    CommandSpec(
        ApplicationCommand.SIMULATION_CONFIGURE,
        "/api/config",
        "POST",
        "ConfigSyncRequestPayload",
        CommandResultKind.SNAPSHOT,
        True,
        "optional",
        "ConfigSyncBody | undefined",
        "SimulationSnapshot",
    ),
    CommandSpec(
        ApplicationCommand.CELL_TOGGLE,
        "/api/cells/toggle",
        "POST",
        "CellTargetPayload",
        CommandResultKind.CELL_DELTA,
        True,
        "required",
        "CellTargetRequest",
        "CellMutationDelta",
    ),
    CommandSpec(
        ApplicationCommand.CELL_SET,
        "/api/cells/set",
        "POST",
        "CellUpdatePayload",
        CommandResultKind.CELL_DELTA,
        True,
        "required",
        "CellUpdateRequest",
        "CellMutationDelta",
    ),
    CommandSpec(
        ApplicationCommand.CELLS_SET_MANY,
        "/api/cells/set-many",
        "POST",
        "CellUpdatesRequestPayload",
        CommandResultKind.CELL_DELTA,
        True,
        "required",
        "CellUpdatesRequest",
        "CellMutationDelta",
    ),
)

COMMAND_BY_PATH = MappingProxyType({spec.transport_path: spec.command for spec in COMMAND_SPECS})
