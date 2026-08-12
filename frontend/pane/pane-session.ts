import type { SimulationBackend } from "../types/controller-api.js";
import type { PatternPayload, SimulationSnapshot } from "../types/domain.js";

const POLL_INTERVAL_MS = 250;

export interface PaneSession {
    getSnapshot(): SimulationSnapshot | null;
    ensureSnapshot(): Promise<SimulationSnapshot>;
    applySnapshot(snapshot: SimulationSnapshot): void;
    refresh(): Promise<void>;
    writeCells(updates: { id: string; state: number }[]): Promise<void>;
    seedFromPattern(pattern: PatternPayload, speed: number, afterReset?: () => void): Promise<void>;
    step(): Promise<void>;
    runToggle(): Promise<void>;
    registerCleanup(cleanup: () => void): void;
    dispose(): void;
}

interface PaneSessionOptions {
    backend: SimulationBackend;
    onSnapshot: (snapshot: SimulationSnapshot) => void;
    onError: (error: unknown) => void;
}

/**
 * Owns the pane's remote state and synchronization lifecycle. UI helpers never
 * install snapshots directly: every read, write, control response, and poll is
 * reconciled through this object.
 */
export function createPaneSession(options: PaneSessionOptions): PaneSession {
    const { backend, onSnapshot, onError } = options;
    let snapshot: SimulationSnapshot | null = null;
    let pollTimer: number | null = null;
    let disposed = false;
    const cleanups = new Set<() => void>();

    function clearPoll(): void {
        if (pollTimer !== null) {
            window.clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    function syncPoll(): void {
        if (disposed || !snapshot?.running) {
            clearPoll();
            return;
        }
        if (pollTimer !== null) {
            return;
        }
        pollTimer = window.setInterval(() => {
            void refresh();
        }, POLL_INTERVAL_MS);
    }

    function applySnapshot(next: SimulationSnapshot): void {
        if (disposed) {
            return;
        }
        snapshot = next;
        onSnapshot(next);
        syncPoll();
    }

    async function ensureSnapshot(): Promise<SimulationSnapshot> {
        if (snapshot) {
            return snapshot;
        }
        const next = await backend.getState();
        applySnapshot(next);
        return next;
    }

    async function refresh(): Promise<void> {
        try {
            applySnapshot(await backend.getState());
        } catch (error) {
            onError(error);
        }
    }

    async function writeCells(updates: { id: string; state: number }[]): Promise<void> {
        const current = await ensureSnapshot();
        const wasRunning = current.running;
        if (wasRunning) {
            applySnapshot(await backend.postControl("/api/control/pause"));
        }
        applySnapshot(await backend.setCells(updates));
        if (wasRunning) {
            applySnapshot(await backend.postControl("/api/control/resume"));
        }
    }

    return {
        getSnapshot: () => snapshot,
        ensureSnapshot,
        applySnapshot,
        refresh,
        writeCells,
        async seedFromPattern(pattern, speed, afterReset): Promise<void> {
            const reset = await backend.postControl("/api/control/reset", {
                topology_spec: pattern.topology_spec,
                speed,
                rule: pattern.rule,
                randomize: false,
            });
            afterReset?.();
            const updates = Object.entries(pattern.cells_by_id).map(([id, state]) => ({
                id,
                state: Number(state),
            }));
            applySnapshot(updates.length > 0 ? await backend.setCells(updates) : reset);
        },
        async step(): Promise<void> {
            applySnapshot(await backend.postControl("/api/control/step"));
        },
        async runToggle(): Promise<void> {
            const current = await ensureSnapshot();
            if (current.running) {
                applySnapshot(await backend.postControl("/api/control/pause"));
                return;
            }
            const path = current.generation > 0 ? "/api/control/resume" : "/api/control/start";
            applySnapshot(await backend.postControl(path));
        },
        registerCleanup(cleanup): void {
            if (disposed) {
                cleanup();
                return;
            }
            cleanups.add(cleanup);
        },
        dispose(): void {
            if (disposed) {
                return;
            }
            disposed = true;
            clearPoll();
            cleanups.forEach((cleanup) => cleanup());
            cleanups.clear();
        },
    };
}
