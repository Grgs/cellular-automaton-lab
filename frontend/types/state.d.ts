import type {
    RuleDefinition,
    TopologyIndex,
    TopologyPayload,
    TopologySpec,
} from "./domain.js";
import type { BrowserTimerId } from "./controller.js";
import type { EditorHistoryEntry } from "./editor.js";

export type RuleSelectionOrigin = "default" | "user";

export interface PatternStatus {
    message: string;
    tone: string;
}

export type PreviewCellStatesById = Record<string, number>;

export interface AppState {
    rules: RuleDefinition[];
    activeRule: RuleDefinition | null;
    editorRuleName: string | null;
    ruleSelectionOrigin: RuleSelectionOrigin;
    selectedEditorTool: string;
    brushSize: number;
    selectedPaintState: number | null;
    selectedPresetIdsByRule: Record<string, string>;
    undoStack: EditorHistoryEntry[];
    redoStack: EditorHistoryEntry[];
    pollTimer: BrowserTimerId | null;
    isRunning: boolean;
    generation: number;
    speed: number;
    topologySpec: TopologySpec;
    patchDepth: number;
    pendingPatchDepth: number | null;
    patchDepthByTilingFamily: Record<string, number>;
    width: number;
    height: number;
    topologyRevision: string | null;
    topology: TopologyPayload | null;
    topologyIndex: TopologyIndex | null;
    cellStates: number[];
    previewTopology: TopologyPayload | null;
    previewTopologyRevision: string | null;
    previewCellStatesById: PreviewCellStatesById | null;
    cellSize: number;
    cellSizeByTilingFamily: Record<string, number>;
    renderCellSize: number;
    drawerOpen: boolean;
    overlaysDismissed: boolean;
    inspectorTemporarilyHidden: boolean;
    overlayRunPending: boolean;
    runningOverlayRestoreActive: boolean;
    inspectorOccludesGrid: boolean;
    editArmed: boolean;
    editCueVisible: boolean;
    firstRunHintDismissed: boolean;
    blockingActivityKind: string | null;
    blockingActivityMessage: string;
    blockingActivityDetail: string;
    blockingActivityVisible: boolean;
    blockingActivityStartedAt: number | null;
    patternStatus: PatternStatus;
}

export interface TopologyRenderPayload {
    topology: TopologyPayload | null;
    cellStates: number[];
    previewCellStatesById: PreviewCellStatesById | null;
}
