import { createHttpSimulationBackend } from "./api.js";
import { createAppControllerBootstrap } from "./app-controller-bootstrap.js";
import { createAppControllerSync } from "./app-controller-sync.js";
import { initializeAppController } from "./app-controller-startup.js";
import type { AppActionSet } from "./types/actions.js";
import type { AppController, CreateAppControllerOptions } from "./types/controller-app.js";
import type { ConfigSyncController, UiSessionController } from "./types/controller-sync-session.js";
import type { InteractionController, ViewportController } from "./types/controller-view.js";

export function createAppController({
    elements,
    gridView,
    backend = createHttpSimulationBackend(),
    onError = (error: unknown) => console.error(error),
}: CreateAppControllerOptions): AppController {
    let interactions: InteractionController | null = null;
    let viewportController: ViewportController | null = null;
    let configSyncController: ConfigSyncController | null = null;
    let uiSessionController: UiSessionController | null = null;
    let controlActions: AppActionSet | null = null;
    let disposed = false;
    const controllerRefs = {
        configSyncController: null as ConfigSyncController | null,
        uiSessionController: null as UiSessionController | null,
    };
    const bootstrap = createAppControllerBootstrap({
        elements,
        gridView,
        getSyncState: () =>
            controllerRefs.configSyncController
                ? controllerRefs.configSyncController.getViewState()
                : {
                      pendingRuleName: null,
                      syncingRuleName: null,
                      pendingSpeed: null,
                      syncingSpeed: null,
                      isSyncing: false,
                      hasPendingRuleSync: false,
                      hasPendingSpeedSync: false,
                      shouldLockRule: false,
                      shouldLockSpeed: false,
                  },
    });
    const { state, mutationRunner, appView } = bootstrap;
    const sync = createAppControllerSync({
        state,
        appView,
        onError,
        fetchRulesFn: () => backend.getRules(),
        fetchStateFn: () => backend.getState(),
        getConfigSyncController: () => controllerRefs.configSyncController,
        getUiSessionController: () => controllerRefs.uiSessionController,
        getRefreshState: () => sync.refreshState,
    });

    async function init(): Promise<void> {
        ({
            interactions,
            viewportController,
            configSyncController,
            uiSessionController,
            controlActions,
        } = await initializeAppController({
            state,
            elements,
            gridView,
            mutationRunner,
            appView,
            onError,
            postControlFn: backend.postControl.bind(backend),
            toggleCellRequestFn: backend.toggleCell.bind(backend),
            setCellRequestFn: backend.setCell.bind(backend),
            setCellsRequestFn: backend.setCells.bind(backend),
            sync,
            onConfigSyncController: (nextConfigSyncController) => {
                controllerRefs.configSyncController = nextConfigSyncController;
                configSyncController = nextConfigSyncController;
            },
            onUiSessionController: (nextUiSessionController) => {
                controllerRefs.uiSessionController = nextUiSessionController;
                uiSessionController = nextUiSessionController;
            },
        }));
    }

    function dispose(): void {
        if (disposed) {
            return;
        }
        disposed = true;
        viewportController?.dispose();
        configSyncController?.dispose();
        mutationRunner.dispose();
        void Promise.resolve(backend.dispose()).catch(onError);
        interactions = null;
        viewportController = null;
        configSyncController = null;
        uiSessionController = null;
        controlActions = null;
        controllerRefs.configSyncController = null;
        controllerRefs.uiSessionController = null;
    }

    return {
        init,
        dispose,
        refreshState: sync.refreshState,
        loadRules: sync.loadRules,
        applySimulationState: sync.applySimulationState,
        applyCellSize: (nextCellSize) => controlActions?.setCellSize?.(nextCellSize),
        applyPaintState: (nextPaintState) => controlActions?.setPaintState(nextPaintState),
        getState: () => state,
        getInteractions: () => interactions,
        getViewportController: () => viewportController,
        getConfigSyncController: () => configSyncController,
        getUiSessionController: () => uiSessionController,
    };
}
