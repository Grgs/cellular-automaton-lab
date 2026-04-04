import type { EditorTool } from "../editor-tools.js";
import type { ConfigSyncBody } from "./controller-api.js";
import type { SimulationSnapshot } from "./domain.js";
import type { MatchMediaResult, UiDisclosureId, UiSessionStorage } from "./session.js";

export interface ConfigSyncViewState {
    pendingRuleName: string | null;
    syncingRuleName: string | null;
    pendingSpeed: number | null;
    syncingSpeed: number | null;
    isSyncing: boolean;
    hasPendingRuleSync: boolean;
    hasPendingSpeedSync: boolean;
    shouldLockRule: boolean;
    shouldLockSpeed: boolean;
}

export interface ConfigSyncController {
    reconcile(simulationState: SimulationSnapshot): void;
    shouldAdoptBackendRule(): boolean;
    getViewState(): ConfigSyncViewState;
    requestRuleSync(nextRuleName: string | null, options?: RuleSyncRequestOptions): void;
    scheduleSpeedSync(nextSpeed: number): void;
    getDisplaySpeed(fallbackSpeed: number): number;
    dispose(): void;
}

export interface UiSessionController {
    getStorage(): UiSessionStorage;
    restoreInitialCellSize(): void;
    restoreDisclosures(): void;
    restoreDrawerState(): void;
    restorePaintStateForCurrentRule(): void;
    persistCellSize(tilingFamilyOrCellSize: string | number, cellSize?: number): void;
    persistUnsafeSizingEnabled(enabled: boolean): void;
    persistEditorTool(editorTool: EditorTool): void;
    persistBrushSize(brushSize: number): void;
    persistPaintStateForCurrentRule(): void;
    persistPatchDepthForTilingFamily(tilingFamily: string | null | undefined, patchDepth: number): void;
    persistDisclosureState(id: UiDisclosureId, open: boolean): void;
    persistDrawerState(drawerOpen: boolean): void;
    resetSessionPreferences(): void;
}

export interface RuleSyncRequestOptions {
    running?: boolean;
    body?: ConfigSyncBody;
}

export interface MatchMediaFunction {
    (query: string): MatchMediaResult;
}

export interface CreateUiSessionStorageFunction {
    (options?: { storage?: Storage; storageKey?: string }): UiSessionStorage;
}
