import type { ConfigSyncViewState } from "./controller.js";
import type {
    AdjacencyModeOption,
    PresetMetadata,
    RuleDefinition,
    TopologyOption,
} from "./domain.js";
import type { AppState } from "./state.js";
import type { EditorTool } from "../editor-tools.js";
import type { ThemeName } from "../theme.js";

export interface LabeledOption<TValue extends string | number = string | number> {
    value: TValue;
    label: string;
}

export interface RuleSelectOption {
    name: string;
    displayName: string;
}

export interface PaintPaletteState {
    value: number;
    label: string;
    color: string;
}

export interface RunToggleViewModel {
    label: string;
    controlAction: string;
    ariaLabel: string;
    isRunning: boolean;
}

export interface DrawerToggleState {
    drawerToggleLabel: string;
    drawerToggleTitle: string;
}

export interface OverlayVisibilityState {
    overlaysVisible: boolean;
    hudVisible: boolean;
    drawerVisible: boolean;
    backdropVisible: boolean;
}

export interface PatternStatusViewState {
    patternStatusText: string;
    patternStatusTone: string;
}

export interface BlockingActivityViewState {
    blockingActivityVisible: boolean;
    blockingActivityMessage: string;
    blockingActivityDetail: string;
}

export interface QuickStartHintState {
    quickStartHintText: string;
    quickStartHintVisible: boolean;
}

export interface ViewportSizingState {
    usesPatchDepth: boolean;
    cellSize: number;
    cellSizeMin: number;
    cellSizeMax: number;
    patchDepth: number;
    patchDepthMin: number;
    patchDepthMax: number;
    gridSizeText: string;
}

export interface RangeControlViewModel {
    visible: boolean;
    visibleTopBar: boolean;
    value: string;
    label: string;
    min: string;
    max: string;
}

export interface TopBarViewModel {
    statusText: string;
    generationText: string;
    syncStatusText: string;
    ruleText: string;
    gridSizeText: string;
    canvasHudTilingText: string;
    canvasHudAdjacencyText: string;
    canvasHudAdjacencyVisible: boolean;
    hudVisible: boolean;
    runToggle: RunToggleViewModel;
}

export interface DrawerViewModel {
    inspectorTilingText: string;
    inspectorRuleText: string;
    ruleSummaryText: string;
    overlaysDismissed: boolean;
    drawerVisible: boolean;
    backdropVisible: boolean;
    tilingFamilyOptions: TopologyOption[];
    tilingFamilyValue: string;
    adjacencyModeOptions: AdjacencyModeOption[];
    adjacencyModeValue: string;
    adjacencyModeVisible: boolean;
    syncStatusText: string;
    speedValue: string;
    speedLabel: string;
    ruleSelectValue: string;
    ruleOptions: RuleSelectOption[];
    ruleDescription: string;
    paletteStates: PaintPaletteState[];
    selectedPaintState: number | null;
    randomResetVisible: boolean;
    randomResetDisabled: boolean;
    randomResetTitle: string;
    presetSeedLabel: string;
    presetSeedDisabled: boolean;
    presetSeedTitle: string;
    presetHelperText: string;
    presetSeedOptions: PresetMetadata[];
    presetSeedValue: string | null;
    presetSeedSelectVisible: boolean;
    importPatternLabel: string;
    importPatternTitle: string;
    copyPatternLabel: string;
    copyPatternDisabled: boolean;
    copyPatternTitle: string;
    exportPatternLabel: string;
    exportPatternDisabled: boolean;
    exportPatternTitle: string;
    pastePatternLabel: string;
    pastePatternDisabled: boolean;
    pastePatternTitle: string;
    drawerToggleLabel: string;
    drawerToggleTitle: string;
    quickStartHintText: string;
    quickStartHintVisible: boolean;
    cellSizeVisible: boolean;
    cellSizeVisibleTopBar: boolean;
    cellSizeValue: string;
    cellSizeLabel: string;
    cellSizeMin: string;
    cellSizeMax: string;
    unsafeSizingEnabled: boolean;
    patchDepthVisible: boolean;
    patchDepthVisibleTopBar: boolean;
    patchDepthValue: string;
    patchDepthLabel: string;
    patchDepthMin: string;
    patchDepthMax: string;
    blockingActivityVisible: boolean;
    blockingActivityMessage: string;
    blockingActivityDetail: string;
    patternStatusText: string;
    patternStatusTone: string;
}

export interface EditorViewModel {
    editorTools: readonly LabeledOption<string>[];
    selectedEditorTool: EditorTool;
    brushSizeOptions: readonly LabeledOption<number>[];
    selectedBrushSize: number;
    undoDisabled: boolean;
    redoDisabled: boolean;
    editorShortcutHint: string;
    gridEditMode: "idle" | "armed" | "running";
    canvasEditCueVisible: boolean;
    canvasEditCueText: string;
}

export interface ControlsViewModel extends TopBarViewModel, DrawerViewModel, EditorViewModel {
    theme: ThemeName;
}

export interface ControlsViewModelInput {
    state: AppState;
    syncState: ConfigSyncViewState;
    theme: ThemeName;
}

export interface ControlsModelRuleContext {
    state: AppState;
    syncState: ConfigSyncViewState;
    activeRule: RuleDefinition | null;
    paletteRule: RuleDefinition | null;
}

export interface SelectOptionRenderValue {
    value: string;
    label: string;
}
