/// <reference lib="webworker" />

import type {
    StandaloneInitMessage,
    StandaloneRequestMessage,
    StandaloneWorkerIncomingMessage,
    StandaloneWorkerOutgoingMessage,
} from "./standalone/protocol.js";
import type { PlainObject } from "./runtime-validation.js";
import {
    decodeInitResponse,
    decodeRequestResponse,
    decodeTickResponse,
} from "./standalone/runtime-decoders.js";

const PYODIDE_BASE_URL = "../pyodide/";
const PYODIDE_SCRIPT_URL = `${PYODIDE_BASE_URL}pyodide.mjs`;

interface PyodideRuntime {
    globals: {
        set(key: string, value: unknown): void;
    };
    FS: {
        mkdirTree(path: string): void;
        writeFile(path: string, contents: string, options: { encoding: "utf8" }): void;
    };
    runPythonAsync(expression: string): Promise<unknown>;
}

interface PyodideLoaderModule {
    loadPyodide?: (options: { indexURL: string }) => Promise<PyodideRuntime>;
}

interface PythonBundleEntry {
    target_path: string;
    contents: string;
}

interface PythonBundle {
    version: number;
    files: PythonBundleEntry[];
}

const runtimeScope = self as DedicatedWorkerGlobalScope;
let pyodideInstance: PyodideRuntime | null = null;
let initialized = false;
let currentSpeed = 1;
let running = false;
let tickTimer: number | null = null;
let operationChain: Promise<void> = Promise.resolve();

function postMessage(message: StandaloneWorkerOutgoingMessage): void {
    runtimeScope.postMessage(message);
}

function runSerialized<T>(task: () => Promise<T>): Promise<T> {
    const result = operationChain.then(task, task);
    operationChain = result.then(
        () => undefined,
        () => undefined,
    );
    return result;
}

function clearTickTimer(): void {
    if (tickTimer !== null) {
        runtimeScope.clearTimeout(tickTimer);
        tickTimer = null;
    }
}

function scheduleTickLoop(): void {
    clearTickTimer();
    if (!running) {
        return;
    }
    const delay = Math.max(20, Math.round(1000 / Math.max(1, currentSpeed)));
    tickTimer = runtimeScope.setTimeout(() => {
        void runSerialized(executeTick);
    }, delay);
}

async function executePython(expression: string, globals: PlainObject = {}): Promise<string> {
    const runtime = pyodideInstance;
    if (!runtime) {
        throw new Error("Pyodide runtime is unavailable.");
    }
    Object.entries(globals).forEach(([key, value]) => {
        runtime.globals.set(key, value);
    });
    return String(await runtime.runPythonAsync(expression));
}

async function fetchPythonBundle(url: string): Promise<PythonBundle> {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Standalone python bundle request failed: ${response.status}`);
    }
    const payload = (await response.json()) as PythonBundle;
    if (!Number.isFinite(Number(payload.version)) || !Array.isArray(payload.files)) {
        throw new Error("Standalone python bundle is invalid.");
    }
    return payload;
}

async function installPythonBundle(bundleUrl: string): Promise<void> {
    const runtime = pyodideInstance;
    if (!runtime) {
        throw new Error("Pyodide runtime is unavailable.");
    }
    const bundle = await fetchPythonBundle(bundleUrl);
    for (const entry of bundle.files) {
        const targetPath = String(entry.target_path || "");
        const contents = String(entry.contents ?? "");
        if (!targetPath.startsWith("/app/")) {
            throw new Error("Standalone python bundle is invalid.");
        }
        const targetDirectory = targetPath.split("/").slice(0, -1).join("/");
        if (targetDirectory.length > 0) {
            runtime.FS.mkdirTree(targetDirectory);
        }
        runtime.FS.writeFile(targetPath, contents, { encoding: "utf8" });
    }
}

async function ensurePyodide(pythonBundleUrl: string): Promise<void> {
    if (pyodideInstance) {
        return;
    }
    const loader = (await import(/* @vite-ignore */ PYODIDE_SCRIPT_URL)) as PyodideLoaderModule;
    if (typeof loader.loadPyodide !== "function") {
        throw new Error("Pyodide loader did not become available inside the standalone worker.");
    }
    pyodideInstance = await loader.loadPyodide({ indexURL: PYODIDE_BASE_URL });
    await installPythonBundle(pythonBundleUrl);
    await pyodideInstance.runPythonAsync(`
import sys
if "/app" not in sys.path:
    sys.path.insert(0, "/app")
import backend.browser_runtime as browser_runtime
`);
}

function syncSnapshotState(snapshot: { running?: boolean; speed?: number } | undefined): void {
    running = Boolean(snapshot?.running);
    currentSpeed = Number(snapshot?.speed) || currentSpeed;
}

async function handleInit(initMessage: StandaloneInitMessage): Promise<void> {
    try {
        await ensurePyodide(initMessage.pythonBundleUrl);
        const persistedSnapshotJson = initMessage.persistedSnapshot
            ? JSON.stringify(initMessage.persistedSnapshot)
            : null;
        const raw = await executePython(
            "browser_runtime.initialize_runtime(persisted_snapshot_json)",
            { persisted_snapshot_json: persistedSnapshotJson },
        );
        const payload = decodeInitResponse(raw);
        const snapshot = payload.snapshot;
        if (!snapshot) {
            throw new Error("Standalone init did not return a simulation snapshot.");
        }
        syncSnapshotState(snapshot);
        scheduleTickLoop();
        initialized = true;
        postMessage({
            type: "ready",
            requestId: initMessage.requestId,
            snapshot,
            persistedSnapshot: payload.persistedSnapshot,
        });
    } catch (error) {
        postMessage({
            type: "ready",
            requestId: initMessage.requestId,
            error: error instanceof Error ? error.message : String(error),
        });
    }
}

async function handleRequest(request: StandaloneRequestMessage): Promise<void> {
    if (!initialized) {
        postMessage({
            type: "response",
            requestId: request.requestId,
            ok: false,
            error: "Standalone runtime has not been initialized.",
        });
        return;
    }
    try {
        const raw = await executePython(
            "browser_runtime.handle_request(request_path, payload_json)",
            {
                request_path: request.path,
                payload_json:
                    request.payload === undefined ? null : JSON.stringify(request.payload),
            },
        );
        const payload = decodeRequestResponse(raw);
        if (!payload.ok) {
            postMessage({
                type: "response",
                requestId: request.requestId,
                ok: false,
                error: payload.error || "Standalone runtime command failed.",
                ...(payload.code === undefined ? {} : { code: payload.code }),
                ...(payload.limit === undefined ? {} : { limit: payload.limit }),
                ...(payload.estimated_cells === undefined
                    ? {}
                    : { estimated_cells: payload.estimated_cells }),
                ...(payload.actual_cells === undefined
                    ? {}
                    : { actual_cells: payload.actual_cells }),
            });
            return;
        }
        if (payload.snapshot !== undefined) {
            syncSnapshotState(payload.snapshot);
        }
        scheduleTickLoop();
        postMessage({
            type: "response",
            requestId: request.requestId,
            ok: true,
            ...(payload.snapshot === undefined ? {} : { snapshot: payload.snapshot }),
            ...(payload.rules === undefined ? {} : { rules: payload.rules }),
            ...(payload.comparison === undefined ? {} : { comparison: payload.comparison }),
            ...(payload.filmstrip === undefined ? {} : { filmstrip: payload.filmstrip }),
            ...(payload.topologyPreview === undefined
                ? {}
                : { topologyPreview: payload.topologyPreview }),
            ...(payload.cellDelta === undefined ? {} : { cellDelta: payload.cellDelta }),
            ...(payload.persistedSnapshot === undefined
                ? {}
                : { persistedSnapshot: payload.persistedSnapshot }),
        });
    } catch (error) {
        postMessage({
            type: "response",
            requestId: request.requestId,
            ok: false,
            error: error instanceof Error ? error.message : String(error),
        });
    }
}

async function executeTick(): Promise<void> {
    if (!initialized || !running) {
        clearTickTimer();
        return;
    }
    try {
        const raw = await executePython("browser_runtime.tick_running()");
        const payload = decodeTickResponse(raw);
        if (!payload.ok) {
            throw new Error(payload.error || "Standalone tick failed.");
        }
        if (payload.stepped && payload.snapshot) {
            syncSnapshotState(payload.snapshot);
            if (payload.persistedSnapshot) {
                postMessage({
                    type: "persist",
                    persistedSnapshot: payload.persistedSnapshot,
                });
            }
        }
    } catch (error) {
        running = false;
        console.error("Standalone runtime tick failed", error);
    } finally {
        scheduleTickLoop();
    }
}

runtimeScope.addEventListener("message", (event: MessageEvent<StandaloneWorkerIncomingMessage>) => {
    void runSerialized(async () => {
        if (event.data.type === "init") {
            await handleInit(event.data);
            return;
        }
        await handleRequest(event.data);
    });
});
