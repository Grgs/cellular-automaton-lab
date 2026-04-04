/// <reference lib="webworker" />

import type {
    StandaloneInitMessage,
    StandaloneRequestMessage,
    StandaloneWorkerIncomingMessage,
    StandaloneWorkerOutgoingMessage,
} from "./standalone/protocol.js";

declare function importScripts(...urls: string[]): void;
declare let loadPyodide: ((options: { indexURL: string }) => Promise<any>) | undefined;

interface PythonBundleEntry {
    target_path: string;
    contents: string;
}

interface PythonBundle {
    version: number;
    files: PythonBundleEntry[];
}

const runtimeScope = self as DedicatedWorkerGlobalScope;
let pyodideInstance: any = null;
let initialized = false;
let currentSpeed = 1;
let running = false;
let tickTimer: number | null = null;
let operationChain: Promise<unknown> = Promise.resolve();

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

async function executePython(expression: string, globals: Record<string, unknown> = {}): Promise<string> {
    if (!pyodideInstance) {
        throw new Error("Pyodide runtime is unavailable.");
    }
    Object.entries(globals).forEach(([key, value]) => {
        pyodideInstance.globals.set(key, value);
    });
    return String(await pyodideInstance.runPythonAsync(expression));
}

async function fetchPythonBundle(url: string): Promise<PythonBundle> {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Standalone python bundle request failed: ${response.status}`);
    }
    const payload = await response.json() as PythonBundle;
    if (!Number.isFinite(Number(payload.version)) || !Array.isArray(payload.files)) {
        throw new Error("Standalone python bundle is invalid.");
    }
    return payload;
}

async function installPythonBundle(bundleUrl: string): Promise<void> {
    const bundle = await fetchPythonBundle(bundleUrl);
    for (const entry of bundle.files) {
        const targetPath = String(entry.target_path || "");
        const contents = String(entry.contents ?? "");
        if (!targetPath.startsWith("/app/")) {
            throw new Error("Standalone python bundle is invalid.");
        }
        const targetDirectory = targetPath.split("/").slice(0, -1).join("/");
        if (targetDirectory.length > 0) {
            pyodideInstance.FS.mkdirTree(targetDirectory);
        }
        pyodideInstance.FS.writeFile(targetPath, contents, { encoding: "utf8" });
    }
}

async function ensurePyodide(initMessage: StandaloneInitMessage): Promise<void> {
    if (pyodideInstance) {
        return;
    }
    importScripts(`${initMessage.pyodideBaseUrl.replace(/\/?$/, "/")}pyodide.js`);
    if (typeof loadPyodide !== "function") {
        throw new Error("Pyodide loader did not become available inside the standalone worker.");
    }
    pyodideInstance = await loadPyodide({ indexURL: initMessage.pyodideBaseUrl });
    await installPythonBundle(initMessage.pythonBundleUrl);
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
        await ensurePyodide(initMessage);
        const persistedSnapshotJson = initMessage.persistedSnapshot
            ? JSON.stringify(initMessage.persistedSnapshot)
            : null;
        const raw = await executePython(
            "browser_runtime.initialize_runtime(persisted_snapshot_json)",
            { persisted_snapshot_json: persistedSnapshotJson },
        );
        const payload = JSON.parse(raw) as { snapshot?: { running?: boolean; speed?: number }; persisted_snapshot?: object };
        const snapshot = payload.snapshot;
        syncSnapshotState(snapshot);
        scheduleTickLoop();
        initialized = true;
        postMessage({
            type: "ready",
            requestId: initMessage.requestId,
            snapshot: snapshot as never,
            persistedSnapshot: (payload.persisted_snapshot ?? null) as never,
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
                payload_json: request.payload === undefined ? null : JSON.stringify(request.payload),
            },
        );
        const payload = JSON.parse(raw) as {
            ok: boolean;
            error?: string;
            snapshot?: { running?: boolean; speed?: number };
            rules?: unknown[];
            persisted_snapshot?: object;
        };
        if (!payload.ok) {
            postMessage({
                type: "response",
                requestId: request.requestId,
                ok: false,
                error: payload.error || "Standalone runtime command failed.",
            });
            return;
        }
        syncSnapshotState(payload.snapshot);
        scheduleTickLoop();
        postMessage({
            type: "response",
            requestId: request.requestId,
            ok: true,
            ...(payload.snapshot === undefined ? {} : { snapshot: payload.snapshot as never }),
            ...(payload.rules === undefined ? {} : { rules: payload.rules as never }),
            ...(payload.persisted_snapshot === undefined ? {} : { persistedSnapshot: payload.persisted_snapshot as never }),
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
        const payload = JSON.parse(raw) as {
            ok: boolean;
            stepped?: boolean;
            snapshot?: { running?: boolean; speed?: number };
            persisted_snapshot?: object;
            error?: string;
        };
        if (!payload.ok) {
            throw new Error(payload.error || "Standalone tick failed.");
        }
        if (payload.stepped && payload.snapshot) {
            syncSnapshotState(payload.snapshot);
            if (payload.persisted_snapshot) {
                postMessage({
                    type: "persist",
                    persistedSnapshot: payload.persisted_snapshot as never,
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
