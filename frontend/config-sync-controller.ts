import { createConfigSyncMutationRuntime } from "./config-sync/runtime.js";
import { createConfigRuleSyncRequester } from "./config-sync/rule-sync.js";
import { createConfigSpeedSyncScheduler } from "./config-sync/speed-sync.js";
import { createConfigSyncStateManager } from "./config-sync/state.js";
import type {
    BrowserClearTimeout,
    BrowserSetTimeout,
    ConfigSyncController,
    ConfigSyncViewState,
    MutationRunner,
    PostControlFunction,
    SimulationMutations,
} from "./types/controller.js";
import type { SimulationSnapshot } from "./types/domain.js";
import type { AppState } from "./types/state.js";

export function createConfigSyncController({
    state: _state,
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
    applySimulationState: (
        simulationState: SimulationSnapshot,
        options?: { source?: string },
    ) => void;
    refreshState: () => Promise<void>;
    setTimeoutFn?: BrowserSetTimeout;
    clearTimeoutFn?: BrowserClearTimeout;
    speedDebounceMs?: number;
}): ConfigSyncController {
    const stateManager = createConfigSyncStateManager(onSyncStateChanged);
    const runtime = createConfigSyncMutationRuntime({
        mutationRunner,
        simulationMutations,
        onError,
        applySimulationState,
        refreshState,
    });
    const speedSync = createConfigSpeedSyncScheduler({
        stateManager,
        runtime,
        postControl,
        setTimeoutFn,
        clearTimeoutFn,
        speedDebounceMs,
    });
    const ruleSync = createConfigRuleSyncRequester({
        stateManager,
        runtime,
        postControl,
    });

    return {
        dispose() {
            speedSync.dispose();
        },
        getDisplaySpeed(fallbackSpeed: number) {
            return stateManager.getDisplaySpeed(fallbackSpeed);
        },
        getViewState(): ConfigSyncViewState {
            return stateManager.getViewState();
        },
        reconcile(simulationState: SimulationSnapshot) {
            stateManager.reconcile(simulationState, {
                clearScheduledSpeedSync: speedSync.clearScheduledSpeedSync,
            });
        },
        requestRuleSync(nextRuleName, options) {
            ruleSync.requestRuleSync(nextRuleName, options);
        },
        scheduleSpeedSync(nextSpeed) {
            speedSync.scheduleSpeedSync(nextSpeed);
        },
        shouldAdoptBackendRule() {
            return stateManager.shouldAdoptBackendRule();
        },
    };
}
