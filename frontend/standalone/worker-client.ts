import type { AppBootstrapData, RulesResponse, SimulationSnapshot } from "../types/domain.js";
import type { ConfigSyncBody, ResetControlBody, SimulationBackend } from "../types/controller.js";
import { createSimulationStatePersistence } from "./persistence.js";
import type {
    StandaloneCommandPath,
    StandaloneErrorResponse,
    StandaloneInitErrorResponse,
    StandaloneReadyResponse,
    StandaloneRequestMessage,
    StandaloneRequestPayload,
    StandaloneSuccessResponse,
    StandaloneWorkerIncomingMessage,
    StandaloneWorkerOutgoingMessage,
} from "./protocol.js";

const DEFAULT_PYODIDE_BASE_URL = "https://cdn.jsdelivr.net/pyodide/v0.27.5/full/";

interface PendingRequest {
    resolve: (
        value:
            | StandaloneSuccessResponse
            | StandaloneReadyResponse
            | StandaloneInitErrorResponse
            | StandaloneErrorResponse,
    ) => void;
    reject: (error: Error) => void;
}

function createRequestId(): string {
    return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

function requireSnapshot(snapshot: SimulationSnapshot | undefined): SimulationSnapshot {
    if (!snapshot) {
        throw new Error("Standalone runtime did not return a simulation snapshot.");
    }
    return snapshot;
}

export async function createStandaloneEnvironment(bootstrapData: AppBootstrapData): Promise<{
    backend: SimulationBackend;
    bootstrapData: AppBootstrapData;
}> {
    const persistence = await createSimulationStatePersistence();
    const worker = new Worker(new URL("../standalone-worker.ts", import.meta.url), {
        type: "classic",
    });
    const pendingRequests = new Map<string, PendingRequest>();
    let fatalError: Error | null = null;
    let disposed = false;

    function rejectPending(error: Error): void {
        fatalError = error;
        pendingRequests.forEach((pending) => pending.reject(error));
        pendingRequests.clear();
    }

    function handleWorkerError(event: ErrorEvent): void {
        rejectPending(new Error(event.message || "Standalone worker crashed."));
    }

    function handleWorkerMessage(event: MessageEvent<StandaloneWorkerOutgoingMessage>): void {
        if (disposed) {
            return;
        }
        const message = event.data;
        if (message.type === "persist") {
            void persistence.save(message.persistedSnapshot);
            return;
        }
        const pending = pendingRequests.get(message.requestId);
        if (!pending) {
            return;
        }
        pendingRequests.delete(message.requestId);
        pending.resolve(message);
    }

    function dispose(): void {
        if (disposed) {
            return;
        }
        disposed = true;
        worker.removeEventListener("error", handleWorkerError);
        worker.removeEventListener("message", handleWorkerMessage);
        rejectPending(new Error("Standalone runtime was disposed."));
        worker.terminate();
    }

    worker.addEventListener("error", handleWorkerError);
    worker.addEventListener("message", handleWorkerMessage);

    async function sendMessage(
        message: StandaloneWorkerIncomingMessage,
    ): Promise<
        | StandaloneSuccessResponse
        | StandaloneReadyResponse
        | StandaloneInitErrorResponse
        | StandaloneErrorResponse
    > {
        if (disposed) {
            throw new Error("Standalone runtime was disposed.");
        }
        if (fatalError) {
            throw fatalError;
        }
        return new Promise((resolve, reject) => {
            pendingRequests.set(message.requestId, { resolve, reject });
            worker.postMessage(message);
        });
    }

    const persistedSnapshot = await persistence.load();
    const initRequestId = createRequestId();
    let initResponse:
        | StandaloneSuccessResponse
        | StandaloneReadyResponse
        | StandaloneInitErrorResponse
        | StandaloneErrorResponse;
    try {
        initResponse = await sendMessage({
            type: "init",
            requestId: initRequestId,
            persistedSnapshot,
            pythonBundleUrl: new URL(
                /* @vite-ignore */ "../standalone-python-bundle.json",
                import.meta.url,
            ).toString(),
            pyodideBaseUrl: DEFAULT_PYODIDE_BASE_URL,
        });
    } catch (error) {
        dispose();
        throw error;
    }

    if ("error" in initResponse) {
        dispose();
        throw new Error(initResponse.error);
    }
    if (initResponse.persistedSnapshot) {
        await persistence.save(initResponse.persistedSnapshot);
    }

    async function request(
        path: StandaloneCommandPath,
        payload?: StandaloneRequestPayload,
    ): Promise<StandaloneSuccessResponse> {
        if (fatalError) {
            throw fatalError;
        }
        const response = await sendMessage({
            type: "request",
            requestId: createRequestId(),
            path,
            ...(payload === undefined ? {} : { payload }),
        } satisfies StandaloneRequestMessage);
        if (!("ok" in response)) {
            throw new Error("Standalone runtime returned an unexpected response.");
        }
        if (!response.ok) {
            throw new Error(response.error);
        }
        if (response.persistedSnapshot) {
            await persistence.save(response.persistedSnapshot);
        }
        return response;
    }

    type ControlRequestPayload = ResetControlBody | ConfigSyncBody;

    async function postControl(
        path: "/api/control/reset",
        body: ResetControlBody,
    ): Promise<SimulationSnapshot>;
    async function postControl(
        path: "/api/config",
        body: ConfigSyncBody,
    ): Promise<SimulationSnapshot>;
    async function postControl(
        path:
            | "/api/control/start"
            | "/api/control/pause"
            | "/api/control/resume"
            | "/api/control/step",
    ): Promise<SimulationSnapshot>;
    async function postControl(
        path: StandaloneCommandPath,
        body?: ControlRequestPayload,
    ): Promise<SimulationSnapshot> {
        const response = await request(path, body);
        return requireSnapshot(response.snapshot);
    }

    const backend: SimulationBackend = {
        async getState() {
            const response = await request("/api/state");
            return requireSnapshot(response.snapshot);
        },
        async getRules(): Promise<RulesResponse> {
            const response = await request("/api/rules");
            return { rules: response.rules ?? [] };
        },
        dispose,
        postControl,
        async toggleCell(cell) {
            const response = await request("/api/cells/toggle", { id: cell.id });
            return requireSnapshot(response.snapshot);
        },
        async setCell(cell, state) {
            const response = await request("/api/cells/set", { id: cell.id, state });
            return requireSnapshot(response.snapshot);
        },
        async setCells(cells) {
            const response = await request("/api/cells/set-many", { cells });
            return requireSnapshot(response.snapshot);
        },
    };

    return {
        backend,
        bootstrapData,
    };
}
