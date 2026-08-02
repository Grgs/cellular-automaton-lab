import type { AppBootstrapData, RulesResponse, SimulationSnapshot } from "../types/domain.js";
import type {
    AppRuntimeEnvironment,
    ConfigSyncBody,
    ResetControlBody,
    SimulationBackend,
} from "../types/controller.js";
import { createSimulationStatePersistence } from "./persistence.js";
import { persistedSnapshotFrom, SimulationSnapshotCache } from "../simulation-snapshot-cache.js";
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
import { BackendRequestError } from "../backend-request-error.js";

export interface StandaloneEnvironmentOptions {
    persistState?: boolean;
}

// Each live fork boots a persist-free Pyodide runtime. Two concurrent forks
// is the explicit standalone memory/CPU budget.
const STANDALONE_FORK_CAPACITY = 2;

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

function createStandalonePaneBackendFactory(
    bootstrapData: AppBootstrapData,
): (sessionId: string) => SimulationBackend {
    return () => {
        let backend: SimulationBackend | null = null;
        let environmentPromise: Promise<SimulationBackend> | null = null;
        let disposed = false;

        async function resolveBackend(): Promise<SimulationBackend> {
            if (disposed) {
                throw new Error("Standalone pane runtime was disposed.");
            }
            if (!environmentPromise) {
                environmentPromise = createStandaloneEnvironment(bootstrapData, {
                    persistState: false,
                }).then((environment) => {
                    if (disposed) {
                        void environment.backend.dispose();
                        throw new Error("Standalone pane runtime was disposed.");
                    }
                    backend = environment.backend;
                    return environment.backend;
                });
            }
            return environmentPromise;
        }

        const postControl = (async (path: string, body?: unknown) => {
            const resolvedBackend = await resolveBackend();
            const delegate = resolvedBackend.postControl as (
                nextPath: string,
                nextBody?: unknown,
            ) => ReturnType<SimulationBackend["getState"]>;
            return body === undefined ? delegate(path) : delegate(path, body);
        }) as SimulationBackend["postControl"];

        return {
            getState: async () => (await resolveBackend()).getState(),
            getRules: async () => (await resolveBackend()).getRules(),
            dispose: () => {
                disposed = true;
                if (backend) {
                    void backend.dispose();
                    return;
                }
                // A replaced wall can dispose a fork while it is still booting.
                void environmentPromise
                    ?.then((resolvedBackend) => resolvedBackend.dispose())
                    .catch(() => undefined);
            },
            postControl,
            toggleCell: async (cell) => (await resolveBackend()).toggleCell(cell),
            setCell: async (cell, state) => (await resolveBackend()).setCell(cell, state),
            setCells: async (cells) => (await resolveBackend()).setCells(cells),
            compareSeed: async (request) => (await resolveBackend()).compareSeed(request),
            requestFilmstrip: async (request) => (await resolveBackend()).requestFilmstrip(request),
            previewTopology: async (request) => (await resolveBackend()).previewTopology(request),
        };
    };
}

function standaloneRuntimeEnvironment(
    bootstrapData: AppBootstrapData,
    persistState: boolean,
): AppRuntimeEnvironment {
    return {
        liveForks: {
            kind: "supported",
            baseSessionId: "standalone",
            backendFactory: createStandalonePaneBackendFactory(bootstrapData),
            maxConcurrent: STANDALONE_FORK_CAPACITY,
        },
        persistence: persistState
            ? { scope: "browser-device", guarantee: "best-effort-local" }
            : { scope: "none", guarantee: "ephemeral" },
    };
}

export async function createStandaloneEnvironment(
    bootstrapData: AppBootstrapData,
    { persistState = true }: StandaloneEnvironmentOptions = {},
): Promise<{
    backend: SimulationBackend;
    bootstrapData: AppBootstrapData;
    runtimeEnvironment: AppRuntimeEnvironment;
}> {
    const persistence = persistState ? await createSimulationStatePersistence() : null;
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
            if (persistence) {
                void persistence.save(message.persistedSnapshot);
            }
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

    const persistedSnapshot = persistence ? await persistence.load() : null;
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
        });
    } catch (error) {
        dispose();
        throw error;
    }

    if ("error" in initResponse) {
        dispose();
        throw new Error(initResponse.error);
    }
    if (initResponse.persistedSnapshot && persistence) {
        await persistence.save(initResponse.persistedSnapshot);
    }
    const snapshots = new SimulationSnapshotCache();
    snapshots.install(requireSnapshot(initResponse.snapshot), null);

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
            throw new BackendRequestError(response.error, {
                ...(response.code === undefined ? {} : { code: response.code }),
                ...(response.limit === undefined ? {} : { limit: response.limit }),
                ...(response.estimated_cells === undefined
                    ? {}
                    : { estimatedCells: response.estimated_cells }),
                ...(response.actual_cells === undefined
                    ? {}
                    : { actualCells: response.actual_cells }),
            });
        }
        return response;
    }

    async function persistAcceptedSnapshot(snapshot: SimulationSnapshot): Promise<void> {
        if (persistence) {
            await persistence.save(persistedSnapshotFrom(snapshot));
        }
    }

    async function fetchFullState(): Promise<SimulationSnapshot> {
        const requestBase = snapshots.current();
        const response = await request("/api/state");
        const snapshot = snapshots.install(requireSnapshot(response.snapshot), requestBase);
        await persistAcceptedSnapshot(snapshot);
        return snapshot;
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
        const requestBase = snapshots.current();
        const response = await request(path, body);
        const snapshot = snapshots.install(requireSnapshot(response.snapshot), requestBase);
        await persistAcceptedSnapshot(snapshot);
        return snapshot;
    }

    async function reconcileCellResponse(
        response: StandaloneSuccessResponse,
    ): Promise<SimulationSnapshot> {
        if (!response.cellDelta) {
            throw new Error("Standalone runtime did not return a cell-mutation delta.");
        }
        const snapshot = await snapshots.reconcileDelta(response.cellDelta, fetchFullState);
        await persistAcceptedSnapshot(snapshot);
        return snapshot;
    }

    const backend: SimulationBackend = {
        async getState() {
            return fetchFullState();
        },
        async getRules(): Promise<RulesResponse> {
            const response = await request("/api/rules");
            return { rules: response.rules ?? [] };
        },
        dispose,
        postControl,
        async toggleCell(cell) {
            const response = await request("/api/cells/toggle", { id: cell.id });
            return reconcileCellResponse(response);
        },
        async setCell(cell, state) {
            const response = await request("/api/cells/set", { id: cell.id, state });
            return reconcileCellResponse(response);
        },
        async setCells(cells) {
            const response = await request("/api/cells/set-many", { cells });
            return reconcileCellResponse(response);
        },
        async compareSeed(compareRequest, _options) {
            const response = await request("/api/compare", compareRequest);
            if (!response.comparison) {
                throw new Error("Standalone runtime did not return a comparison result.");
            }
            return response.comparison;
        },
        async requestFilmstrip(filmstripRequest, _options) {
            const response = await request("/api/compare/filmstrip", filmstripRequest);
            if (!response.filmstrip) {
                throw new Error("Standalone runtime did not return a filmstrip result.");
            }
            return response.filmstrip;
        },
        async previewTopology(previewRequest) {
            const response = await request("/api/topology/preview", previewRequest);
            if (!response.topologyPreview) {
                throw new Error("Standalone runtime did not return a topology preview.");
            }
            return response.topologyPreview;
        },
    };

    return {
        backend,
        bootstrapData,
        runtimeEnvironment: standaloneRuntimeEnvironment(bootstrapData, persistState),
    };
}
