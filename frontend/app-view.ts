import { buildControlsViewModel } from "./controls-model.js";
import { getGeometryAdapter } from "./geometry/registry.js";
import { applyOverlayIntent, OVERLAY_INTENT_LAYOUT_OCCLUSION_CHANGED } from "./overlay-policy.js";
import { normalizeRuleDimensions } from "./rule-constraints.js";
import {
    clearViewportPreview,
    currentTopologyVariantKey,
    setViewportPreview,
} from "./state/simulation-state.js";
import { setRenderCellSize } from "./state/sizing-state.js";
import {
    currentDimensions,
    topologyRenderPayload,
} from "./state/selectors.js";
import { topologyCellStatesById } from "./topology.js";
import { currentTheme } from "./theme.js";
import { DEFAULT_GRID_DIMENSIONS, computeViewportGridSize } from "./layout.js";
import { renderControls } from "./controls-view.js";
import type {
    AppView,
    ConfigSyncViewState,
    GridView,
    ViewportDimensions,
} from "./types/controller.js";
import type { DomElements } from "./types/dom.js";
import type { AppState } from "./types/state.js";

const EMPTY_SYNC_STATE: ConfigSyncViewState = {
    pendingRuleName: null,
    syncingRuleName: null,
    pendingSpeed: null,
    syncingSpeed: null,
    isSyncing: false,
    hasPendingRuleSync: false,
    hasPendingSpeedSync: false,
    shouldLockRule: false,
    shouldLockSpeed: false,
};

interface FitRenderCellSizeAdapter {
    fitRenderCellSize?: (options: {
        viewportWidth: number;
        viewportHeight: number;
        width: number;
        height: number;
        topology: AppState["topology"];
        fallbackCellSize: number;
    }) => number;
}

interface PreviewResult {
    applied?: boolean;
    renderGrid?: boolean;
}

interface ViewportPreviewAdapter {
    applyViewportPreview: (options: {
        state: AppState;
        dimensions: ViewportDimensions;
        currentTopology: AppState["topology"];
        currentCellStates: number[];
        buildPreviewCellStatesById: typeof topologyCellStatesById;
        setViewportPreview: typeof setViewportPreview;
        clearViewportPreview: typeof clearViewportPreview;
    }) => PreviewResult | null | undefined;
}

export function createAppView({
    state,
    elements,
    gridView,
    getSyncState = () => EMPTY_SYNC_STATE,
}: {
    state: AppState;
    elements: DomElements;
    gridView: GridView | null;
    getSyncState?: () => ConfigSyncViewState;
}): AppView {
    function syncInspectorOcclusion() {
        const mainStage = elements.mainStage;
        const grid = elements.grid;
        const controlDrawer = elements.controlDrawer;

        if (!mainStage || !grid || !controlDrawer) {
            applyOverlayIntent(state, OVERLAY_INTENT_LAYOUT_OCCLUSION_CHANGED, {
                inspectorOccludesGrid: true,
            });
            return;
        }

        const stageRect = mainStage.getBoundingClientRect();
        const gridRect = grid.getBoundingClientRect();
        const drawerRect = controlDrawer.getBoundingClientRect();
        const drawerWidth = drawerRect.width;

        if (stageRect.width <= 0 || gridRect.width <= 0 || drawerWidth <= 0) {
            applyOverlayIntent(state, OVERLAY_INTENT_LAYOUT_OCCLUSION_CHANGED, {
                inspectorOccludesGrid: true,
            });
            return;
        }

        const availableRightGutter = Math.max(0, stageRect.right - gridRect.right);
        applyOverlayIntent(state, OVERLAY_INTENT_LAYOUT_OCCLUSION_CHANGED, {
            inspectorOccludesGrid: drawerWidth > availableRightGutter + 2,
        });
    }

    function resolveViewportSize(): ViewportDimensions {
        return {
            width: Math.max(0, elements.gridViewport?.clientWidth || 0),
            height: Math.max(0, elements.gridViewport?.clientHeight || 0),
        };
    }

    function fittedRenderCellSize(geometry = currentTopologyVariantKey(state)): number {
        const adapter = getGeometryAdapter(geometry) as FitRenderCellSizeAdapter;
        const viewport = resolveViewportSize();
        if (viewport.width === 0 || viewport.height === 0 || typeof adapter.fitRenderCellSize !== "function") {
            return state.renderCellSize || state.cellSize;
        }
        const dimensions = currentDimensions(state);
        const width = dimensions.width;
        const height = dimensions.height;
        return adapter.fitRenderCellSize({
            viewportWidth: viewport.width,
            viewportHeight: viewport.height,
            width,
            height,
            topology: state.topology,
            fallbackCellSize: state.renderCellSize || state.cellSize,
        });
    }

    function renderGrid(): void {
        if (!gridView?.render) {
            return;
        }
        const topologyVariantKey = currentTopologyVariantKey(state);
        setRenderCellSize(state, fittedRenderCellSize());
        gridView.render(
            topologyRenderPayload(state),
            state.renderCellSize,
            state.activeRule?.states ?? [],
            topologyVariantKey,
        );
    }

    function renderControlsPanel(): void {
        syncInspectorOcclusion();
        renderControls(
            elements,
            buildControlsViewModel({
                state,
                syncState: getSyncState(),
                theme: currentTheme(),
                selectionInspectorSource: {
                    selectedCells: gridView?.getSelectedCells ? gridView.getSelectedCells() : [],
                },
            }),
        );
    }

    function renderAll(): void {
        renderGrid();
        renderControlsPanel();
    }

    function viewportDimensionsFor(
        geometry = currentTopologyVariantKey(state),
        ruleName = state.activeRule?.name,
        cellSizeOverride = state.cellSize,
    ): ViewportDimensions {
        const fallback = currentDimensions(state);
        const dimensions = computeViewportGridSize(
            elements.gridViewport,
            cellSizeOverride,
            fallback.width > 0 && fallback.height > 0 ? fallback : DEFAULT_GRID_DIMENSIONS,
            geometry,
        );
        return normalizeRuleDimensions(ruleName, dimensions);
    }

    function applyViewportPreview(dimensions: ViewportDimensions): void {
        const adapter = getGeometryAdapter(currentTopologyVariantKey(state)) as ViewportPreviewAdapter;
        const previewResult = adapter.applyViewportPreview({
            state,
            dimensions,
            currentTopology: state.topology,
            currentCellStates: state.cellStates,
            buildPreviewCellStatesById: topologyCellStatesById,
            setViewportPreview,
            clearViewportPreview,
        });
        if (!previewResult?.applied) {
            return;
        }
        if (previewResult.renderGrid) {
            renderGrid();
        }
        renderControlsPanel();
    }

    return {
        renderAll,
        renderGrid,
        renderControlsPanel,
        viewportDimensionsFor,
        applyViewportPreview,
    };
}
