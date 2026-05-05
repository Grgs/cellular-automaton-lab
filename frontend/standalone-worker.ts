/// <reference lib="webworker" />

import type {
    PersistedSimulationSnapshotV5,
    RuleDefinition,
    RulesResponse,
    SimulationSnapshot,
    TopologyPayload,
    TopologySpec,
} from "./types/domain.js";
import type {
    StandaloneInitMessage,
    StandaloneRequestMessage,
    StandaloneWorkerIncomingMessage,
    StandaloneWorkerOutgoingMessage,
} from "./standalone/protocol.js";
import type { PlainObject } from "./runtime-validation.js";
import { isPlainObject } from "./runtime-validation.js";

declare function importScripts(...urls: string[]): void;
declare let loadPyodide: ((options: { indexURL: string }) => Promise<PyodideRuntime>) | undefined;

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

function parseRuntimeJson(raw: string, context: string): PlainObject {
    const payload: unknown = JSON.parse(raw);
    if (!isPlainObject(payload)) {
        throw new Error(`${context} returned an invalid payload.`);
    }
    return payload;
}

function requireTopologySpec(value: unknown, context: string): TopologySpec {
    if (
        !isPlainObject(value) ||
        typeof value.tiling_family !== "string" ||
        typeof value.adjacency_mode !== "string" ||
        typeof value.sizing_mode !== "string" ||
        typeof value.width !== "number" ||
        typeof value.height !== "number" ||
        typeof value.patch_depth !== "number"
    ) {
        throw new Error(`${context} returned an invalid topology spec.`);
    }
    return {
        tiling_family: value.tiling_family,
        adjacency_mode: value.adjacency_mode,
        sizing_mode: value.sizing_mode,
        width: value.width,
        height: value.height,
        patch_depth: value.patch_depth,
    };
}

function requireRuleDefinition(value: unknown, context: string): RuleDefinition {
    if (
        !isPlainObject(value) ||
        typeof value.name !== "string" ||
        typeof value.display_name !== "string" ||
        typeof value.description !== "string" ||
        typeof value.default_paint_state !== "number" ||
        typeof value.supports_randomize !== "boolean" ||
        !Array.isArray(value.states) ||
        typeof value.rule_protocol !== "string" ||
        typeof value.supports_all_topologies !== "boolean"
    ) {
        throw new Error(`${context} returned an invalid rule definition.`);
    }
    const states = value.states.map((state) => {
        if (
            !isPlainObject(state) ||
            typeof state.value !== "number" ||
            typeof state.label !== "string" ||
            typeof state.color !== "string" ||
            typeof state.paintable !== "boolean"
        ) {
            throw new Error(`${context} returned an invalid rule state definition.`);
        }
        return {
            value: state.value,
            label: state.label,
            color: state.color,
            paintable: state.paintable,
        };
    });
    return {
        name: value.name,
        display_name: value.display_name,
        description: value.description,
        default_paint_state: value.default_paint_state,
        supports_randomize: value.supports_randomize,
        states,
        rule_protocol: value.rule_protocol,
        supports_all_topologies: value.supports_all_topologies,
        ...(typeof value.label === "string" ? { label: value.label } : {}),
    };
}

function requireTopologyPayload(value: unknown, context: string): TopologyPayload {
    if (
        !isPlainObject(value) ||
        typeof value.topology_revision !== "string" ||
        !Array.isArray(value.cells)
    ) {
        throw new Error(`${context} returned an invalid topology payload.`);
    }
    return {
        topology_revision: value.topology_revision,
        topology_spec: requireTopologySpec(value.topology_spec, context),
        cells: value.cells as TopologyPayload["cells"],
    };
}

function optionalSnapshot(value: unknown, context: string): SimulationSnapshot | undefined {
    if (value === undefined) {
        return undefined;
    }
    if (!isPlainObject(value)) {
        throw new Error(`${context} returned an invalid simulation snapshot.`);
    }
    if (
        typeof value.speed !== "number" ||
        typeof value.running !== "boolean" ||
        typeof value.generation !== "number" ||
        typeof value.topology_revision !== "string" ||
        !Array.isArray(value.cell_states)
    ) {
        throw new Error(`${context} returned an invalid simulation snapshot.`);
    }
    return {
        topology_spec: requireTopologySpec(value.topology_spec, context),
        speed: value.speed,
        running: value.running,
        generation: value.generation,
        rule: requireRuleDefinition(value.rule, context),
        topology_revision: value.topology_revision,
        topology: requireTopologyPayload(value.topology, context),
        cell_states: value.cell_states as number[],
    };
}

function optionalPersistedSnapshot(
    value: unknown,
    context: string,
): PersistedSimulationSnapshotV5 | undefined {
    if (value === undefined || value === null) {
        return undefined;
    }
    if (!isPlainObject(value)) {
        throw new Error(`${context} returned an invalid persisted snapshot.`);
    }
    if (
        value.version !== 5 ||
        typeof value.speed !== "number" ||
        typeof value.running !== "boolean" ||
        typeof value.generation !== "number" ||
        typeof value.rule !== "string" ||
        !isPlainObject(value.cells_by_id)
    ) {
        throw new Error(`${context} returned an invalid persisted snapshot.`);
    }
    return {
        version: 5,
        topology_spec: requireTopologySpec(value.topology_spec, context),
        speed: value.speed,
        running: value.running,
        generation: value.generation,
        rule: value.rule,
        cells_by_id: value.cells_by_id as Record<string, number>,
    };
}

function optionalRules(value: unknown, context: string): RulesResponse["rules"] | undefined {
    if (value === undefined) {
        return undefined;
    }
    if (!Array.isArray(value)) {
        throw new Error(`${context} returned invalid rules.`);
    }
    return value.map((entry) => requireRuleDefinition(entry, context));
}

function requireBoolean(value: unknown, context: string, fieldName: string): boolean {
    if (typeof value !== "boolean") {
        throw new Error(`${context} returned invalid ${fieldName}.`);
    }
    return value;
}

function optionalString(value: unknown): string | undefined {
    return typeof value === "string" ? value : undefined;
}

function parseInitResponse(raw: string): {
    snapshot?: SimulationSnapshot;
    persistedSnapshot: PersistedSimulationSnapshotV5 | null;
} {
    const payload = parseRuntimeJson(raw, "Standalone init");
    const result: {
        snapshot?: SimulationSnapshot;
        persistedSnapshot: PersistedSimulationSnapshotV5 | null;
    } = {
        persistedSnapshot:
            optionalPersistedSnapshot(payload.persisted_snapshot, "Standalone init") ?? null,
    };
    const snapshot = optionalSnapshot(payload.snapshot, "Standalone init");
    if (snapshot !== undefined) {
        result.snapshot = snapshot;
    }
    return result;
}

function parseRequestResponse(raw: string): {
    ok: boolean;
    error?: string;
    snapshot?: SimulationSnapshot;
    rules?: RulesResponse["rules"];
    persistedSnapshot?: PersistedSimulationSnapshotV5;
} {
    const payload = parseRuntimeJson(raw, "Standalone request");
    const result: {
        ok: boolean;
        error?: string;
        snapshot?: SimulationSnapshot;
        rules?: RulesResponse["rules"];
        persistedSnapshot?: PersistedSimulationSnapshotV5;
    } = {
        ok: requireBoolean(payload.ok, "Standalone request", "ok"),
    };
    const error = optionalString(payload.error);
    if (error !== undefined) {
        result.error = error;
    }
    const snapshot = optionalSnapshot(payload.snapshot, "Standalone request");
    if (snapshot !== undefined) {
        result.snapshot = snapshot;
    }
    const rules = optionalRules(payload.rules, "Standalone request");
    if (rules !== undefined) {
        result.rules = rules;
    }
    const persistedSnapshot = optionalPersistedSnapshot(
        payload.persisted_snapshot,
        "Standalone request",
    );
    if (persistedSnapshot !== undefined) {
        result.persistedSnapshot = persistedSnapshot;
    }
    return result;
}

function parseTickResponse(raw: string): {
    ok: boolean;
    stepped: boolean;
    error?: string;
    snapshot?: SimulationSnapshot;
    persistedSnapshot?: PersistedSimulationSnapshotV5;
} {
    const payload = parseRuntimeJson(raw, "Standalone tick");
    const result: {
        ok: boolean;
        stepped: boolean;
        error?: string;
        snapshot?: SimulationSnapshot;
        persistedSnapshot?: PersistedSimulationSnapshotV5;
    } = {
        ok: requireBoolean(payload.ok, "Standalone tick", "ok"),
        stepped: payload.stepped === true,
    };
    const error = optionalString(payload.error);
    if (error !== undefined) {
        result.error = error;
    }
    const snapshot = optionalSnapshot(payload.snapshot, "Standalone tick");
    if (snapshot !== undefined) {
        result.snapshot = snapshot;
    }
    const persistedSnapshot = optionalPersistedSnapshot(
        payload.persisted_snapshot,
        "Standalone tick",
    );
    if (persistedSnapshot !== undefined) {
        result.persistedSnapshot = persistedSnapshot;
    }
    return result;
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
        const payload = parseInitResponse(raw);
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
        const payload = parseRequestResponse(raw);
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
            ...(payload.snapshot === undefined ? {} : { snapshot: payload.snapshot }),
            ...(payload.rules === undefined ? {} : { rules: payload.rules }),
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
        const payload = parseTickResponse(raw);
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
