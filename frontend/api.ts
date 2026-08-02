import type {
    CellMutationDelta,
    CellIdentifier,
    CompareRequest,
    FilmstripRequest,
    RulesResponse,
    SeedComparisonResult,
    SeedFilmstripResult,
    SimulationSnapshot,
    TopologyPreview,
    TopologyPreviewRequest,
} from "./types/domain.js";
import type {
    ConfigSyncBody,
    EmptyControlCommandPath,
    ResetControlBody,
    SimulationBackend,
} from "./types/controller.js";
import { SimulationSnapshotCache } from "./simulation-snapshot-cache.js";
import { decodeCellMutationDelta } from "./standalone/runtime-decoders.js";
import { BackendRequestError } from "./backend-request-error.js";

interface CellMutation extends CellIdentifier {
    state: number;
}

export interface HttpSimulationBackendOptions {
    sessionId?: string;
}

function sessionPath(path: string, sessionId: string | undefined): string {
    if (!sessionId) {
        return path;
    }
    return `/api/sessions/${encodeURIComponent(sessionId)}${path.slice("/api".length)}`;
}

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...options,
    });

    if (!response.ok) {
        // Surface the server's error detail (e.g. "preview limit is 10000") so
        // callers can classify failures instead of seeing only a status code.
        let detail = "";
        let code: string | undefined;
        let limit: number | undefined;
        let estimatedCells: number | undefined;
        let actualCells: number | undefined;
        try {
            const body: unknown = await response.json();
            if (body && typeof body === "object" && "error" in body) {
                const errorBody = body as Record<string, unknown>;
                detail = String(errorBody.error);
                code = typeof errorBody.code === "string" ? errorBody.code : undefined;
                limit = typeof errorBody.limit === "number" ? errorBody.limit : undefined;
                estimatedCells =
                    typeof errorBody.estimated_cells === "number"
                        ? errorBody.estimated_cells
                        : undefined;
                actualCells =
                    typeof errorBody.actual_cells === "number" ? errorBody.actual_cells : undefined;
            }
        } catch {
            // Non-JSON error body; the status code alone will have to do.
        }
        throw new BackendRequestError(detail, {
            status: response.status,
            ...(code === undefined ? {} : { code }),
            ...(limit === undefined ? {} : { limit }),
            ...(estimatedCells === undefined ? {} : { estimatedCells }),
            ...(actualCells === undefined ? {} : { actualCells }),
        });
    }

    return response.json();
}

export function fetchState(sessionId?: string): Promise<SimulationSnapshot> {
    return request<SimulationSnapshot>(sessionPath("/api/state", sessionId));
}

export function fetchRules(sessionId?: string): Promise<RulesResponse> {
    return request<RulesResponse>(sessionPath("/api/rules", sessionId));
}

function normalizeCellPayload(cell: CellIdentifier): CellIdentifier {
    if (
        typeof cell === "object" &&
        cell !== null &&
        typeof cell.id === "string" &&
        cell.id.length > 0
    ) {
        return { id: cell.id };
    }
    throw new Error("Cell mutations require a topology cell id.");
}

export function toggleCellRequest(
    cell: CellIdentifier,
    sessionId?: string,
): Promise<CellMutationDelta> {
    return request<unknown>(sessionPath("/api/cells/toggle", sessionId), {
        method: "POST",
        body: JSON.stringify(normalizeCellPayload(cell)),
    }).then((payload) => decodeCellMutationDelta(payload, "Cell toggle response"));
}

export function setCellRequest(
    cell: CellIdentifier,
    state: number,
    sessionId?: string,
): Promise<CellMutationDelta> {
    const payload = normalizeCellPayload(cell);
    return request<unknown>(sessionPath("/api/cells/set", sessionId), {
        method: "POST",
        body: JSON.stringify({ ...payload, state }),
    }).then((response) => decodeCellMutationDelta(response, "Cell set response"));
}

export function setCellsRequest(
    cells: CellMutation[],
    sessionId?: string,
): Promise<CellMutationDelta> {
    return request<unknown>(sessionPath("/api/cells/set-many", sessionId), {
        method: "POST",
        body: JSON.stringify({ cells }),
    }).then((payload) => decodeCellMutationDelta(payload, "Cell batch response"));
}

export function postControl(path: EmptyControlCommandPath): Promise<SimulationSnapshot>;
export function postControl(
    path: "/api/control/reset",
    body: ResetControlBody,
): Promise<SimulationSnapshot>;
export function postControl(path: "/api/config", body: ConfigSyncBody): Promise<SimulationSnapshot>;
export function postControl(
    path: EmptyControlCommandPath | "/api/control/reset" | "/api/config",
    body?: ConfigSyncBody | ResetControlBody,
    sessionId?: string,
): Promise<SimulationSnapshot>;
export function postControl(
    path: EmptyControlCommandPath | "/api/control/reset" | "/api/config",
    body?: ConfigSyncBody | ResetControlBody,
    sessionId?: string,
): Promise<SimulationSnapshot> {
    return request<SimulationSnapshot>(sessionPath(path, sessionId), {
        method: "POST",
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
}

export async function compareSeedRequest(
    body: CompareRequest,
    sessionId?: string,
    signal?: AbortSignal,
): Promise<SeedComparisonResult> {
    const response = await request<{ comparison: SeedComparisonResult }>(
        sessionPath("/api/compare", sessionId),
        {
            method: "POST",
            body: JSON.stringify(body),
            ...(signal === undefined ? {} : { signal }),
        },
    );
    return response.comparison;
}

export async function requestFilmstripRequest(
    body: FilmstripRequest,
    sessionId?: string,
    signal?: AbortSignal,
): Promise<SeedFilmstripResult> {
    const response = await request<{ filmstrip: SeedFilmstripResult }>(
        sessionPath("/api/compare/filmstrip", sessionId),
        {
            method: "POST",
            body: JSON.stringify(body),
            ...(signal === undefined ? {} : { signal }),
        },
    );
    return response.filmstrip;
}

export async function previewTopologyRequest(
    body: TopologyPreviewRequest,
    sessionId?: string,
): Promise<TopologyPreview> {
    const response = await request<{ topology_preview: TopologyPreview }>(
        sessionPath("/api/topology/preview", sessionId),
        {
            method: "POST",
            body: JSON.stringify(body),
        },
    );
    return response.topology_preview;
}

export function createHttpSimulationBackend({
    sessionId,
}: HttpSimulationBackendOptions = {}): SimulationBackend {
    const snapshots = new SimulationSnapshotCache();

    async function getStateForSession(): Promise<SimulationSnapshot> {
        const requestBase = snapshots.current();
        const nextSnapshot = await fetchState(sessionId);
        return snapshots.install(nextSnapshot, requestBase);
    }

    const postControlForSession = (async (
        path: EmptyControlCommandPath | "/api/control/reset" | "/api/config",
        body?: ConfigSyncBody | ResetControlBody,
    ) => {
        const requestBase = snapshots.current();
        const nextSnapshot = await postControl(path, body, sessionId);
        return snapshots.install(nextSnapshot, requestBase);
    }) as SimulationBackend["postControl"];

    async function reconcileCellMutation(
        mutation: Promise<CellMutationDelta>,
    ): Promise<SimulationSnapshot> {
        const delta = await mutation;
        return snapshots.reconcileDelta(delta, () => fetchState(sessionId));
    }

    return {
        getState: getStateForSession,
        getRules: () => fetchRules(sessionId),
        dispose() {},
        postControl: postControlForSession,
        toggleCell: (cell) => reconcileCellMutation(toggleCellRequest(cell, sessionId)),
        setCell: (cell, state) => reconcileCellMutation(setCellRequest(cell, state, sessionId)),
        setCells: (cells) => reconcileCellMutation(setCellsRequest(cells, sessionId)),
        compareSeed: (body, options) => compareSeedRequest(body, sessionId, options?.signal),
        requestFilmstrip: (body, options) =>
            requestFilmstripRequest(body, sessionId, options?.signal),
        previewTopology: (body) => previewTopologyRequest(body, sessionId),
    };
}
