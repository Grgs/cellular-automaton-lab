import type {
    CellIdentifier,
    CompareRequest,
    RulesResponse,
    SeedComparisonResult,
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
        throw new Error(`Request failed: ${response.status}`);
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
): Promise<SimulationSnapshot> {
    return request<SimulationSnapshot>(sessionPath("/api/cells/toggle", sessionId), {
        method: "POST",
        body: JSON.stringify(normalizeCellPayload(cell)),
    });
}

export function setCellRequest(
    cell: CellIdentifier,
    state: number,
    sessionId?: string,
): Promise<SimulationSnapshot> {
    const payload = normalizeCellPayload(cell);
    return request<SimulationSnapshot>(sessionPath("/api/cells/set", sessionId), {
        method: "POST",
        body: JSON.stringify({ ...payload, state }),
    });
}

export function setCellsRequest(
    cells: CellMutation[],
    sessionId?: string,
): Promise<SimulationSnapshot> {
    return request<SimulationSnapshot>(sessionPath("/api/cells/set-many", sessionId), {
        method: "POST",
        body: JSON.stringify({ cells }),
    });
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
): Promise<SeedComparisonResult> {
    const response = await request<{ comparison: SeedComparisonResult }>(
        sessionPath("/api/compare", sessionId),
        {
            method: "POST",
            body: JSON.stringify(body),
        },
    );
    return response.comparison;
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
    const postControlForSession = ((
        path: EmptyControlCommandPath | "/api/control/reset" | "/api/config",
        body?: ConfigSyncBody | ResetControlBody,
    ) => postControl(path, body, sessionId)) as SimulationBackend["postControl"];

    return {
        getState: () => fetchState(sessionId),
        getRules: () => fetchRules(sessionId),
        dispose() {},
        postControl: postControlForSession,
        toggleCell: (cell) => toggleCellRequest(cell, sessionId),
        setCell: (cell, state) => setCellRequest(cell, state, sessionId),
        setCells: (cells) => setCellsRequest(cells, sessionId),
        compareSeed: (body) => compareSeedRequest(body, sessionId),
        previewTopology: (body) => previewTopologyRequest(body, sessionId),
    };
}
