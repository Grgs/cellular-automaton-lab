import { collectConfig } from "./controls-model.js";
import { createAppActions } from "./app-actions.js";
import { createInteractionController } from "./interactions.js";
import { sameDimensions } from "./layout.js";
import { applyOverlayIntent, OVERLAY_INTENT_WORKSPACE_EMPTY_CLICK } from "./overlay-policy.js";
import { createViewportController } from "./viewport-controller.js";
import { createSurfaceCellResolver } from "./cell-resolution.js";
import { currentPaintState } from "./state/selectors.js";
import { createViewportControllerDependencies } from "./app-controller-bootstrap.js";
import type { AppControllerServicePhaseResult } from "./app-controller-services.js";
import type { PostControlFunction, SetCellRequestFunction, SetCellsRequestFunction, ToggleCellRequestFunction } from "./types/controller-api.js";
import type { MutationRunner } from "./types/controller-runtime.js";
import type { AppControllerSync, AppControllerStartupResult } from "./types/controller-app.js";
import type { AppView, GridView } from "./types/controller-view.js";
import type { DomElements } from "./types/dom.js";
import type { PreviewPaintCells } from "./types/editor.js";
import type { AppState } from "./types/state.js";

export function wireAppController({
    state,
    elements,
    gridView,
    mutationRunner,
    appView,
    onError,
    postControlFn,
    toggleCellRequestFn,
    setCellRequestFn,
    setCellsRequestFn,
    sync,
    services,
}: {
    state: AppState;
    elements: DomElements;
    gridView: GridView;
    mutationRunner: MutationRunner;
    appView: AppView;
    onError: (error: unknown) => void;
    postControlFn: PostControlFunction;
    toggleCellRequestFn: ToggleCellRequestFunction;
    setCellRequestFn: SetCellRequestFunction;
    setCellsRequestFn: SetCellsRequestFunction;
    sync: AppControllerSync;
    services: AppControllerServicePhaseResult;
}): Pick<AppControllerStartupResult, "interactions" | "viewportController" | "controlActions"> {
    const interactions = createInteractionController({
        surfaceElement: elements.grid,
        state,
        resolveCellFromEvent: createSurfaceCellResolver({ state, gridView }),
        previewPaintCells: (cells: PreviewPaintCells) => gridView.setPreviewCells(cells),
        clearPreview: () => gridView.clearPreview(),
        setHoveredCell: (cell) => gridView.setHoveredCell(cell),
        setSelectedCells: (cells) => gridView.setSelectedCells(cells),
        getSelectedCells: () => gridView.getSelectedCells(),
        setGestureOutline: (cells, tone) => gridView.setGestureOutline(cells, tone),
        flashGestureOutline: (cells, tone, durationMs) => gridView.flashGestureOutline(cells, tone, durationMs),
        clearGestureOutline: () => gridView.clearGestureOutline(),
        mutationRunner,
        simulationMutations: services.getSimulationMutations(),
        onError,
        applySimulationState: sync.applySimulationState,
        refreshState: sync.refreshState,
        toggleCellRequest: toggleCellRequestFn,
        setCellRequest: setCellRequestFn,
        setCellsRequest: setCellsRequestFn,
        postControl: postControlFn,
        getPaintState: () => currentPaintState(state),
        getEditorTool: () => state.selectedEditorTool,
        getBrushSize: () => state.brushSize,
        dismissOverlays: () => {
            const changed = applyOverlayIntent(state, OVERLAY_INTENT_WORKSPACE_EMPTY_CLICK);
            if (changed) {
                appView.renderControlsPanel();
            }
            return Promise.resolve(changed);
        },
        renderControlPanel: appView.renderControlsPanel,
    });

    const viewportController = createViewportController(
        createViewportControllerDependencies({
            state,
            elements,
            interactions,
            appView,
            collectConfig,
            sameDimensions,
        }),
    );

    const controlActions = createAppActions({
        state,
        elements,
        interactions,
        viewportController,
        configSyncController: services.configSyncController,
        uiSessionController: services.uiSessionController,
        renderCurrentGrid: appView.renderGrid,
        renderControlPanel: appView.renderControlsPanel,
        applySimulationState: sync.applySimulationState,
        getViewportDimensions: (geometry: string, ruleName: string | null, cellSize: number) => (
            appView.viewportDimensionsFor(geometry, ruleName, cellSize)
        ),
        postControlFn,
        setCellsRequestFn,
        onError,
        refreshState: sync.refreshState,
        simulationMutations: services.getSimulationMutations(),
    });

    return {
        interactions,
        viewportController,
        controlActions,
    };
}
