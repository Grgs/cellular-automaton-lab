import type {
    CellMutationDelta,
    CompareRequest,
    FilmstripRequest,
    RuleDefinition,
    SeedComparisonResult,
    SeedFilmstripResult,
    SimulationSnapshot,
    TopologyPreview,
    TopologyPreviewRequest,
} from "./types/domain.js";
import type {
    CellTargetRequest,
    CellUpdateRequest,
    CellUpdatesRequest,
    ConfigSyncBody,
    ResetControlBody,
} from "./types/controller-api.js";

/**
 * Generated from backend/application_commands/contracts.py.
 * Regenerate with `python -m tools repo command-contract --write`.
 */
interface CommandContract<TRequest, TResult> {
    request: TRequest;
    result: TResult;
}

export interface ApplicationCommandMap {
    "state.get": CommandContract<undefined, SimulationSnapshot>;
    "rules.list": CommandContract<undefined, { rules: RuleDefinition[] }>;
    "compare.run": CommandContract<CompareRequest, { comparison: SeedComparisonResult }>;
    "filmstrip.run": CommandContract<FilmstripRequest, { filmstrip: SeedFilmstripResult }>;
    "topology.preview": CommandContract<
        TopologyPreviewRequest,
        { topology_preview: TopologyPreview }
    >;
    "simulation.start": CommandContract<undefined, SimulationSnapshot>;
    "simulation.pause": CommandContract<undefined, SimulationSnapshot>;
    "simulation.resume": CommandContract<undefined, SimulationSnapshot>;
    "simulation.step": CommandContract<undefined, SimulationSnapshot>;
    "simulation.reset": CommandContract<ResetControlBody | undefined, SimulationSnapshot>;
    "simulation.configure": CommandContract<ConfigSyncBody | undefined, SimulationSnapshot>;
    "cell.toggle": CommandContract<CellTargetRequest, CellMutationDelta>;
    "cell.set": CommandContract<CellUpdateRequest, CellMutationDelta>;
    "cells.set_many": CommandContract<CellUpdatesRequest, CellMutationDelta>;
}

export interface ApplicationCommandPathMap {
    "/api/state": ApplicationCommandMap["state.get"];
    "/api/rules": ApplicationCommandMap["rules.list"];
    "/api/compare": ApplicationCommandMap["compare.run"];
    "/api/compare/filmstrip": ApplicationCommandMap["filmstrip.run"];
    "/api/topology/preview": ApplicationCommandMap["topology.preview"];
    "/api/control/start": ApplicationCommandMap["simulation.start"];
    "/api/control/pause": ApplicationCommandMap["simulation.pause"];
    "/api/control/resume": ApplicationCommandMap["simulation.resume"];
    "/api/control/step": ApplicationCommandMap["simulation.step"];
    "/api/control/reset": ApplicationCommandMap["simulation.reset"];
    "/api/config": ApplicationCommandMap["simulation.configure"];
    "/api/cells/toggle": ApplicationCommandMap["cell.toggle"];
    "/api/cells/set": ApplicationCommandMap["cell.set"];
    "/api/cells/set-many": ApplicationCommandMap["cells.set_many"];
}

export type StandaloneRequestPayload =
    | CompareRequest
    | FilmstripRequest
    | TopologyPreviewRequest
    | ResetControlBody
    | ConfigSyncBody
    | CellTargetRequest
    | CellUpdateRequest
    | CellUpdatesRequest;

export type ApplicationCommandId = keyof ApplicationCommandMap;
export type ApplicationCommandPath = keyof ApplicationCommandPathMap;
export type ApplicationCommandRequest<TCommand extends ApplicationCommandId> =
    ApplicationCommandMap[TCommand]["request"];
export type ApplicationCommandResult<TCommand extends ApplicationCommandId> =
    ApplicationCommandMap[TCommand]["result"];
