import type { ConfigSyncViewState } from "../types/controller.js";
import type { SimulationSnapshot } from "../types/domain.js";

interface SyncStateData {
    pendingRuleName: string | null;
    syncingRuleName: string | null;
    pendingSpeed: number | null;
    syncingSpeed: number | null;
}

export interface ConfigSyncStateManager {
    getViewState(): ConfigSyncViewState;
    shouldAdoptBackendRule(): boolean;
    getDisplaySpeed(fallbackSpeed: number): number;
    reconcile(simulationState: SimulationSnapshot, options?: { clearScheduledSpeedSync?: () => void }): void;
    markPendingRule(nextRuleName: string | null): void;
    beginRuleSync(nextRuleName: string | null): void;
    clearRuleSync(): void;
    markPendingSpeed(nextSpeed: number): void;
    beginSpeedSync(nextSpeed: number): void;
    clearSpeedSync(options?: { clearScheduledSpeedSync?: () => void }): void;
    pendingSpeed(): number | null;
}

export function createConfigSyncStateManager(
    onSyncStateChanged: (viewState: ConfigSyncViewState) => void = () => {},
): ConfigSyncStateManager {
    const syncState: SyncStateData = {
        pendingRuleName: null,
        syncingRuleName: null,
        pendingSpeed: null,
        syncingSpeed: null,
    };

    function hasPendingRuleSync(): boolean {
        return syncState.pendingRuleName !== null || syncState.syncingRuleName !== null;
    }

    function hasPendingSpeedSync(): boolean {
        return syncState.pendingSpeed !== null || syncState.syncingSpeed !== null;
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

    function notify(): void {
        onSyncStateChanged(getViewState());
    }

    function reconcile(
        simulationState: SimulationSnapshot,
        { clearScheduledSpeedSync }: { clearScheduledSpeedSync?: () => void } = {},
    ): void {
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
            clearScheduledSpeedSync?.();
            changed = true;
        }

        if (changed) {
            notify();
        }
    }

    function shouldAdoptBackendRule(): boolean {
        return !hasPendingRuleSync();
    }

    function getDisplaySpeed(fallbackSpeed: number): number {
        return syncState.pendingSpeed ?? syncState.syncingSpeed ?? Number(fallbackSpeed);
    }

    function markPendingRule(nextRuleName: string | null): void {
        syncState.pendingRuleName = nextRuleName || null;
        notify();
    }

    function beginRuleSync(nextRuleName: string | null): void {
        syncState.pendingRuleName = null;
        syncState.syncingRuleName = nextRuleName || null;
        notify();
    }

    function clearRuleSync(): void {
        syncState.pendingRuleName = null;
        syncState.syncingRuleName = null;
        notify();
    }

    function markPendingSpeed(nextSpeed: number): void {
        syncState.pendingSpeed = Number(nextSpeed);
        notify();
    }

    function beginSpeedSync(nextSpeed: number): void {
        syncState.syncingSpeed = Number(nextSpeed);
        if (syncState.pendingSpeed === Number(nextSpeed)) {
            syncState.pendingSpeed = null;
        }
        notify();
    }

    function clearSpeedSync({ clearScheduledSpeedSync }: { clearScheduledSpeedSync?: () => void } = {}): void {
        syncState.pendingSpeed = null;
        syncState.syncingSpeed = null;
        clearScheduledSpeedSync?.();
        notify();
    }

    return {
        getViewState,
        shouldAdoptBackendRule,
        getDisplaySpeed,
        reconcile,
        markPendingRule,
        beginRuleSync,
        clearRuleSync,
        markPendingSpeed,
        beginSpeedSync,
        clearSpeedSync,
        pendingSpeed: () => syncState.pendingSpeed,
    };
}
