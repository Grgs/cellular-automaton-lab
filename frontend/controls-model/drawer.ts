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
import type { IndexedTopologyCell, ResolvedPresetSelection, RuleDefinition } from "../types/domain.js";
import type {
    ControlsModelRuleContext,
    DrawerViewModel,
    SelectionInspectorSource,
    SelectionInspectorSummaryRow,
    SelectionInspectorViewModel,
} from "../types/ui.js";

const EMPTY_SELECTION_HINT = "Right-click a cell to inspect it. Right-drag to summarize a selection.";
const MAX_ADVANCED_SELECTED_CELL_IDS = 20;

function formatNumber(value: number): string {
    return value.toFixed(3);
}

function formatPoint(point: { x: number; y: number }): string {
    return `(${formatNumber(point.x)}, ${formatNumber(point.y)})`;
}

function countNeighbors(cell: { neighbors: Array<string | null> }): number {
    return cell.neighbors.filter((neighborId) => typeof neighborId === "string" && neighborId.length > 0).length;
}

function formatStateLabel(stateValue: number, activeRule: RuleDefinition | null): string {
    const resolvedLabel = activeRule?.states?.find((state) => state.value === stateValue)?.label;
    if (stateValue === 0) {
        return resolvedLabel ? `${resolvedLabel} (0)` : "Dead (0)";
    }
    if (resolvedLabel) {
        return `${resolvedLabel} (${stateValue})`;
    }
    return `State ${stateValue}`;
}

function formatFrequencyMap(frequencies: Map<string, number>): string {
    return Array.from(frequencies.entries())
        .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
        .map(([label, count]) => `${label}: ${count}`)
        .join(", ");
}

function addFrequencyValue(frequencies: Map<string, number>, label: string | null | undefined): void {
    if (typeof label !== "string" || label.length === 0) {
        return;
    }
    frequencies.set(label, (frequencies.get(label) ?? 0) + 1);
}

function collectIndexedSelection(
    selectedCells: SelectionInspectorSource["selectedCells"],
    byId: Map<string, IndexedTopologyCell> | undefined,
): IndexedTopologyCell[] {
    if (!byId) {
        return [];
    }
    return selectedCells
        .map((cell) => byId.get(cell.id))
        .filter((cell): cell is IndexedTopologyCell => Boolean(cell));
}

function buildSingleSelectionInspector(
    cell: IndexedTopologyCell,
    cellStates: number[],
    activeRule: RuleDefinition | null,
): SelectionInspectorViewModel {
    const stateValue = Number(cellStates[cell.index] ?? 0);
    const summaryRows: SelectionInspectorSummaryRow[] = [
        { label: "State", value: formatStateLabel(stateValue, activeRule) },
        { label: "Cell ID", value: cell.id },
        { label: "Kind", value: cell.kind },
        { label: "Neighbor Count", value: String(countNeighbors(cell)) },
    ];
    const decorations = Array.isArray(cell.decoration_tokens) ? [...cell.decoration_tokens].sort() : [];
    if (cell.tile_family) {
        summaryRows.push({ label: "Tile Family", value: cell.tile_family });
    }
    if (cell.orientation_token) {
        summaryRows.push({ label: "Orientation", value: cell.orientation_token });
    }
    if (cell.chirality_token) {
        summaryRows.push({ label: "Chirality", value: cell.chirality_token });
    }
    if (decorations.length > 0) {
        summaryRows.push({ label: "Decorations", value: decorations.join(", ") });
    }
    if (cell.center) {
        summaryRows.push({ label: "Center", value: formatPoint(cell.center) });
    }
    if (Array.isArray(cell.vertices) && cell.vertices.length > 0) {
        summaryRows.push({ label: "Vertex Count", value: String(cell.vertices.length) });
    }
    if (cell.slot) {
        summaryRows.push({ label: "Slot", value: cell.slot });
    }

    const advancedRows: SelectionInspectorSummaryRow[] = [];
    const neighborIds = cell.neighbors.filter((neighborId): neighborId is string => typeof neighborId === "string" && neighborId.length > 0);
    if (neighborIds.length > 0) {
        advancedRows.push({ label: "Neighbor IDs", value: neighborIds.join(", ") });
    }
    if (Array.isArray(cell.vertices) && cell.vertices.length > 0) {
        advancedRows.push({
            label: "Vertices",
            value: cell.vertices.map((vertex) => formatPoint(vertex)).join(", "),
        });
    }

    return {
        mode: "single",
        title: "1 Cell Selected",
        subtitle: `${cell.kind} | ${formatStateLabel(stateValue, activeRule)}`,
        hintText: EMPTY_SELECTION_HINT,
        summaryRows,
        advancedRows,
        advancedVisible: advancedRows.length > 0,
        advancedSummaryText: "Advanced Details",
    };
}

function buildMultiSelectionInspector(
    cells: IndexedTopologyCell[],
    cellStates: number[],
    activeRule: RuleDefinition | null,
): SelectionInspectorViewModel {
    const stateMix = new Map<string, number>();
    const kindMix = new Map<string, number>();
    const tileFamilyMix = new Map<string, number>();
    const orientationMix = new Map<string, number>();
    const chiralityMix = new Map<string, number>();
    const decorationMix = new Map<string, number>();
    const neighborCountDistribution = new Map<string, number>();
    const vertexCountDistribution = new Map<string, number>();
    const selectedIds = cells.map((cell) => cell.id);
    const centers = cells.filter((cell) => Boolean(cell.center)).map((cell) => cell.center!);

    cells.forEach((cell) => {
        const stateValue = Number(cellStates[cell.index] ?? 0);
        addFrequencyValue(stateMix, formatStateLabel(stateValue, activeRule));
        addFrequencyValue(kindMix, cell.kind);
        addFrequencyValue(tileFamilyMix, cell.tile_family);
        addFrequencyValue(orientationMix, cell.orientation_token);
        addFrequencyValue(chiralityMix, cell.chirality_token);
        addFrequencyValue(neighborCountDistribution, String(countNeighbors(cell)));
        if (Array.isArray(cell.vertices) && cell.vertices.length > 0) {
            addFrequencyValue(vertexCountDistribution, String(cell.vertices.length));
        }
        if (Array.isArray(cell.decoration_tokens)) {
            [...cell.decoration_tokens].sort().forEach((token) => addFrequencyValue(decorationMix, token));
        }
    });

    const summaryRows: SelectionInspectorSummaryRow[] = [
        { label: "Selected Cells", value: String(cells.length) },
        { label: "State Mix", value: formatFrequencyMap(stateMix) },
        { label: "Kind Mix", value: formatFrequencyMap(kindMix) },
    ];
    if (tileFamilyMix.size > 0) {
        summaryRows.push({ label: "Tile Family Mix", value: formatFrequencyMap(tileFamilyMix) });
    }
    if (orientationMix.size > 0) {
        summaryRows.push({ label: "Orientation Mix", value: formatFrequencyMap(orientationMix) });
    }
    if (chiralityMix.size > 0) {
        summaryRows.push({ label: "Chirality Mix", value: formatFrequencyMap(chiralityMix) });
    }
    if (decorationMix.size > 0) {
        summaryRows.push({ label: "Decoration Mix", value: formatFrequencyMap(decorationMix) });
    }

    const advancedRows: SelectionInspectorSummaryRow[] = [
        { label: "Neighbor Count Distribution", value: formatFrequencyMap(neighborCountDistribution) },
    ];
    if (vertexCountDistribution.size > 0) {
        advancedRows.push({ label: "Vertex Count Distribution", value: formatFrequencyMap(vertexCountDistribution) });
    }
    if (centers.length > 0) {
        const xs = centers.map((center) => center.x);
        const ys = centers.map((center) => center.y);
        advancedRows.push({
            label: "Center Bounds",
            value: `x ${formatNumber(Math.min(...xs))}-${formatNumber(Math.max(...xs))}, y ${formatNumber(Math.min(...ys))}-${formatNumber(Math.max(...ys))}`,
        });
    }
    if (selectedIds.length > 0) {
        const visibleIds = selectedIds.slice(0, MAX_ADVANCED_SELECTED_CELL_IDS);
        const remainingCount = selectedIds.length - visibleIds.length;
        advancedRows.push({
            label: "Selected Cell IDs",
            value: remainingCount > 0
                ? `${visibleIds.join(", ")}, +${remainingCount} more`
                : visibleIds.join(", "),
        });
    }

    return {
        mode: "multi",
        title: `${cells.length} Cells Selected`,
        subtitle: "Aggregate selection summary",
        hintText: EMPTY_SELECTION_HINT,
        summaryRows,
        advancedRows,
        advancedVisible: advancedRows.length > 0,
        advancedSummaryText: "Advanced Details",
    };
}

function buildSelectionInspectorViewModel({
    selectedCells,
    topologyIndex,
    cellStates,
    activeRule,
}: {
    selectedCells: SelectionInspectorSource["selectedCells"];
    topologyIndex: ControlsModelRuleContext["state"]["topologyIndex"];
    cellStates: ControlsModelRuleContext["state"]["cellStates"];
    activeRule: RuleDefinition | null;
}): SelectionInspectorViewModel {
    const indexedSelection = collectIndexedSelection(selectedCells, topologyIndex?.byId);
    if (indexedSelection.length === 0) {
        return {
            mode: "empty",
            title: "No Cells Selected",
            subtitle: "",
            hintText: EMPTY_SELECTION_HINT,
            summaryRows: [],
            advancedRows: [],
            advancedVisible: false,
            advancedSummaryText: "Advanced Details",
        };
    }
    if (indexedSelection.length === 1) {
        return buildSingleSelectionInspector(indexedSelection[0]!, cellStates, activeRule);
    }
    return buildMultiSelectionInspector(indexedSelection, cellStates, activeRule);
}

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
