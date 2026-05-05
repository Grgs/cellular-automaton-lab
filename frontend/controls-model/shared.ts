import {
    DEFAULT_BRUSH_SIZE,
    EDITOR_SHORTCUT_HINT,
    EDITOR_TOOL_BRUSH,
    EDITOR_TOOL_FILL,
    EDITOR_TOOL_LINE,
    EDITOR_TOOL_RECTANGLE,
} from "../editor-tools.js";
import {
    DEFAULT_CELL_SIZE,
    DEFAULT_TOPOLOGY_SPEC,
    DEFAULT_PATCH_DEPTH,
    MAX_CELL_SIZE,
    MAX_PATCH_DEPTH,
    MIN_CELL_SIZE,
    MIN_PATCH_DEPTH,
} from "../state/constants.js";
import {
    defaultCellSizeForTilingFamily,
    defaultPatchDepthForTilingFamily,
    maxCellSizeForTilingFamily,
    maxPatchDepthForTilingFamily,
    minCellSizeForTilingFamily,
    minPatchDepthForTilingFamily,
} from "../state/sizing-state.js";
import { topologyUsesPatchDepth } from "../topology-catalog.js";
import type { ConfigSyncViewState } from "../types/controller.js";
import type { RuleDefinition } from "../types/domain.js";
import type { AppState } from "../types/state.js";
import type {
    BlockingActivityViewState,
    DrawerToggleState,
    LabeledOption,
    OverlayVisibilityState,
    PatternStatusViewState,
    QuickStartHintState,
    RunToggleViewModel,
    ViewportSizingState,
} from "../types/ui.js";

export const EDITOR_TOOL_OPTIONS: readonly LabeledOption<string>[] = Object.freeze([
    { value: EDITOR_TOOL_BRUSH, label: "Brush" },
    { value: EDITOR_TOOL_LINE, label: "Line" },
    { value: EDITOR_TOOL_RECTANGLE, label: "Rectangle" },
    { value: EDITOR_TOOL_FILL, label: "Fill" },
]);

export const BRUSH_SIZE_OPTIONS: readonly LabeledOption<number>[] = Object.freeze([
    { value: 1, label: "1" },
    { value: 2, label: "2" },
    { value: 3, label: "3" },
]);

export function buildRunToggleState(isRunning: boolean, generation: number): RunToggleViewModel {
    const nextAction = isRunning ? "pause" : generation > 0 ? "resume" : "start";

    return {
        label: isRunning ? "Pause" : "Run",
        controlAction: nextAction,
        ariaLabel: isRunning ? "Pause simulation" : "Run simulation",
        isRunning,
    };
}

export function resolveSpeedValue(state: AppState, syncState: ConfigSyncViewState): number {
    return syncState?.pendingSpeed ?? syncState?.syncingSpeed ?? state.speed;
}

export function resolvePatternStatus(state: AppState): PatternStatusViewState {
    if (state.blockingActivityVisible && state.blockingActivityMessage) {
        return {
            patternStatusText: state.blockingActivityMessage,
            patternStatusTone: "info",
        };
    }
    return {
        patternStatusText: state.patternStatus?.message ?? "",
        patternStatusTone: state.patternStatus?.tone ?? "info",
    };
}

export function resolveBlockingActivity(state: AppState): BlockingActivityViewState {
    return {
        blockingActivityVisible: Boolean(
            state.blockingActivityVisible && state.blockingActivityMessage,
        ),
        blockingActivityMessage: state.blockingActivityVisible
            ? (state.blockingActivityMessage ?? "")
            : "",
        blockingActivityDetail: state.blockingActivityVisible
            ? (state.blockingActivityDetail ?? "")
            : "",
    };
}

function hasLiveCells(state: AppState): boolean {
    return (
        Array.isArray(state.cellStates) &&
        state.cellStates.some((cellState) => Number(cellState) !== 0)
    );
}

function matchesDefaultTopologySpec(state: AppState): boolean {
    const topologySpec = state.topologySpec || {};
    const sizingMode = String(topologySpec.sizing_mode || "");
    const isPatchDepth = sizingMode === "patch_depth";
    return (
        String(topologySpec.tiling_family || "") === DEFAULT_TOPOLOGY_SPEC.tiling_family &&
        String(topologySpec.adjacency_mode || "") === DEFAULT_TOPOLOGY_SPEC.adjacency_mode &&
        sizingMode === DEFAULT_TOPOLOGY_SPEC.sizing_mode &&
        (isPatchDepth
            ? Number(topologySpec.patch_depth) === Number(DEFAULT_TOPOLOGY_SPEC.patch_depth)
            : Number(topologySpec.width) > 0 && Number(topologySpec.height) > 0)
    );
}

export function buildOverlayVisibilityState(state: AppState): OverlayVisibilityState {
    const inspectorOccludesGrid = state.inspectorOccludesGrid !== false;
    const runningOverlayRestoreActive = Boolean(state.runningOverlayRestoreActive);
    const hudBlocked =
        !runningOverlayRestoreActive && Boolean(state.isRunning || state.overlayRunPending);
    const drawerBlocked = Boolean(
        !runningOverlayRestoreActive &&
        (state.overlayRunPending || (state.isRunning && inspectorOccludesGrid)),
    );
    const hudVisible = !hudBlocked && !state.overlaysDismissed;
    const drawerVisible =
        !drawerBlocked &&
        state.drawerOpen &&
        !state.inspectorTemporarilyHidden &&
        (!state.overlaysDismissed || !inspectorOccludesGrid);
    const backdropVisible = drawerVisible && inspectorOccludesGrid;

    return {
        overlaysVisible: hudVisible || drawerVisible || backdropVisible,
        hudVisible,
        drawerVisible,
        backdropVisible,
    };
}

export function buildDrawerToggleState(state: AppState): DrawerToggleState {
    const overlayVisibility = buildOverlayVisibilityState(state);
    const savedInspectorOpen = Boolean(state.drawerOpen);
    const hudVisible = Boolean(overlayVisibility.hudVisible);
    const drawerVisible = Boolean(overlayVisibility.drawerVisible);

    if (hudVisible && drawerVisible) {
        return {
            drawerToggleLabel: "Hide Inspector",
            drawerToggleTitle: "Hide the overlay inspector.",
        };
    }
    if (hudVisible && !drawerVisible) {
        return {
            drawerToggleLabel: "Show Inspector",
            drawerToggleTitle: "Show the overlay inspector.",
        };
    }
    if (!hudVisible && drawerVisible) {
        return {
            drawerToggleLabel: "Show HUD",
            drawerToggleTitle: "Restore the canvas HUD.",
        };
    }
    if (savedInspectorOpen) {
        return {
            drawerToggleLabel: "Show Overlays",
            drawerToggleTitle: "Restore the canvas HUD and overlay inspector.",
        };
    }
    return {
        drawerToggleLabel: "Show HUD",
        drawerToggleTitle: "Restore the canvas HUD.",
    };
}

export function buildQuickStartHintState(
    state: AppState,
    activeRule: RuleDefinition | null,
): QuickStartHintState {
    const patternStatusText =
        state.blockingActivityVisible && state.blockingActivityMessage
            ? state.blockingActivityMessage
            : (state.patternStatus?.message ?? "");
    const shouldShow =
        !state.firstRunHintDismissed &&
        !state.isRunning &&
        !state.overlayRunPending &&
        Number(state.generation) === 0 &&
        !hasLiveCells(state) &&
        matchesDefaultTopologySpec(state) &&
        String(activeRule?.name || "") === "conway" &&
        patternStatusText === "";

    return {
        quickStartHintText: "Or click the grid to paint.",
        quickStartHintVisible: shouldShow,
    };
}

export function resolveViewportSizingState(state: AppState): ViewportSizingState {
    const usesPatchDepth = topologyUsesPatchDepth(state.topologySpec);
    const tilingFamily = state.topologySpec?.tiling_family;
    const patchDepthMax = usesPatchDepth
        ? maxPatchDepthForTilingFamily(tilingFamily, { unsafe: state.unsafeSizingEnabled })
        : MAX_PATCH_DEPTH;
    const patchDepthMin = usesPatchDepth
        ? minPatchDepthForTilingFamily(tilingFamily, { unsafe: state.unsafeSizingEnabled })
        : MIN_PATCH_DEPTH;
    const cellSizeMin = usesPatchDepth
        ? MIN_CELL_SIZE
        : minCellSizeForTilingFamily(tilingFamily, { unsafe: state.unsafeSizingEnabled });
    const cellSizeMax = usesPatchDepth
        ? MAX_CELL_SIZE
        : maxCellSizeForTilingFamily(tilingFamily, { unsafe: state.unsafeSizingEnabled });
    const cellSize = Number.isFinite(state.cellSize)
        ? state.cellSize
        : defaultCellSizeForTilingFamily(tilingFamily);
    const patchDepth =
        typeof state.pendingPatchDepth === "number" && Number.isFinite(state.pendingPatchDepth)
            ? state.pendingPatchDepth
            : Number.isFinite(state.patchDepth)
              ? state.patchDepth
              : defaultPatchDepthForTilingFamily(tilingFamily);
    const tileCount = Array.isArray(state.topology?.cells) ? state.topology.cells.length : 0;
    const previewActive = Boolean(
        state.previewTopology &&
        state.previewTopologyRevision &&
        state.previewTopologyRevision === state.topologyRevision,
    );
    const width = previewActive
        ? Number(state.previewTopology?.topology_spec?.width) || 0
        : (state.width ?? 0);
    const height = previewActive
        ? Number(state.previewTopology?.topology_spec?.height) || 0
        : (state.height ?? 0);

    return {
        usesPatchDepth,
        cellSize,
        cellSizeMin,
        cellSizeMax,
        patchDepth,
        patchDepthMin,
        patchDepthMax,
        gridSizeText: usesPatchDepth
            ? `Depth ${patchDepth} • ${tileCount} tiles`
            : `${width} x ${height}`,
    };
}

export function buildCellSizeViewState(
    cellSize: number,
    cellSizeMin = MIN_CELL_SIZE,
    cellSizeMax = MAX_CELL_SIZE,
): {
    cellSizeVisible: boolean;
    cellSizeVisibleTopBar: boolean;
    cellSizeValue: string;
    cellSizeLabel: string;
    cellSizeMin: string;
    cellSizeMax: string;
} {
    return {
        cellSizeVisible: true,
        cellSizeVisibleTopBar: true,
        cellSizeValue: String(cellSize),
        cellSizeLabel: `${cellSize}px`,
        cellSizeMin: String(cellSizeMin),
        cellSizeMax: String(cellSizeMax),
    };
}

export function buildPatchDepthViewState(
    patchDepth: number,
    patchDepthMax = MAX_PATCH_DEPTH,
    patchDepthMin = MIN_PATCH_DEPTH,
): {
    patchDepthVisible: boolean;
    patchDepthVisibleTopBar: boolean;
    patchDepthValue: string;
    patchDepthLabel: string;
    patchDepthMin: string;
    patchDepthMax: string;
} {
    return {
        patchDepthVisible: true,
        patchDepthVisibleTopBar: true,
        patchDepthValue: String(patchDepth),
        patchDepthLabel: `Depth ${patchDepth}`,
        patchDepthMin: String(patchDepthMin),
        patchDepthMax: String(patchDepthMax),
    };
}

export function buildHiddenCellSizeViewState(): {
    cellSizeVisible: boolean;
    cellSizeVisibleTopBar: boolean;
    cellSizeValue: string;
    cellSizeLabel: string;
    cellSizeMin: string;
    cellSizeMax: string;
} {
    return {
        cellSizeVisible: false,
        cellSizeVisibleTopBar: false,
        cellSizeValue: String(DEFAULT_CELL_SIZE),
        cellSizeLabel: `${DEFAULT_CELL_SIZE}px`,
        cellSizeMin: String(MIN_CELL_SIZE),
        cellSizeMax: String(MAX_CELL_SIZE),
    };
}

export function buildHiddenPatchDepthViewState(): {
    patchDepthVisible: boolean;
    patchDepthVisibleTopBar: boolean;
    patchDepthValue: string;
    patchDepthLabel: string;
    patchDepthMin: string;
    patchDepthMax: string;
} {
    return {
        patchDepthVisible: false,
        patchDepthVisibleTopBar: false,
        patchDepthValue: String(DEFAULT_PATCH_DEPTH),
        patchDepthLabel: `Depth ${DEFAULT_PATCH_DEPTH}`,
        patchDepthMin: String(MIN_PATCH_DEPTH),
        patchDepthMax: String(MAX_PATCH_DEPTH),
    };
}

export {
    DEFAULT_BRUSH_SIZE,
    EDITOR_SHORTCUT_HINT,
    MAX_CELL_SIZE,
    MAX_PATCH_DEPTH,
    MIN_CELL_SIZE,
    MIN_PATCH_DEPTH,
};
