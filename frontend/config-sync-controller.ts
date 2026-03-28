import { createSimulationMutations } from "./interactions/simulation-mutations.js";
import type {
    BrowserClearTimeout,
    BrowserSetTimeout,
    BrowserTimerId,
    ConfigSyncBody,
    ConfigSyncController,
    ConfigSyncViewState,
    CreateSimulationMutationsOptions,
    MutationRunner,
    PostControlFunction,
    RuleSyncRequestOptions,
    SimulationMutations,
} from "./types/controller.js";
import type { SimulationSnapshot } from "./types/domain.js";
import type { AppState } from "./types/state.js";

interface ConfigSyncState {
    pendingRuleName: string | null;
    syncingRuleName: string | null;
    pendingSpeed: number | null;
    syncingSpeed: number | null;
}

export function createConfigSyncController({
    state,
    mutationRunner,
    simulationMutations = null,
    postControl,
    onError,
    onSyncStateChanged = () => {},
    applySimulationState,
    refreshState,
    setTimeoutFn = (callback, delay) => window.setTimeout(callback, delay),
    clearTimeoutFn = (timerId) => window.clearTimeout(timerId),
    speedDebounceMs = 200,
}: {
    state: AppState;
    mutationRunner: MutationRunner;
    simulationMutations?: SimulationMutations | null;
    postControl: PostControlFunction;
    onError: (error: unknown) => void;
    onSyncStateChanged?: (viewState: ConfigSyncViewState) => void;
    applySimulationState: (simulationState: SimulationSnapshot, options?: { source?: string }) => void;
    refreshState: () => Promise<void>;
    setTimeoutFn?: BrowserSetTimeout;
    clearTimeoutFn?: BrowserClearTimeout;
    speedDebounceMs?: number;
}): ConfigSyncController {
    const mutations = simulationMutations || createSimulationMutations({
        mutationRunner,
        onError,
        applySimulationState,
        refreshState,
    } satisfies CreateSimulationMutationsOptions);
    const syncState: ConfigSyncState = {
        pendingRuleName: null,
        syncingRuleName: null,
        pendingSpeed: null,
        syncingSpeed: null,
    };
    let speedSyncTimer: BrowserTimerId | null = null;

    function hasPendingRuleSync(): boolean {
        return syncState.pendingRuleName !== null || syncState.syncingRuleName !== null;
    }

    function hasPendingSpeedSync(): boolean {
        return syncState.pendingSpeed !== null || syncState.syncingSpeed !== null;
    }

    function notify(): void {
        onSyncStateChanged(getViewState());
    }

    function clearScheduledSpeedSync(): void {
        if (speedSyncTimer !== null) {
            clearTimeoutFn(speedSyncTimer);
            speedSyncTimer = null;
        }
    }

    function clearRuleSync(): void {
        syncState.pendingRuleName = null;
        syncState.syncingRuleName = null;
    }

    function clearSpeedSync(): void {
        syncState.pendingSpeed = null;
        syncState.syncingSpeed = null;
        clearScheduledSpeedSync();
    }

    function getViewState(): ConfigSyncViewState {
        return {
            pendingRuleName: syncState.pendingRuleName,
            syncingRuleName: syncState.syncingRuleName,
            pendingSpeed: syncState.pendingSpeed,
            syncingSpeed: syncState.syncingSpeed,
            isSyncing: syncState.syncingRuleName !== null || syncState.syncingSpeed !== null,
            hasPendingRuleSync: hasPendingRuleSync(),
            hasPendingSpeedSync: hasPendingSpeedSync(),
            shouldLockRule: false,
            shouldLockSpeed: false,
        };
    }

    function shouldAdoptBackendRule(): boolean {
        return !hasPendingRuleSync();
    }

    function getDisplaySpeed(fallbackSpeed: number): number {
        return syncState.pendingSpeed ?? syncState.syncingSpeed ?? Number(fallbackSpeed);
    }

    function reconcile(simulationState: SimulationSnapshot): void {
        let changed = false;
        const nextRuleName = simulationState.rule?.name ?? null;
        const nextSpeed = Number(simulationState.speed);

        if (syncState.syncingRuleName && nextRuleName === syncState.syncingRuleName) {
            syncState.syncingRuleName = null;
            changed = true;
        }
        if (syncState.pendingRuleName && nextRuleName === syncState.pendingRuleName) {
            syncState.pendingRuleName = null;
            changed = true;
        }

        if (syncState.syncingSpeed !== null && nextSpeed === Number(syncState.syncingSpeed)) {
            syncState.syncingSpeed = null;
            changed = true;
        }
        if (syncState.pendingSpeed !== null && nextSpeed === Number(syncState.pendingSpeed)) {
            syncState.pendingSpeed = null;
            clearScheduledSpeedSync();
            changed = true;
        }

        if (changed) {
            notify();
        }
    }

    function normalizeConfigBody(body: ConfigSyncBody | null = null): ConfigSyncBody {
        if (!body) {
            return {};
        }
        const nextBody: ConfigSyncBody = { ...body };
        if (body.topology_spec && Object.keys(body.topology_spec).length > 0) {
            nextBody.topology_spec = { ...body.topology_spec };
        }
        return nextBody;
    }

    async function runConfigMutation(
        task: () => Promise<SimulationSnapshot>,
        { onFailure }: { onFailure?: () => void } = {},
    ): Promise<void> {
        try {
            await mutations.runSerialized(
                async () => mutations.applyRemoteState(await task()),
                {
                    onRecover: async () => {
                        if (typeof onFailure === "function") {
                            onFailure();
                        }
                        await refreshState();
                    },
                },
            );
        } catch {
            // The shared mutation runner already reported and recovered.
        }
    }

    async function syncSpeedValue(nextSpeed: number): Promise<void> {
        syncState.syncingSpeed = Number(nextSpeed);
        if (syncState.pendingSpeed === Number(nextSpeed)) {
            syncState.pendingSpeed = null;
        }
        notify();

        await runConfigMutation(
            () => postControl("/api/config", { speed: Number(nextSpeed) }),
            {
                onFailure: () => {
                    clearSpeedSync();
                    notify();
                },
            },
        );
    }

    function scheduleSpeedSync(nextSpeed: number): void {
        syncState.pendingSpeed = Number(nextSpeed);
        clearScheduledSpeedSync();
        notify();

        speedSyncTimer = setTimeoutFn(() => {
            speedSyncTimer = null;
            if (syncState.pendingSpeed === null) {
                return;
            }
            void syncSpeedValue(nextSpeed);
        }, speedDebounceMs);
    }

    async function syncRuleChange(
        nextRuleName: string | null,
        { running = false, body = undefined }: RuleSyncRequestOptions = {},
    ): Promise<void> {
        syncState.pendingRuleName = null;
        syncState.syncingRuleName = nextRuleName || null;
        notify();

        await runConfigMutation(
            async () => {
                if (running) {
                    const pausedState = await postControl("/api/control/pause");
                    await mutations.applyRemoteState(pausedState);
                }
                return postControl("/api/config", {
                    rule: nextRuleName,
                    ...normalizeConfigBody(body),
                });
            },
            {
                onFailure: () => {
                    clearRuleSync();
                    notify();
                },
            },
        );
    }

    function requestRuleSync(nextRuleName: string | null, options: RuleSyncRequestOptions = {}): void {
        syncState.pendingRuleName = nextRuleName || null;
        notify();
        void syncRuleChange(nextRuleName, options);
    }

    function dispose(): void {
        clearScheduledSpeedSync();
    }

    return {
        dispose,
        getDisplaySpeed,
        getViewState,
        reconcile,
        requestRuleSync,
        scheduleSpeedSync,
        shouldAdoptBackendRule,
    };
}
