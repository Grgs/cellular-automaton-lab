import { getTopologyDefinition, topologyModeLabel } from "../topology-catalog.js";
import {
    buildRunToggleState,
    resolveViewportSizingState,
    buildOverlayVisibilityState,
} from "./shared.js";
import type { ControlsModelRuleContext, TopBarViewModel } from "../types/ui.js";

export function buildTopBarViewModel({
    state,
    syncState,
    activeRule,
}: ControlsModelRuleContext): TopBarViewModel {
    const sizingState = resolveViewportSizingState(state);
    const tilingFamily = state.topologySpec?.tiling_family || "square";
    const topologyDefinition = getTopologyDefinition(tilingFamily);
    const adjacencyModeValue = state.topologySpec?.adjacency_mode || "edge";
    const adjacencyModeVisible = (topologyDefinition?.supported_adjacency_modes?.length || 0) > 1;
    const overlayVisibility = buildOverlayVisibilityState(state);
    return {
        statusText: state.isRunning ? "Running" : "Paused",
        generationText: String(state.generation),
        syncStatusText: syncState?.isSyncing ? "Syncing..." : "",
        ruleText: activeRule?.display_name || "",
        gridSizeText: sizingState.gridSizeText,
        canvasHudTilingText: topologyDefinition?.label || tilingFamily,
        canvasHudAdjacencyText: topologyModeLabel(tilingFamily, adjacencyModeValue),
        canvasHudAdjacencyVisible: adjacencyModeVisible,
        hudVisible: overlayVisibility.hudVisible,
        runToggle: buildRunToggleState(state.isRunning, state.generation),
    };
}
