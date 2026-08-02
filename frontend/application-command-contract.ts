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

interface CommandContract<TRequest, TResult> {
    request: TRequest;
    result: TResult;
}

/** Compile-time mirror of the transport-neutral Python application registry. */
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

export type ApplicationCommandId = keyof ApplicationCommandMap;
export type ApplicationCommandRequest<TCommand extends ApplicationCommandId> =
    ApplicationCommandMap[TCommand]["request"];
export type ApplicationCommandResult<TCommand extends ApplicationCommandId> =
    ApplicationCommandMap[TCommand]["result"];
