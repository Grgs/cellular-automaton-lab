import type { AppActionSet } from "./actions.js";
import type {
    FetchRulesFunction,
    FetchStateFunction,
    InitAppOptions,
    SimulationBackend,
} from "./controller-api.js";
import type { MutationRunner } from "./controller-runtime.js";
import type { ConfigSyncController, UiSessionController } from "./controller-sync-session.js";
import type { AppView, GridView, InteractionController, ViewportController } from "./controller-view.js";
import type { DomElements } from "./dom.js";
import type { SimulationSnapshot, TopologyPayload } from "./domain.js";
import type { RenderDiagnosticsSnapshot } from "./rendering.js";
import type { AppState } from "./state.js";

export interface SimulationReconcilerDependencies {
    state: AppState;
    getConfigSyncController?: () => ConfigSyncController | null;
    getUiSessionController?: () => UiSessionController | null;
    getRefreshState?: () => (() => Promise<void>);
    applySimulationSnapshot: (state: AppState, simulationState: SimulationSnapshot) => void;
    shouldClearHistoryForSimulationUpdate: (
        state: AppState,
        simulationState: SimulationSnapshot,
        source: string,
    ) => boolean;
    clearEditorHistory: (state: AppState) => void;
    setEditorRule: (
        state: AppState,
        ruleName: string | null,
        options?: { resetPaintState?: boolean },
    ) => void;
    syncPolling: (state: AppState, isRunning: boolean, refreshState: () => Promise<void>) => void;
    renderAll: () => void;
    clearEditModeFn?: (state: AppState) => boolean;
}

export interface AppControllerSync {
    applySimulationState(simulationState: SimulationSnapshot, options?: { source?: string }): void;
    resolveSimulationState(simulationState: SimulationSnapshot): Promise<SimulationSnapshot>;
    refreshState(): Promise<void>;
    loadRules(): Promise<void>;
    getSimulationReconciler(): { apply(simulationState: SimulationSnapshot, options?: { source?: string }): void };
}

export interface AppControllerStartupResult {
    interactions: InteractionController;
    viewportController: ViewportController;
    configSyncController: ConfigSyncController;
    uiSessionController: UiSessionController;
    controlActions: AppActionSet;
}

export interface AppController {
    init(): Promise<void>;
    dispose(): void;
    refreshState(): Promise<void>;
    loadRules(): Promise<void>;
    applySimulationState(simulationState: SimulationSnapshot, options?: { source?: string }): void;
    applyCellSize(nextCellSize: number): void;
    applyPaintState(nextPaintState: number): void;
    applyReviewTopology(topology: TopologyPayload): void;
    getState(): AppState;
    getRenderDiagnostics(): RenderDiagnosticsSnapshot | null;
    getInteractions(): InteractionController | null;
    getViewportController(): ViewportController | null;
    getConfigSyncController(): ConfigSyncController | null;
    getUiSessionController(): UiSessionController | null;
}

export interface AppControllerBootstrapResult {
    state: AppState;
    mutationRunner: MutationRunner;
    appView: AppView;
}

export interface CreateAppControllerOptions {
    elements: DomElements;
    gridView: GridView;
    backend?: SimulationBackend;
    onError?: (error: unknown) => void;
}

export type { FetchRulesFunction, FetchStateFunction, InitAppOptions };
