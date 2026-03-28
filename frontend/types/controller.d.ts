import type {
    CellIdentifier,
    CellStateDefinition,
    RulesResponse,
    SimulationSnapshot,
    TopologySpec,
} from "./domain.js";
import type { AppState, TopologyRenderPayload } from "./state.js";
import type { DomElements } from "./dom.js";
import type { MatchMediaResult, UiDisclosureId, UiSessionStorage } from "./session.js";
import type { AppActionSet } from "./actions.js";

export type BrowserTimerId = number;
export type BrowserSetTimeout = (callback: () => void, delay: number) => BrowserTimerId;
export type BrowserClearTimeout = (timerId: BrowserTimerId) => void;

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
    persistEditorTool(editorTool: string): void;
    persistBrushSize(brushSize: number): void;
    persistPaintStateForCurrentRule(): void;
    persistPatchDepthForTilingFamily(tilingFamily: string | null | undefined, patchDepth: number): void;
    persistDisclosureState(id: UiDisclosureId, open: boolean): void;
    persistDrawerState(drawerOpen: boolean): void;
    resetSessionPreferences(): void;
}

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

export interface MutationRunnerOptions {
    onError?: (error: unknown) => void;
    onRecover?: (error: unknown) => Promise<void> | void;
}

export interface MutationRunner {
    run<T>(task: () => Promise<T>, options?: MutationRunnerOptions): Promise<T>;
    dispose(): void;
}

export interface BlockingActivityConfig {
    kind?: string | null;
    message?: string;
    detail?: string;
    delayMs?: number;
    escalateAfterMs?: number;
}

export interface SimulationMutationOptions extends MutationRunnerOptions {
    source?: string;
    recoverWithRefresh?: boolean;
    blockingActivity?: BlockingActivityConfig | null;
}

export interface ConfigTopologySpecPatch {
    width?: number;
    height?: number;
}

export interface ConfigSyncBody {
    topology_spec?: ConfigTopologySpecPatch;
    speed?: number;
    rule?: string | null;
}

export interface ResetControlBody {
    topology_spec: TopologySpec;
    speed: number;
    rule: string | null;
    randomize: boolean;
}

export interface ControlCommandMap {
    "/api/control/start": undefined;
    "/api/control/pause": undefined;
    "/api/control/resume": undefined;
    "/api/control/step": undefined;
    "/api/control/reset": ResetControlBody;
    "/api/config": ConfigSyncBody;
}

export type EmptyControlCommandPath = {
    [TPath in keyof ControlCommandMap]: ControlCommandMap[TPath] extends undefined ? TPath : never;
}[keyof ControlCommandMap];

export interface RuleSyncRequestOptions {
    running?: boolean;
    body?: ConfigSyncBody;
}

export interface ViewportSyncOptions {
    includeConfig?: boolean;
    force?: boolean;
    preview?: boolean;
    previewApplied?: boolean;
    delay?: number;
    body?: ConfigSyncBody;
    desiredDimensions?: ViewportDimensions;
    blockingActivity?: BlockingActivityConfig | null;
}

export interface CreateSimulationMutationsOptions {
    state?: AppState | null;
    mutationRunner: MutationRunner;
    onError?: (error: unknown) => void;
    applySimulationState?: (simulationState: SimulationSnapshot, options?: { source?: string }) => void;
    resolveSimulationState?: (simulationState: SimulationSnapshot) => Promise<SimulationSnapshot>;
    refreshState?: () => Promise<void>;
    renderControlPanel?: () => void;
    setTimeoutFn?: BrowserSetTimeout;
    clearTimeoutFn?: BrowserClearTimeout;
}

export interface SimulationMutations {
    applyState(simulationState: SimulationSnapshot, options?: { source?: string }): SimulationSnapshot;
    applyRemoteState(
        simulationState: SimulationSnapshot,
        options?: { source?: string },
    ): Promise<SimulationSnapshot>;
    runSerialized<T>(task: () => Promise<T>, options?: SimulationMutationOptions): Promise<T>;
    runStateMutation<T>(
        task: () => Promise<SimulationSnapshot>,
        options?: SimulationMutationOptions,
    ): Promise<SimulationSnapshot>;
}

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

export interface ViewportDimensions {
    width: number;
    height: number;
}

export interface AppView {
    renderAll(): void;
    renderGrid(): void;
    renderControlsPanel(): void;
    viewportDimensionsFor(geometry?: string, ruleName?: string | null, cellSizeOverride?: number): ViewportDimensions;
    applyViewportPreview(dimensions: ViewportDimensions): void;
}

export interface InteractionController {
    bindGridInteractions(): void;
    toggleCell?(cell: CellIdentifier): Promise<unknown>;
    sendControl(path: EmptyControlCommandPath, options?: SimulationMutationOptions): Promise<SimulationSnapshot | null>;
    sendControl(
        path: "/api/control/reset",
        body: ResetControlBody,
        options?: SimulationMutationOptions,
    ): Promise<SimulationSnapshot | null>;
    sendControl(
        path: "/api/config",
        body: ConfigSyncBody,
        options?: SimulationMutationOptions,
    ): Promise<SimulationSnapshot | null>;
    runSerialized<T>(task: () => Promise<T>, options?: MutationRunnerOptions): Promise<T>;
    undo?(): Promise<unknown>;
    redo?(): Promise<unknown>;
    cancelActivePreview?(): Promise<unknown>;
}

export interface ViewportController {
    sync(options?: ViewportSyncOptions): Promise<boolean>;
    schedule(options?: ViewportSyncOptions): boolean;
    flush(options?: ViewportSyncOptions): Promise<boolean>;
    suppressAutoSync(durationMs?: number): void;
    install(viewportElement: HTMLElement | null): void;
    dispose(): void;
}

export interface GridView {
    render?(
        payload: TopologyRenderPayload,
        cellSize: number,
        stateDefinitions: CellStateDefinition[],
        geometry: string,
    ): void;
    getCellFromPointerEvent?(event: Event): CellIdentifier | null;
    setPreviewCells(cells: unknown): void;
    clearPreview(): void;
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
    refreshState(): Promise<void>;
    loadRules(): Promise<void>;
    applySimulationState(simulationState: SimulationSnapshot, options?: { source?: string }): void;
    applyCellSize(nextCellSize: number): void;
    applyPaintState(nextPaintState: number): void;
    getState(): AppState;
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

export interface MatchMediaFunction {
    (query: string): MatchMediaResult;
}

export interface CreateUiSessionStorageFunction {
    (options?: { storage?: Storage; storageKey?: string }): UiSessionStorage;
}

export interface FetchRulesFunction {
    (): Promise<RulesResponse>;
}

export interface FetchStateFunction {
    (): Promise<SimulationSnapshot>;
}

export interface PostControlFunction {
    (path: EmptyControlCommandPath): Promise<SimulationSnapshot>;
    (path: "/api/control/reset", body: ResetControlBody): Promise<SimulationSnapshot>;
    (path: "/api/config", body: ConfigSyncBody): Promise<SimulationSnapshot>;
}

export interface CellMutationRequestFunction {
    (cell: { id: string }, state?: number): Promise<SimulationSnapshot>;
}

export interface ToggleCellRequestFunction {
    (cell: CellIdentifier): Promise<SimulationSnapshot>;
}

export interface SetCellRequestFunction {
    (cell: CellIdentifier, state: number): Promise<SimulationSnapshot>;
}

export interface SetCellsRequestFunction {
    (cells: Array<{ id: string; state: number }>): Promise<SimulationSnapshot>;
}

export interface ViewportControllerDependencies {
    getCurrentDimensions(): ViewportDimensions;
    getViewportDimensions(geometry?: string, ruleName?: string | null, cellSize?: number): ViewportDimensions;
    collectConfig(): { speed: number; rule: string };
    applyPreview(dimensions: ViewportDimensions): void;
    sendControl(
        path: "/api/config",
        body: ConfigSyncBody,
        options?: SimulationMutationOptions,
    ): Promise<SimulationSnapshot | null>;
    sameDimensions(left: ViewportDimensions, right: ViewportDimensions | null | undefined): boolean;
}

export interface CreateSimulationMutationsFunction {
    (options: CreateSimulationMutationsOptions): SimulationMutations;
}

export interface CreateAppControllerOptions {
    elements: DomElements;
    gridView: GridView;
    onError?: (error: unknown) => void;
}
