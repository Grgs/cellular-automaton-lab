import { bindControls } from "./controls-bindings.js";
import { collectConfig } from "./controls-model.js";
import { createAppActions } from "./app-actions.js";
import { createConfigSyncController } from "./config-sync-controller.js";
import { createInteractionController } from "./interactions.js";
import { createSimulationMutations } from "./interactions/simulation-mutations.js";
import { sameDimensions } from "./layout.js";
import { applyOverlayIntent, OVERLAY_INTENT_WORKSPACE_EMPTY_CLICK } from "./overlay-policy.js";
import { createUiSessionController } from "./ui-session-controller.js";
import { createUiSessionStorage } from "./ui-session.js";
import { createViewportController } from "./viewport-controller.js";
import { createSurfaceCellResolver } from "./cell-resolution.js";
import { currentPaintState } from "./state/selectors.js";
import { createViewportControllerDependencies } from "./app-controller-bootstrap.js";
import type {
    AppControllerStartupResult,
    AppControllerSync,
    AppView,
    ConfigSyncController,
    GridView,
    InteractionController,
    MutationRunner,
    PostControlFunction,
    SetCellRequestFunction,
    SetCellsRequestFunction,
    SimulationMutations,
    ToggleCellRequestFunction,
    UiSessionController,
    ViewportController,
} from "./types/controller.js";
import type { DomElements } from "./types/dom.js";
import type { PreviewPaintCells } from "./types/editor.js";
import type { AppState } from "./types/state.js";

export async function initializeAppController({
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
    onConfigSyncController = () => {},
    onUiSessionController = () => {},
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
    onConfigSyncController?: (controller: ConfigSyncController) => void;
    onUiSessionController?: (controller: UiSessionController) => void;
}): Promise<AppControllerStartupResult> {
    let simulationMutations: SimulationMutations | null = null;
    const getSimulationMutations = (): SimulationMutations => {
        if (!simulationMutations) {
            simulationMutations = createSimulationMutations({
                state,
                mutationRunner,
                onError,
                applySimulationState: sync.applySimulationState,
                resolveSimulationState: sync.resolveSimulationState,
                refreshState: sync.refreshState,
                renderControlPanel: appView.renderControlsPanel,
            });
        }
        return simulationMutations;
    };

    const uiSessionController = createUiSessionController({
        state,
        elements,
        createUiSessionStorage,
    });
    onUiSessionController(uiSessionController);
    uiSessionController.restoreInitialCellSize();
    uiSessionController.restoreDrawerState();

    const configSyncController = createConfigSyncController({
        state,
        mutationRunner,
        simulationMutations: getSimulationMutations(),
        postControl: postControlFn,
        onError,
        onSyncStateChanged: appView.renderControlsPanel,
        applySimulationState: sync.applySimulationState,
        refreshState: sync.refreshState,
    });
    onConfigSyncController(configSyncController);

    const interactions = createInteractionController({
        surfaceElement: elements.grid,
        state,
        resolveCellFromEvent: createSurfaceCellResolver({ state, gridView }),
        previewPaintCells: (cells: PreviewPaintCells) => gridView.setPreviewCells(cells),
        clearPreview: () => gridView.clearPreview(),
        mutationRunner,
        simulationMutations: getSimulationMutations(),
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
        configSyncController,
        uiSessionController,
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
        simulationMutations: getSimulationMutations(),
    });

    await sync.loadRules();
    uiSessionController.restoreDisclosures();
    bindControls(elements, controlActions);
    appView.renderControlsPanel();
    await sync.refreshState();
    interactions.bindGridInteractions();
    viewportController.install(elements.gridViewport);

    return {
        interactions,
        viewportController,
        configSyncController,
        uiSessionController,
        controlActions,
    };
}
