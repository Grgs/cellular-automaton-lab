import { afterEach, describe, expect, it, vi } from "vitest";

import type {
    AppBootstrapData,
    PersistedSimulationSnapshotV5,
    SimulationSnapshot,
} from "../types/domain.js";
import type {
    StandaloneInitMessage,
    StandaloneRequestMessage,
    StandaloneWorkerIncomingMessage,
    StandaloneWorkerOutgoingMessage,
} from "./protocol.js";

class FakeWorker {
    readonly postedMessages: StandaloneWorkerIncomingMessage[] = [];
    terminated = false;
    terminationCount = 0;
    private listeners = new Map<
        string,
        Set<(event: MessageEvent<StandaloneWorkerOutgoingMessage> | ErrorEvent) => void>
    >();

    addEventListener(
        type: string,
        listener: (event: MessageEvent<StandaloneWorkerOutgoingMessage> | ErrorEvent) => void,
    ): void {
        const existing = this.listeners.get(type) ?? new Set();
        existing.add(listener);
        this.listeners.set(type, existing);
    }

    removeEventListener(
        type: string,
        listener: (event: MessageEvent<StandaloneWorkerOutgoingMessage> | ErrorEvent) => void,
    ): void {
        this.listeners.get(type)?.delete(listener);
    }

    postMessage(message: StandaloneWorkerIncomingMessage): void {
        this.postedMessages.push(message);
    }

    terminate(): void {
        this.terminated = true;
        this.terminationCount += 1;
    }

    dispatchMessage(message: StandaloneWorkerOutgoingMessage): void {
        for (const listener of this.listeners.get("message") ?? []) {
            listener({ data: message } as MessageEvent<StandaloneWorkerOutgoingMessage>);
        }
    }

    dispatchError(message: string): void {
        for (const listener of this.listeners.get("error") ?? []) {
            listener({ message } as ErrorEvent);
        }
    }
}

const bootstrapData: AppBootstrapData = {
    app_defaults: {
        simulation: {
            topology_spec: {
                tiling_family: "square",
                adjacency_mode: "edge",
                sizing_mode: "grid",
                width: 10,
                height: 6,
                patch_depth: 0,
            },
            speed: 5,
            rule: "conway",
            min_grid_size: 4,
            max_grid_size: 200,
            min_patch_depth: 0,
            max_patch_depth: 6,
            min_speed: 1,
            max_speed: 30,
        },
        ui: {
            cell_size: 12,
            min_cell_size: 8,
            max_cell_size: 24,
            storage_key: "ui-key",
        },
        theme: {
            default: "light",
            storage_key: "theme-key",
        },
    },
    topology_catalog: [],
    periodic_face_tilings: [],
    aperiodic_families: [],
    server_meta: { app_name: "cellular-automaton-lab" },
    snapshot_version: 5,
};

const snapshot: SimulationSnapshot = {
    topology_spec: {
        tiling_family: "square",
        adjacency_mode: "edge",
        sizing_mode: "grid",
        width: 10,
        height: 6,
        patch_depth: 0,
    },
    speed: 5,
    running: false,
    generation: 0,
    state_revision: 0,
    state_epoch: 1,
    rule: {
        name: "conway",
        display_name: "Conway",
        description: "Classic Life",
        states: [{ value: 0, label: "Dead", color: "#000", paintable: true }],
        default_paint_state: 1,
        supports_randomize: true,
        rule_protocol: "universal-v1",
        supports_all_topologies: true,
        compatible_tiling_families: null,
    },
    topology_revision: "rev-1",
    topology: {
        topology_revision: "rev-1",
        topology_spec: {
            tiling_family: "square",
            adjacency_mode: "edge",
            sizing_mode: "grid",
            width: 10,
            height: 6,
            patch_depth: 0,
        },
        cells: [{ id: "c:0:0", kind: "cell", neighbors: [null, null, null, null] }],
    },
    cell_states: [0],
};

const persistedSnapshot: PersistedSimulationSnapshotV5 = {
    version: 5,
    topology_spec: snapshot.topology_spec,
    speed: 5,
    running: false,
    generation: 0,
    rule: "conway",
    cells_by_id: {},
};

async function loadWorkerClientModule() {
    vi.resetModules();
    const persistence = {
        load: vi.fn<() => Promise<PersistedSimulationSnapshotV5 | null>>(async () => null),
        save: vi.fn<(nextSnapshot: PersistedSimulationSnapshotV5) => Promise<void>>(async () => {}),
    };
    const createSimulationStatePersistence = vi.fn(async () => persistence);
    const workers: FakeWorker[] = [];
    function rememberWorker(worker: FakeWorker): void {
        workers.push(worker);
    }

    vi.stubGlobal(
        "Worker",
        class WorkerStub extends FakeWorker {
            constructor(_url: URL, _options: WorkerOptions) {
                super();
                rememberWorker(this);
            }
        },
    );

    vi.doMock("./persistence.js", () => ({
        createSimulationStatePersistence,
    }));

    const module = await import("./worker-client.js");
    return {
        module,
        persistence,
        createSimulationStatePersistence,
        workers,
        worker: (index = workers.length - 1) => {
            const resolvedWorker = workers[index];
            if (!resolvedWorker) {
                throw new Error("worker was not created");
            }
            return resolvedWorker;
        },
    };
}

function lastInitMessage(worker: FakeWorker): StandaloneInitMessage {
    const message = worker.postedMessages.at(-1);
    if (!message || message.type !== "init") {
        throw new Error("expected init message");
    }
    return message;
}

function lastRequestMessage(worker: FakeWorker): StandaloneRequestMessage {
    const message = worker.postedMessages.at(-1);
    if (!message || message.type !== "request") {
        throw new Error("expected request message");
    }
    return message;
}

afterEach(() => {
    vi.resetModules();
    vi.doUnmock("./persistence.js");
    vi.unstubAllGlobals();
});

async function flushAsyncStartup(): Promise<void> {
    await Promise.resolve();
    await Promise.resolve();
}

describe("standalone worker client", () => {
    it("initializes successfully and proxies state requests", async () => {
        const { module, persistence, worker } = await loadWorkerClientModule();

        const environmentPromise = module.createStandaloneEnvironment(bootstrapData);
        await flushAsyncStartup();
        const initMessage = lastInitMessage(worker());
        expect(initMessage.pythonBundleUrl).toContain("standalone-python-bundle.json");
        expect(initMessage).not.toHaveProperty("pyodideBaseUrl");
        worker().dispatchMessage({
            type: "ready",
            requestId: initMessage.requestId,
            snapshot,
            persistedSnapshot,
        });

        const environment = await environmentPromise;
        expect(persistence.save).toHaveBeenCalledWith(persistedSnapshot);
        expect(environment.runtimeEnvironment).toMatchObject({
            liveForks: {
                kind: "supported",
                baseSessionId: "standalone",
                maxConcurrent: 2,
            },
            persistence: { scope: "browser-device", guarantee: "best-effort-local" },
        });

        const statePromise = environment.backend.getState();
        const requestMessage = lastRequestMessage(worker());
        worker().dispatchMessage({
            type: "response",
            requestId: requestMessage.requestId,
            ok: true,
            snapshot,
        });

        await expect(statePromise).resolves.toEqual(snapshot);
    });

    it("rejects initialization failures and disposes the worker", async () => {
        const { module, worker } = await loadWorkerClientModule();

        const environmentPromise = module.createStandaloneEnvironment(bootstrapData);
        await flushAsyncStartup();
        const initMessage = lastInitMessage(worker());
        worker().dispatchMessage({
            type: "ready",
            requestId: initMessage.requestId,
            error: "Pyodide failed to load",
        });

        await expect(environmentPromise).rejects.toThrow("Pyodide failed to load");
        expect(worker().terminated).toBe(true);
    });

    it("can initialize temporary runtimes without persisted state", async () => {
        const { module, persistence, createSimulationStatePersistence, worker } =
            await loadWorkerClientModule();

        const environmentPromise = module.createStandaloneEnvironment(bootstrapData, {
            persistState: false,
        });
        await flushAsyncStartup();
        const initMessage = lastInitMessage(worker());
        expect(initMessage.persistedSnapshot).toBeNull();
        expect(createSimulationStatePersistence).not.toHaveBeenCalled();
        worker().dispatchMessage({
            type: "ready",
            requestId: initMessage.requestId,
            snapshot,
            persistedSnapshot,
        });

        await expect(environmentPromise).resolves.toEqual(
            expect.objectContaining({
                backend: expect.objectContaining({ getState: expect.any(Function) }),
                bootstrapData,
                runtimeEnvironment: expect.objectContaining({
                    persistence: { scope: "none", guarantee: "ephemeral" },
                }),
            }),
        );
        expect(persistence.save).not.toHaveBeenCalled();
    });

    it("does not create a worker when initialization is already aborted", async () => {
        const { module, workers } = await loadWorkerClientModule();
        const abortController = new AbortController();
        abortController.abort();

        await expect(
            module.createStandaloneEnvironment(bootstrapData, {
                signal: abortController.signal,
            }),
        ).rejects.toThrow("aborted");
        expect(workers).toHaveLength(0);
    });

    it("terminates a worker when initialization is aborted", async () => {
        const { module, worker } = await loadWorkerClientModule();
        const abortController = new AbortController();

        const environmentPromise = module.createStandaloneEnvironment(bootstrapData, {
            persistState: false,
            signal: abortController.signal,
        });
        await flushAsyncStartup();
        const initMessage = lastInitMessage(worker());

        abortController.abort();
        worker().dispatchMessage({
            type: "ready",
            requestId: initMessage.requestId,
            snapshot,
            persistedSnapshot: null,
        });

        await expect(environmentPromise).rejects.toThrow("disposed");
        expect(worker().terminated).toBe(true);
        expect(worker().terminationCount).toBe(1);
    });

    it("immediately terminates a live fork disposed during startup", async () => {
        const { module, worker, workers } = await loadWorkerClientModule();
        const environmentPromise = module.createStandaloneEnvironment(bootstrapData, {
            persistState: false,
        });
        await flushAsyncStartup();
        const mainInitMessage = lastInitMessage(worker(0));
        worker(0).dispatchMessage({
            type: "ready",
            requestId: mainInitMessage.requestId,
            snapshot,
            persistedSnapshot: null,
        });
        const environment = await environmentPromise;
        if (environment.runtimeEnvironment.liveForks.kind !== "supported") {
            throw new Error("expected live forks to be supported");
        }

        const fork = environment.runtimeEnvironment.liveForks.backendFactory("profile-fork");
        const statePromise = fork.getState();
        await flushAsyncStartup();
        expect(workers).toHaveLength(2);
        const forkWorker = worker(1);
        const forkInitMessage = lastInitMessage(forkWorker);

        fork.dispose();
        fork.dispose();
        forkWorker.dispatchMessage({
            type: "ready",
            requestId: forkInitMessage.requestId,
            snapshot,
            persistedSnapshot: null,
        });

        await expect(statePromise).rejects.toThrow("disposed");
        expect(forkWorker.terminated).toBe(true);
        expect(forkWorker.terminationCount).toBe(1);
        expect(worker(0).terminated).toBe(false);
    });

    it("rejects failed command responses", async () => {
        const { module, worker } = await loadWorkerClientModule();

        const environmentPromise = module.createStandaloneEnvironment(bootstrapData);
        await flushAsyncStartup();
        const initMessage = lastInitMessage(worker());
        worker().dispatchMessage({
            type: "ready",
            requestId: initMessage.requestId,
            snapshot,
            persistedSnapshot: null,
        });
        const environment = await environmentPromise;

        const statePromise = environment.backend.getState();
        const requestMessage = lastRequestMessage(worker());
        worker().dispatchMessage({
            type: "response",
            requestId: requestMessage.requestId,
            ok: false,
            error: "state failed",
            code: "topology_cell_budget_exceeded",
            limit: 20_000,
            actual_cells: 20_001,
        });

        await expect(statePromise).rejects.toMatchObject({
            message: "state failed",
            code: "topology_cell_budget_exceeded",
            limit: 20_000,
            actualCells: 20_001,
        });
    });

    it("applies cell deltas and persists the reconciled snapshot", async () => {
        const { module, persistence, worker } = await loadWorkerClientModule();
        const environmentPromise = module.createStandaloneEnvironment(bootstrapData);
        await flushAsyncStartup();
        const initMessage = lastInitMessage(worker());
        worker().dispatchMessage({
            type: "ready",
            requestId: initMessage.requestId,
            snapshot,
            persistedSnapshot: null,
        });
        const environment = await environmentPromise;

        const mutationPromise = environment.backend.setCell({ id: "c:0:0" }, 1);
        const requestMessage = lastRequestMessage(worker());
        worker().dispatchMessage({
            type: "response",
            requestId: requestMessage.requestId,
            ok: true,
            cellDelta: {
                base_state_revision: 0,
                state_revision: 1,
                state_epoch: 1,
                topology_revision: "rev-1",
                generation: 0,
                cell_updates: [{ id: "c:0:0", state: 1 }],
            },
        });

        await expect(mutationPromise).resolves.toMatchObject({
            state_revision: 1,
            state_epoch: 1,
            cell_states: [1],
        });
        expect(persistence.save).toHaveBeenLastCalledWith(
            expect.objectContaining({ cells_by_id: { "c:0:0": 1 } }),
        );
    });

    it("forces a full-state resync when a cell delta is stale", async () => {
        const { module, worker } = await loadWorkerClientModule();
        const environmentPromise = module.createStandaloneEnvironment(bootstrapData);
        await flushAsyncStartup();
        const initMessage = lastInitMessage(worker());
        worker().dispatchMessage({
            type: "ready",
            requestId: initMessage.requestId,
            snapshot,
            persistedSnapshot: null,
        });
        const environment = await environmentPromise;

        const mutationPromise = environment.backend.setCell({ id: "c:0:0" }, 1);
        const mutationMessage = lastRequestMessage(worker());
        worker().dispatchMessage({
            type: "response",
            requestId: mutationMessage.requestId,
            ok: true,
            cellDelta: {
                base_state_revision: 9,
                state_revision: 10,
                state_epoch: 1,
                topology_revision: "rev-1",
                generation: 0,
                cell_updates: [{ id: "c:0:0", state: 1 }],
            },
        });
        await vi.waitFor(() => expect(lastRequestMessage(worker()).path).toBe("/api/state"));
        const stateMessage = lastRequestMessage(worker());
        worker().dispatchMessage({
            type: "response",
            requestId: stateMessage.requestId,
            ok: true,
            snapshot: { ...snapshot, state_revision: 2, cell_states: [1] },
        });

        await expect(mutationPromise).resolves.toMatchObject({
            state_revision: 2,
            state_epoch: 1,
            cell_states: [1],
        });
    });

    it("disposes pending requests and terminates the worker", async () => {
        const { module, worker } = await loadWorkerClientModule();

        const environmentPromise = module.createStandaloneEnvironment(bootstrapData);
        await flushAsyncStartup();
        const initMessage = lastInitMessage(worker());
        worker().dispatchMessage({
            type: "ready",
            requestId: initMessage.requestId,
            snapshot,
            persistedSnapshot: null,
        });
        const environment = await environmentPromise;

        const statePromise = environment.backend.getState();
        const requestMessage = lastRequestMessage(worker());
        expect(requestMessage.path).toBe("/api/state");

        environment.backend.dispose();

        await expect(statePromise).rejects.toThrow("disposed");
        expect(worker().terminated).toBe(true);
    });
});
