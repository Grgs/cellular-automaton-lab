import { afterEach, describe, expect, it, vi } from "vitest";

import type { AppBootstrapData, PersistedSimulationSnapshotV5, SimulationSnapshot } from "../types/domain.js";
import type {
    StandaloneInitMessage,
    StandaloneRequestMessage,
    StandaloneWorkerIncomingMessage,
    StandaloneWorkerOutgoingMessage,
} from "./protocol.js";

class FakeWorker {
    readonly postedMessages: StandaloneWorkerIncomingMessage[] = [];
    terminated = false;
    private listeners = new Map<string, Set<(event: MessageEvent<StandaloneWorkerOutgoingMessage> | ErrorEvent) => void>>();

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
    rule: {
        name: "conway",
        display_name: "Conway",
        description: "Classic Life",
        states: [{ value: 0, label: "Dead", color: "#000", paintable: true }],
        default_paint_state: 1,
        supports_randomize: true,
        rule_protocol: "universal-v1",
        supports_all_topologies: true,
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
    let lastWorker: FakeWorker | null = null;

    vi.stubGlobal(
        "Worker",
        class WorkerStub extends FakeWorker {
            constructor(_url: URL, _options: WorkerOptions) {
                super();
                lastWorker = this;
            }
        },
    );

    vi.doMock("./persistence.js", () => ({
        createSimulationStatePersistence: vi.fn(async () => persistence),
    }));

    const module = await import("./worker-client.js");
    return {
        module,
        persistence,
        worker: () => {
            if (!lastWorker) {
                throw new Error("worker was not created");
            }
            return lastWorker;
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
        worker().dispatchMessage({
            type: "ready",
            requestId: initMessage.requestId,
            snapshot,
            persistedSnapshot,
        });

        const environment = await environmentPromise;
        expect(persistence.save).toHaveBeenCalledWith(persistedSnapshot);

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
        });

        await expect(statePromise).rejects.toThrow("state failed");
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
