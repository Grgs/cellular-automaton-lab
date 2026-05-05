import type {
    PersistedSimulationSnapshotV5,
    RulesResponse,
    SimulationSnapshot,
} from "../types/domain.js";
import type {
    CellTargetRequest,
    CellUpdateRequest,
    CellUpdatesRequest,
    ConfigSyncBody,
    EmptyControlCommandPath,
    ResetControlBody,
} from "../types/controller.js";

export type StandaloneCommandPath =
    | "/api/state"
    | "/api/rules"
    | "/api/cells/toggle"
    | "/api/cells/set"
    | "/api/cells/set-many"
    | EmptyControlCommandPath
    | "/api/control/reset"
    | "/api/config";

export interface StandaloneInitMessage {
    type: "init";
    requestId: string;
    persistedSnapshot: PersistedSimulationSnapshotV5 | null;
    pythonBundleUrl: string;
    pyodideBaseUrl: string;
}

export type StandaloneRequestPayload =
    | ResetControlBody
    | ConfigSyncBody
    | CellTargetRequest
    | CellUpdateRequest
    | CellUpdatesRequest;

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
    persistedSnapshot?: PersistedSimulationSnapshotV5;
}

export interface StandaloneErrorResponse {
    type: "response";
    requestId: string;
    ok: false;
    error: string;
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
