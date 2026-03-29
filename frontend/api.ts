import type {
    CellIdentifier,
    RuleDefinition,
    RulesResponse,
    SimulationSnapshot,
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

export function fetchState(): Promise<SimulationSnapshot> {
    return request<SimulationSnapshot>("/api/state");
}

export function fetchRules(): Promise<RulesResponse> {
    return request<RulesResponse>("/api/rules");
}

function normalizeCellPayload(cell: CellIdentifier): CellIdentifier {
    if (typeof cell === "object" && cell !== null && typeof cell.id === "string" && cell.id.length > 0) {
        return { id: cell.id };
    }
    throw new Error("Cell mutations require a topology cell id.");
}

export function toggleCellRequest(cell: CellIdentifier): Promise<SimulationSnapshot> {
    return request<SimulationSnapshot>("/api/cells/toggle", {
        method: "POST",
        body: JSON.stringify(normalizeCellPayload(cell)),
    });
}

export function setCellRequest(cell: CellIdentifier, state: number): Promise<SimulationSnapshot> {
    const payload = normalizeCellPayload(cell);
    return request<SimulationSnapshot>("/api/cells/set", {
        method: "POST",
        body: JSON.stringify({ ...payload, state }),
    });
}

export function setCellsRequest(cells: CellMutation[]): Promise<SimulationSnapshot> {
    return request<SimulationSnapshot>("/api/cells/set-many", {
        method: "POST",
        body: JSON.stringify({ cells }),
    });
}

export function postControl(path: EmptyControlCommandPath): Promise<SimulationSnapshot>;
export function postControl(path: "/api/control/reset", body: ResetControlBody): Promise<SimulationSnapshot>;
export function postControl(path: "/api/config", body: ConfigSyncBody): Promise<SimulationSnapshot>;
export function postControl(
    path: EmptyControlCommandPath | "/api/control/reset" | "/api/config",
    body?: ConfigSyncBody | ResetControlBody,
): Promise<SimulationSnapshot> {
    return request<SimulationSnapshot>(path, {
        method: "POST",
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
}

export function createHttpSimulationBackend(): SimulationBackend {
    return {
        getState: fetchState,
        getRules: fetchRules,
        postControl,
        toggleCell: toggleCellRequest,
        setCell: setCellRequest,
        setCells: setCellsRequest,
    };
}
