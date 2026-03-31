import { createMutationRunner } from "./mutation-runner.js";
import { createAppView } from "./app-view.js";
import { createAppState } from "./state/simulation-state.js";
import { currentDimensions } from "./state/selectors.js";
import type { AppControllerBootstrapResult } from "./types/controller-app.js";
import type { ConfigSyncViewState } from "./types/controller-sync-session.js";
import type { AppView, GridView, InteractionController, ViewportControllerDependencies } from "./types/controller-view.js";
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

export function createAppControllerBootstrap({
    elements,
    gridView,
    getSyncState = () => EMPTY_SYNC_STATE,
}: {
    elements: DomElements;
    gridView: GridView | null;
    getSyncState?: () => ConfigSyncViewState;
}): AppControllerBootstrapResult {
    const state = createAppState();
    const mutationRunner = createMutationRunner();
    const appView: AppView = createAppView({
        state,
        elements,
        gridView,
        getSyncState,
    });
    return {
        state,
        mutationRunner,
        appView,
    };
}

export function createViewportControllerDependencies({
    state,
    elements,
    interactions,
    appView,
    collectConfig,
    sameDimensions,
}: {
    state: AppState;
    elements: DomElements;
    interactions: InteractionController;
    appView: AppView;
    collectConfig: (elements: DomElements) => { speed: number; rule: string };
    sameDimensions: ViewportControllerDependencies["sameDimensions"];
}): ViewportControllerDependencies {
    return {
        getCurrentDimensions: () => currentDimensions(state),
        getViewportDimensions: (geometry, ruleName, cellSize) => appView.viewportDimensionsFor(geometry, ruleName, cellSize),
        collectConfig: () => collectConfig(elements),
        applyPreview: (dimensions) => appView.applyViewportPreview(dimensions),
        sendControl: (path, body, options = {}) => interactions.sendControl(path, body, options),
        sameDimensions,
    };
}
