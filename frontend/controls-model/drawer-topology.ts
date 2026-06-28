import {
    tilingFamilyOptions,
    topologyModeFieldLabel,
    topologyModeOptions,
} from "../topology-catalog.js";
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

function formatSpeed(value: number): string {
    if (!Number.isFinite(value)) {
        return "--";
    }
    if (value >= 10 || Number.isInteger(value)) {
        return String(Math.round(value));
    }
    return value.toFixed(1);
}

function buildActualSpeedState({
    measuredSpeed,
    targetSpeed,
    running,
}: {
    measuredSpeed: number | null;
    targetSpeed: number;
    running: boolean;
}): Pick<DrawerTopologyViewModel, "speedActualLabel" | "speedActualVisible" | "speedLimited"> {
    if (!running) {
        return {
            speedActualLabel: "",
            speedActualVisible: false,
            speedLimited: false,
        };
    }
    if (measuredSpeed === null) {
        return {
            speedActualLabel: "Actual: measuring",
            speedActualVisible: true,
            speedLimited: false,
        };
    }

    const speedLimited = targetSpeed >= 5 && measuredSpeed < targetSpeed * 0.8;
    return {
        speedActualLabel: `${speedLimited ? "Limited" : "Actual"}: ${formatSpeed(
            measuredSpeed,
        )} gen/s`,
        speedActualVisible: true,
        speedLimited,
    };
}

export function buildDrawerTopologyViewModel({
    state,
    syncState,
}: {
    state: AppState;
    syncState: ConfigSyncViewState;
}): DrawerTopologyViewModel {
    const tilingFamily = state.topologySpec?.tiling_family || "square";
    const adjacencyOptions = topologyModeOptions(tilingFamily);
    const adjacencyModeVisible = adjacencyOptions.length > 1;
    const speedValue = resolveSpeedValue(state, syncState);
    const sizingState = resolveViewportSizingState(state);
    const actualSpeedState = buildActualSpeedState({
        measuredSpeed: state.measuredSpeed,
        targetSpeed: Number(speedValue),
        running: state.isRunning,
    });

    return {
        tilingFamilyOptions: tilingFamilyOptions(),
        tilingFamilyValue: tilingFamily,
        adjacencyModeOptions: adjacencyOptions,
        topologyModeLabel: topologyModeFieldLabel(tilingFamily),
        adjacencyModeValue: state.topologySpec?.adjacency_mode || "edge",
        adjacencyModeVisible,
        speedValue: String(speedValue),
        speedLabel: `Target ${formatSpeed(Number(speedValue))} gen/s`,
        ...actualSpeedState,
        unsafeSizingEnabled: Boolean(state.unsafeSizingEnabled),
        tileColorsEnabled: state.tileColorsEnabled !== false,
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
