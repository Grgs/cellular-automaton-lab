import {
    DEFAULT_BRUSH_SIZE,
    DEFAULT_EDITOR_TOOL,
    clampBrushSize,
    resolveEditorTool,
} from "../editor-tools.js";
import {
    describeTopologySpec,
    resolveTopologyVariantKey,
} from "../topology-catalog.js";
import { indexTopology } from "../topology.js";
import {
    DEFAULT_CELL_SIZE,
    DEFAULT_DRAWER_OPEN,
    DEFAULT_PATCH_DEPTH,
    DEFAULT_SPEED,
    DEFAULT_TOPOLOGY_SPEC,
    DEFAULT_TOPOLOGY_VARIANT_KEY,
    RULE_SELECTION_ORIGIN_DEFAULT,
    RULE_SELECTION_ORIGIN_USER,
} from "./constants.js";
import type {
    RuleDefinition,
    TopologyPayload,
    TopologySpec,
} from "../types/domain.js";
import type { EditorTool } from "../editor-tools.js";
import type {
    AppState,
    PreviewCellStatesById,
    RuleSelectionOrigin,
} from "../types/state.js";

function syncSelectedPaintState(
    state: AppState,
    rule: RuleDefinition | null,
    preferDefault = false,
): void {
    if (!rule) {
        state.selectedPaintState = null;
        return;
    }

    const ruleStates = Array.isArray(rule.states) ? rule.states : [];
    const paintableStates = ruleStates.filter((cellState) => cellState.paintable);
    const defaultPaintState = rule.default_paint_state ?? paintableStates[0]?.value ?? 0;
    const selectedStateIsPaintable = paintableStates.some(
        (cellState) => cellState.value === state.selectedPaintState,
    );

    if (preferDefault || !selectedStateIsPaintable) {
        state.selectedPaintState = defaultPaintState;
    }
}

function resolveCurrentEditorRule(state: AppState): RuleDefinition | null {
    const editorRule = findRule(state, state.editorRuleName);
    if (editorRule) {
        return editorRule;
    }
    if (state.activeRule) {
        return state.activeRule;
    }
    return state.rules[0] || null;
}

export function createAppState(): AppState {
    return {
        rules: [],
        activeRule: null,
        editorRuleName: null,
        ruleSelectionOrigin: RULE_SELECTION_ORIGIN_DEFAULT,
        selectedEditorTool: DEFAULT_EDITOR_TOOL,
        brushSize: DEFAULT_BRUSH_SIZE,
        selectedPaintState: null,
        selectedPresetIdsByRule: {},
        undoStack: [],
        redoStack: [],
        pollTimer: null,
        isRunning: false,
        generation: 0,
        speed: DEFAULT_SPEED,
        topologySpec: { ...DEFAULT_TOPOLOGY_SPEC },
        patchDepth: DEFAULT_PATCH_DEPTH,
        pendingPatchDepth: null,
        patchDepthByTilingFamily: {},
        unsafeSizingEnabled: false,
        width: 0,
        height: 0,
        topologyRevision: null,
        topology: null,
        topologyIndex: null,
        cellStates: [],
        previewTopology: null,
        previewTopologyRevision: null,
        previewCellStatesById: null,
        cellSize: DEFAULT_CELL_SIZE,
        cellSizeByTilingFamily: {},
        renderCellSize: DEFAULT_CELL_SIZE,
        drawerOpen: DEFAULT_DRAWER_OPEN,
        overlaysDismissed: false,
        inspectorTemporarilyHidden: false,
        overlayRunPending: false,
        runningOverlayRestoreActive: false,
        inspectorOccludesGrid: true,
        editArmed: false,
        editCueVisible: false,
        firstRunHintDismissed: false,
        blockingActivityKind: null,
        blockingActivityMessage: "",
        blockingActivityDetail: "",
        blockingActivityVisible: false,
        blockingActivityStartedAt: null,
        patternStatus: {
            message: "",
            tone: "info",
        },
    };
}

export function setRules(state: AppState, rules: RuleDefinition[]): void {
    state.rules = rules;
}

export function findRule(state: AppState, ruleName: string | null): RuleDefinition | undefined {
    return state.rules.find((rule) => rule.name === ruleName);
}

export function setActiveRule(state: AppState, rule: RuleDefinition | null): void {
    state.activeRule = rule;
    if (rule && (!state.editorRuleName || !findRule(state, state.editorRuleName))) {
        state.editorRuleName = rule.name;
    }
    syncSelectedPaintState(state, resolveCurrentEditorRule(state));
}

export function setEditorRule(
    state: AppState,
    ruleName: string | null,
    { resetPaintState = true }: { resetPaintState?: boolean } = {},
): void {
    state.editorRuleName = ruleName || null;
    syncSelectedPaintState(state, resolveCurrentEditorRule(state), resetPaintState);
}

export function setRuleSelectionOrigin(
    state: AppState,
    origin: RuleSelectionOrigin = RULE_SELECTION_ORIGIN_DEFAULT,
): void {
    state.ruleSelectionOrigin = origin === RULE_SELECTION_ORIGIN_USER
        ? RULE_SELECTION_ORIGIN_USER
        : RULE_SELECTION_ORIGIN_DEFAULT;
}

export function currentRuleSelectionOrigin(state: AppState): RuleSelectionOrigin {
    return state.ruleSelectionOrigin === RULE_SELECTION_ORIGIN_USER
        ? RULE_SELECTION_ORIGIN_USER
        : RULE_SELECTION_ORIGIN_DEFAULT;
}

export function setSelectedPaintState(state: AppState, paintState: number | null): void {
    state.selectedPaintState = paintState;
}

export function setEditorTool(state: AppState, tool: EditorTool): void {
    state.selectedEditorTool = resolveEditorTool(tool);
}

export function setBrushSize(state: AppState, brushSize: number): void {
    state.brushSize = clampBrushSize(brushSize);
}

export function setUnsafeSizingEnabled(state: AppState, enabled: boolean): void {
    state.unsafeSizingEnabled = Boolean(enabled);
}

export function getSelectedPresetId(state: AppState, ruleName: string | null): string | null {
    if (!ruleName) {
        return null;
    }
    return state.selectedPresetIdsByRule[ruleName] ?? null;
}

export function setSelectedPresetId(state: AppState, ruleName: string | null, presetId: string | null): void {
    if (!ruleName) {
        return;
    }
    if (!presetId) {
        delete state.selectedPresetIdsByRule[ruleName];
        return;
    }
    state.selectedPresetIdsByRule[ruleName] = presetId;
}

export function setSpeed(state: AppState, speed: number): void {
    state.speed = speed;
}

export function setTopologySpec(state: AppState, topologySpec: Partial<TopologySpec>): void {
    state.topologySpec = describeTopologySpec(topologySpec);
}

export function setTopology(state: AppState, topology: TopologyPayload | null, cellStates: number[] = []): void {
    const normalizedTopology = topology
        ? {
            ...topology,
            topology_spec: describeTopologySpec(
                topology.topology_spec,
            ),
        }
        : null;
    state.topology = normalizedTopology;
    state.topologyRevision = normalizedTopology?.topology_revision ?? null;
    state.topologyIndex = normalizedTopology ? indexTopology(normalizedTopology) : null;
    state.cellStates = Array.isArray(cellStates) ? cellStates : [];
    if (normalizedTopology) {
        const topologySpec = describeTopologySpec(normalizedTopology.topology_spec);
        setTopologySpec(state, {
            ...topologySpec,
            width: topologySpec.width,
            height: topologySpec.height,
            patch_depth: topologySpec.patch_depth,
        });
        state.width = Number(topologySpec.width) || 0;
        state.height = Number(topologySpec.height) || 0;
    } else {
        state.topologyRevision = null;
        state.topologyIndex = null;
        state.cellStates = [];
    }
}

export function setViewportPreview(
    state: AppState,
    previewTopology: TopologyPayload | null,
    previewCellStatesById: PreviewCellStatesById = {},
    baseTopologyRevision: string | null = state.topologyRevision,
): void {
    state.previewTopology = previewTopology ?? null;
    state.previewTopologyRevision = previewTopology ? String(baseTopologyRevision ?? "") : null;
    state.previewCellStatesById = previewTopology ? { ...previewCellStatesById } : null;
}

export function clearViewportPreview(state: AppState): void {
    state.previewTopology = null;
    state.previewTopologyRevision = null;
    state.previewCellStatesById = null;
}

export function currentTopologyVariantKey(state: AppState): string {
    const topologySpec = describeTopologySpec(state.topologySpec || DEFAULT_TOPOLOGY_SPEC);
    return resolveTopologyVariantKey(topologySpec.tiling_family, topologySpec.adjacency_mode)
        || DEFAULT_TOPOLOGY_VARIANT_KEY;
}

export {
    DEFAULT_DRAWER_OPEN,
    DEFAULT_SPEED,
    DEFAULT_TOPOLOGY_SPEC,
    DEFAULT_TOPOLOGY_VARIANT_KEY,
    RULE_SELECTION_ORIGIN_DEFAULT,
    RULE_SELECTION_ORIGIN_USER,
};
