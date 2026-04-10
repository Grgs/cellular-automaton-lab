import { adjacencyModeOptions, getTopologyDefinition, tilingFamilyOptions } from "../topology-catalog.js";
import {
    buildDrawerToggleState,
    buildOverlayVisibilityState,
    buildQuickStartHintState,
    buildCellSizeViewState,
    buildHiddenCellSizeViewState,
    buildHiddenPatchDepthViewState,
    buildPatchDepthViewState,
    resolveBlockingActivity,
    resolvePatternStatus,
    resolveSpeedValue,
    resolveViewportSizingState,
} from "./shared.js";
import { buildSelectionInspectorViewModel } from "./selection-inspector.js";
import type { ResolvedPresetSelection } from "../types/domain.js";
import type {
    ControlsModelRuleContext,
    DrawerViewModel,
    SelectionInspectorSource,
} from "../types/ui.js";

export function buildDrawerViewModel({
    state,
    syncState,
    activeRule,
    paletteRule,
    presetSelection,
    selectionInspectorSource,
}: ControlsModelRuleContext & {
    presetSelection: ResolvedPresetSelection;
    selectionInspectorSource: SelectionInspectorSource;
}): DrawerViewModel {
    const supportsRandomize = Boolean(paletteRule && paletteRule.supports_randomize);
    const presetOptions = presetSelection.presetOptions;
    const presetSeedAvailable = presetOptions.length > 0;
    const exportPatternDisabled = !activeRule || !state.topology;
    const availableRules = Array.isArray(state.rules) ? state.rules : [];
    const tilingFamily = state.topologySpec?.tiling_family || "square";
    const topologyDefinition = getTopologyDefinition(tilingFamily);
    const overlayVisibility = buildOverlayVisibilityState(state);
    const { drawerToggleLabel, drawerToggleTitle } = buildDrawerToggleState(state);
    const blockingActivity = resolveBlockingActivity(state);
    const patternStatus = resolvePatternStatus(state);
    const quickStartHint = buildQuickStartHintState(state, activeRule);
    const speedValue = resolveSpeedValue(state, syncState);
    const sizingState = resolveViewportSizingState(state);
    const adjacencyOptions = adjacencyModeOptions(tilingFamily);
    const adjacencyModeVisible = adjacencyOptions.length > 1;
    const presetHelperText = presetSeedAvailable
        ? "Loads a curated seed for this rule and board."
        : "No curated preset is available for this rule/topology yet.";

    return {
        inspectorTilingText: topologyDefinition?.label || tilingFamily,
        inspectorRuleText: activeRule?.display_name || activeRule?.label || "Choose a rule",
        selectionInspector: buildSelectionInspectorViewModel({
            selectedCells: selectionInspectorSource.selectedCells,
            topologyIndex: state.topologyIndex,
            cellStates: state.cellStates,
            activeRule,
        }),
        ruleSummaryText: paletteRule?.description || "Select a rule to see its evolution notes and paint states.",
        overlaysDismissed: Boolean(state.overlaysDismissed),
        drawerVisible: overlayVisibility.drawerVisible,
        backdropVisible: overlayVisibility.backdropVisible,
        tilingFamilyOptions: tilingFamilyOptions(),
        tilingFamilyValue: tilingFamily,
        adjacencyModeOptions: adjacencyOptions,
        adjacencyModeValue: state.topologySpec?.adjacency_mode || "edge",
        adjacencyModeVisible,
        syncStatusText: syncState?.isSyncing ? "Syncing..." : "",
        speedValue: String(speedValue),
        speedLabel: `${speedValue} gen/s`,
        ruleSelectValue: paletteRule ? paletteRule.name : "",
        ruleOptions: availableRules.map((rule) => ({
            name: rule.name,
            displayName: rule.display_name || rule.label || rule.name,
        })),
        ruleDescription: paletteRule?.description ?? "",
        paletteStates: Array.isArray(paletteRule?.states)
            ? paletteRule.states
                .filter((cellState) => cellState.paintable)
                .map((cellState) => ({
                    value: cellState.value,
                    label: cellState.label ?? `State ${cellState.value}`,
                    color: cellState.color ?? "",
                }))
            : [],
        selectedPaintState: state.selectedPaintState,
        randomResetVisible: supportsRandomize,
        randomResetDisabled: !supportsRandomize,
        randomResetTitle: supportsRandomize
            ? ""
            : "Random reset is only available for rules that define random state weights.",
        presetSeedLabel: "Preset Seed",
        presetSeedDisabled: !presetSeedAvailable,
        presetSeedTitle: presetSeedAvailable
            ? "Reset the grid and load a curated preset seed for the selected rule."
            : "No preset seed is available for the selected rule at the current grid size.",
        presetHelperText,
        presetSeedOptions: presetOptions,
        presetSeedValue: presetSelection.selectedPresetId,
        presetSeedSelectVisible: presetOptions.length > 1,
        importPatternLabel: "Import Pattern",
        importPatternTitle: "Load a saved JSON pattern file into the simulation.",
        copyPatternLabel: "Copy Pattern",
        copyPatternDisabled: exportPatternDisabled,
        copyPatternTitle: exportPatternDisabled
            ? "Patterns can be copied after the simulation finishes loading. If clipboard access fails, use Export Pattern."
            : "Copy a JSON pattern for the current board to the clipboard. If clipboard access fails, use Export Pattern.",
        exportPatternLabel: "Export Pattern",
        exportPatternDisabled,
        exportPatternTitle: exportPatternDisabled
            ? "Patterns can be exported after the simulation finishes loading."
            : "Download a JSON pattern file for the current board.",
        pastePatternLabel: "Paste Pattern",
        pastePatternDisabled: false,
        pastePatternTitle: "Read a JSON pattern from the clipboard and load it into the simulation. If clipboard access fails, use Import Pattern.",
        drawerToggleLabel,
        drawerToggleTitle,
        quickStartHintText: quickStartHint.quickStartHintText,
        quickStartHintVisible: quickStartHint.quickStartHintVisible && patternStatus.patternStatusText === "",
        unsafeSizingEnabled: Boolean(state.unsafeSizingEnabled),
        ...(sizingState.usesPatchDepth
            ? {
                ...buildHiddenCellSizeViewState(),
                ...buildPatchDepthViewState(
                    sizingState.patchDepth,
                    sizingState.patchDepthMax,
                    sizingState.patchDepthMin,
                ),
            }
            : {
                ...buildCellSizeViewState(
                    sizingState.cellSize,
                    sizingState.cellSizeMin,
                    sizingState.cellSizeMax,
                ),
                ...buildHiddenPatchDepthViewState(),
            }),
        ...blockingActivity,
        ...patternStatus,
    };
}
