import type {
    BrowserClearTimeout,
    BrowserSetTimeout,
    BrowserTimerId,
    PostControlFunction,
} from "../types/controller.js";
import type { ConfigSyncStateManager } from "./state.js";
import type { ConfigSyncMutationRuntime } from "./runtime.js";

export interface ConfigSpeedSyncScheduler {
    scheduleSpeedSync(nextSpeed: number): void;
    clearScheduledSpeedSync(): void;
    dispose(): void;
}

export function createConfigSpeedSyncScheduler({
    stateManager,
    runtime,
    postControl,
    setTimeoutFn = (callback, delay) => window.setTimeout(callback, delay),
    clearTimeoutFn = (timerId) => window.clearTimeout(timerId),
    speedDebounceMs = 200,
}: {
    stateManager: ConfigSyncStateManager;
    runtime: ConfigSyncMutationRuntime;
    postControl: PostControlFunction;
    setTimeoutFn?: BrowserSetTimeout;
    clearTimeoutFn?: BrowserClearTimeout;
    speedDebounceMs?: number;
}): ConfigSpeedSyncScheduler {
    let speedSyncTimer: BrowserTimerId | null = null;

    function clearScheduledSpeedSync(): void {
        if (speedSyncTimer !== null) {
            clearTimeoutFn(speedSyncTimer);
            speedSyncTimer = null;
        }
    }

    async function syncSpeedValue(nextSpeed: number): Promise<void> {
        stateManager.beginSpeedSync(nextSpeed);
        await runtime.runConfigMutation(
            () => postControl("/api/config", { speed: Number(nextSpeed) }),
            {
                onFailure: () => {
                    stateManager.clearSpeedSync({ clearScheduledSpeedSync });
                },
            },
        );
    }

    function scheduleSpeedSync(nextSpeed: number): void {
        stateManager.markPendingSpeed(nextSpeed);
        clearScheduledSpeedSync();
        speedSyncTimer = setTimeoutFn(() => {
            speedSyncTimer = null;
            const pendingSpeed = stateManager.pendingSpeed();
            if (pendingSpeed === null) {
                return;
            }
            void syncSpeedValue(pendingSpeed);
        }, speedDebounceMs);
    }

    return {
        scheduleSpeedSync,
        clearScheduledSpeedSync,
        dispose: clearScheduledSpeedSync,
    };
}
