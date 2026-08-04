import type {
    CellMutationDelta,
    PersistedSimulationSnapshotV5,
    RulesResponse,
    SeedComparisonResult,
    SeedFilmstripResult,
    SimulationSnapshot,
    TopologyPreview,
} from "../types/domain.js";
import type {
    ApplicationCommandPath,
    StandaloneRequestPayload,
} from "../application-command-contract.js";
export type { StandaloneRequestPayload } from "../application-command-contract.js";

export type StandaloneCommandPath = ApplicationCommandPath;

export interface StandaloneInitMessage {
    type: "init";
    requestId: string;
    persistedSnapshot: PersistedSimulationSnapshotV5 | null;
    pythonBundleUrl: string;
}

export interface StandaloneRequestMessage {
    type: "request";
    requestId: string;
    path: StandaloneCommandPath;
    payload?: StandaloneRequestPayload;
}

export interface StandaloneTickPersistEvent {
    type: "persist";
    persistedSnapshot: PersistedSimulationSnapshotV5;
}

export interface StandaloneReadyResponse {
    type: "ready";
    requestId: string;
    snapshot: SimulationSnapshot;
    persistedSnapshot: PersistedSimulationSnapshotV5 | null;
}

export interface StandaloneSuccessResponse {
    type: "response";
    requestId: string;
    ok: true;
    snapshot?: SimulationSnapshot;
    rules?: RulesResponse["rules"];
    comparison?: SeedComparisonResult;
    filmstrip?: SeedFilmstripResult;
    topologyPreview?: TopologyPreview;
    cellDelta?: CellMutationDelta;
    persistedSnapshot?: PersistedSimulationSnapshotV5;
}

export interface StandaloneErrorResponse {
    type: "response";
    requestId: string;
    ok: false;
    error: string;
    code?: string;
    limit?: number;
    estimated_cells?: number;
    actual_cells?: number;
}

export interface StandaloneInitErrorResponse {
    type: "ready";
    requestId: string;
    error: string;
}

export type StandaloneWorkerIncomingMessage = StandaloneInitMessage | StandaloneRequestMessage;
export type StandaloneWorkerOutgoingMessage =
    | StandaloneTickPersistEvent
    | StandaloneReadyResponse
    | StandaloneSuccessResponse
    | StandaloneErrorResponse
    | StandaloneInitErrorResponse;
