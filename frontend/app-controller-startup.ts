import { hydrateAppController } from "./app-controller-hydration.js";
import { createAppControllerServices } from "./app-controller-services.js";
import { wireAppController } from "./app-controller-wiring.js";
import type { AppControllerStartupResult, AppControllerSync } from "./types/controller-app.js";
import type { PostControlFunction, SetCellRequestFunction, SetCellsRequestFunction, ToggleCellRequestFunction } from "./types/controller-api.js";
import type { MutationRunner } from "./types/controller-runtime.js";
import type { ConfigSyncController, UiSessionController } from "./types/controller-sync-session.js";
import type { AppView, GridView } from "./types/controller-view.js";
import type { DomElements } from "./types/dom.js";
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
    const services = createAppControllerServices({
        state,
        elements,
        mutationRunner,
        appView,
        onError,
        postControlFn,
        sync,
    });
    onConfigSyncController(services.configSyncController);
    onUiSessionController(services.uiSessionController);

    const { interactions, viewportController, controlActions } = wireAppController({
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
    });

    await hydrateAppController({
        elements,
        appView,
        sync,
        uiSessionController: services.uiSessionController,
        interactions,
        viewportController,
        controlActions,
    });

    return {
        interactions,
        viewportController,
        configSyncController: services.configSyncController,
        uiSessionController: services.uiSessionController,
        controlActions,
    };
}
