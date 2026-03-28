import type {
    BlockingActivityConfig,
    ConfigSyncBody,
    ConfigSyncController,
    InteractionController,
    PostControlFunction,
    ResetControlBody,
    SetCellsRequestFunction,
    SimulationMutations,
    SimulationMutationOptions,
    UiSessionController,
    ViewportController,
    ViewportDimensions,
} from "./controller.js";
import type {
    CellStateUpdate,
    ParsedPattern,
    PatternPayload,
    PresetMetadata,
    ResolvedPresetSelection,
    SimulationSnapshot,
    TopologySpec,
} from "./domain.js";
import type { DomElements } from "./dom.js";
import type { UiDisclosureId } from "./session.js";
import type { AppState } from "./state.js";

export interface SimulationActionRuntime {
    state: AppState;
    interactions: InteractionController;
    viewportController: ViewportController;
    configSyncController: ConfigSyncController;
    uiSessionController: UiSessionController;
    renderControlPanel: () => void;
    getViewportDimensions: (
        geometry: string,
        ruleName: string | null,
        cellSize: number,
    ) => ViewportDimensions;
    dismissHintsAndStatus(): void;
    applyOverlayIntentAndRender(intent: string): boolean;
    buildResetPayload(randomize: boolean): ResetControlBody;
    applyRuleSelection(nextRuleName: string | null): void;
    applySpeedSelection(nextSpeed: number): void;
    requestPatchDepth(
        nextPatchDepth: number,
        options?: { immediate?: boolean },
    ): Promise<boolean>;
    changeTilingFamily(nextTilingFamily: string): Promise<SimulationSnapshot | null | void>;
    changeAdjacencyMode(nextAdjacencyMode: string): Promise<SimulationSnapshot | null | void>;
    resetRuleSelectionOrigin(): void;
}

export interface SimulationActionSet {
    toggleRun(): Promise<SimulationSnapshot | null>;
    step(): Promise<SimulationSnapshot | null>;
    reset(): Promise<SimulationSnapshot | null>;
    randomReset(): Promise<SimulationSnapshot | null>;
    changeSpeed(nextSpeed: number): void;
    changeRule(nextRuleName: string | null): void;
    changeTilingFamily(nextTilingFamily: string): Promise<SimulationSnapshot | null | void>;
    changeAdjacencyMode(nextAdjacencyMode: string): Promise<SimulationSnapshot | null | void>;
    changePatchDepth(nextPatchDepth: number): Promise<boolean>;
    commitPatchDepth(nextPatchDepth: number): Promise<boolean>;
}

export interface ActionMutationAdapter {
    applyState(
        simulationState: SimulationSnapshot,
        options?: { source?: string },
    ): SimulationSnapshot;
    applyRemoteState(
        simulationState: SimulationSnapshot,
        options?: { source?: string },
    ): Promise<SimulationSnapshot>;
    runSerialized<T>(task: () => Promise<T>, options?: SimulationMutationOptions): Promise<T>;
}

export interface PatternActionSet {
    openPatternImport(): void;
    importPatternFile(file: File | null | undefined): Promise<SimulationSnapshot | null>;
    exportPattern(): Promise<PatternPayload | null>;
    copyPattern(): Promise<PatternPayload | null>;
    pastePattern(): Promise<SimulationSnapshot | null>;
}

export interface PresetActionSet {
    loadPresetSeed(presetId: string | null | undefined): Promise<SimulationSnapshot | null | void>;
    changePresetSeedSelection(presetId: string | null | undefined): void;
}

export interface ShowcaseActionSet {
    loadShowcaseDemo(demoId: string): Promise<SimulationSnapshot | null>;
}

export interface UiActionSet {
    setCellSize(nextCellSize: number): Promise<unknown>;
    commitCellSize(nextCellSize: number): Promise<unknown>;
    setPaintState(nextPaintState: number | null): void;
    setEditorTool(nextTool: string): void;
    setBrushSize(nextBrushSize: number): void;
    toggleDrawer(): Promise<boolean>;
    closeDrawer(): Promise<boolean>;
    dismissOverlays(): Promise<boolean>;
    handleTopBarEmptyClick(): Promise<boolean>;
    handleInspectorEmptyClick(): Promise<boolean>;
    handleWorkspaceEmptyClick(): Promise<boolean>;
    setDisclosureState(id: UiDisclosureId, open: boolean): void;
    toggleTheme(): void;
}

export interface AppActionSet extends
    SimulationActionSet,
    PatternActionSet,
    PresetActionSet,
    ShowcaseActionSet,
    UiActionSet {
    resetAllSettings(): Promise<SimulationSnapshot | null>;
    undoEdit(): Promise<unknown> | undefined;
    redoEdit(): Promise<unknown> | undefined;
    cancelEditorPreview(): Promise<unknown> | undefined;
}

export interface PatternActionOptions {
    state: AppState;
    elements: DomElements;
    interactions: InteractionController;
    viewportController: ViewportController;
    renderControlPanel: () => void;
    applySimulationState: (
        simulationState: SimulationSnapshot,
        options?: { source?: string },
    ) => void;
    postControlFn: PostControlFunction;
    setCellsRequestFn: SetCellsRequestFunction;
    onError: (error: unknown) => void;
    refreshState: () => Promise<void>;
    simulationMutations?: ActionMutationAdapter | SimulationMutations | null;
}

export interface PresetActionOptions {
    state: AppState;
    elements: DomElements;
    interactions: InteractionController;
    applySimulationState: (
        simulationState: SimulationSnapshot,
        options?: { source?: string },
    ) => void;
    postControlFn: PostControlFunction;
    setCellsRequestFn: SetCellsRequestFunction;
    onError: (error: unknown) => void;
    refreshState: () => Promise<void>;
    renderControlPanel: () => void;
    simulationMutations?: ActionMutationAdapter | SimulationMutations | null;
}

export interface ShowcaseActionOptions {
    state: AppState;
    elements: DomElements;
    interactions: InteractionController;
    applySimulationState: (
        simulationState: SimulationSnapshot,
        options?: { source?: string },
    ) => void;
    postControlFn: PostControlFunction;
    setCellsRequestFn: SetCellsRequestFunction;
    renderControlPanel: () => void;
    refreshState: () => Promise<void>;
    onError: (error: unknown) => void;
    getViewportDimensions: (
        geometry: string,
        ruleName: string | null,
        cellSize: number,
    ) => ViewportDimensions;
    simulationMutations?: ActionMutationAdapter | SimulationMutations | null;
}

export interface UiActionOptions {
    state: AppState;
    uiSessionController: UiSessionController;
    renderCurrentGrid: () => void;
    renderControlPanel: () => void;
    viewportController: ViewportController | null;
}

export interface AppActionOptions {
    state: AppState;
    elements: DomElements;
    interactions: InteractionController;
    viewportController: ViewportController;
    configSyncController: ConfigSyncController;
    uiSessionController: UiSessionController;
    renderCurrentGrid: () => void;
    renderControlPanel: () => void;
    applySimulationState: (
        simulationState: SimulationSnapshot,
        options?: { source?: string },
    ) => void;
    getViewportDimensions: (
        geometry: string,
        ruleName: string | null,
        cellSize: number,
    ) => ViewportDimensions;
    postControlFn: PostControlFunction;
    setCellsRequestFn: SetCellsRequestFunction;
    onError: (error: unknown) => void;
    refreshState: () => Promise<void>;
    simulationMutations?: ActionMutationAdapter | SimulationMutations | null;
}

export interface PatternImportOptions {
    successMessage: string;
    cancelMessage: string;
    blockingActivity?: BlockingActivityConfig | null;
    onSuccess?: () => void;
}

export type ResetRequestBody = ResetControlBody;

export interface PatternBuildResult {
    pattern: PatternPayload;
    filename: string;
    content: string;
}

export interface ShowcaseDefinition {
    tiling_family: string;
    adjacency_mode: string;
    rule: string;
    randomize: boolean;
    successMessage: string;
    patch_depth?: number;
}

export interface PresetSeedBuildRequest {
    ruleName: string;
    geometry: string;
    width: number;
    height: number;
    presetId: string | null;
}

export interface PatternCellResolver {
    (parsedPattern: ParsedPattern): CellStateUpdate[];
}

export interface ResolvedPresetMetadata extends ResolvedPresetSelection {
    presetOptions: PresetMetadata[];
}

export interface SimulationActionRuleSyncOptions {
    running: boolean;
    body?: ConfigSyncBody;
}
