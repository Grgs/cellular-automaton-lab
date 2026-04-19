import { adjacencyModeOptions, tilingFamilyOptions } from "../topology-catalog.js";
import {
    buildCellSizeViewState,
    buildHiddenCellSizeViewState,
    buildHiddenPatchDepthViewState,
    buildPatchDepthViewState,
    resolveSpeedValue,
    resolveViewportSizingState,
} from "./shared.js";
import type { ConfigSyncViewState } from "../types/controller.js";
import type { AppState } from "../types/state.js";
import type { DrawerTopologyViewModel } from "../types/ui.js";

export function buildDrawerTopologyViewModel({
    state,
    syncState,
}: {
    state: AppState;
    syncState: ConfigSyncViewState;
}): DrawerTopologyViewModel {
    const tilingFamily = state.topologySpec?.tiling_family || "square";
    const adjacencyOptions = adjacencyModeOptions(tilingFamily);
    const adjacencyModeVisible = adjacencyOptions.length > 1;
    const speedValue = resolveSpeedValue(state, syncState);
    const sizingState = resolveViewportSizingState(state);

    return {
        tilingFamilyOptions: tilingFamilyOptions(),
        tilingFamilyValue: tilingFamily,
        adjacencyModeOptions: adjacencyOptions,
        adjacencyModeValue: state.topologySpec?.adjacency_mode || "edge",
        adjacencyModeVisible,
        speedValue: String(speedValue),
        speedLabel: `${speedValue} gen/s`,
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
    };
}
