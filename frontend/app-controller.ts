import {
    fetchRules,
    fetchState,
    fetchTopology,
    postControl,
    setCellRequest,
    setCellsRequest,
    toggleCellRequest,
} from "./api.js";
import { createAppControllerBootstrap } from "./app-controller-bootstrap.js";
import { createAppControllerSync } from "./app-controller-sync.js";
import { initializeAppController } from "./app-controller-startup.js";
import { createConfigSyncController } from "./config-sync-controller.js";
import { createInteractionController } from "./interactions.js";
import { createSimulationMutations } from "./interactions/simulation-mutations.js";
import { createMutationRunner } from "./mutation-runner.js";
import { createAppActions } from "./app-actions.js";
import { createUiSessionController } from "./ui-session-controller.js";
import { createUiSessionStorage } from "./ui-session.js";
import { createViewportController } from "./viewport-controller.js";
import { createSimulationReconciler } from "./simulation-reconciler.js";
import type { AppActionSet } from "./types/actions.js";
import type {
    AppController,
    CreateAppControllerOptions,
    ConfigSyncController,
    InteractionController,
    UiSessionController,
    ViewportController,
} from "./types/controller.js";

export function createAppController({
    elements,
    gridView,
    onError = (error: unknown) => console.error(error),
}: CreateAppControllerOptions): AppController {
    let interactions: InteractionController | null = null;
    let viewportController: ViewportController | null = null;
    let configSyncController: ConfigSyncController | null = null;
    let uiSessionController: UiSessionController | null = null;
    let controlActions: AppActionSet | null = null;
    const controllerRefs = {
        configSyncController: null as ConfigSyncController | null,
        uiSessionController: null as UiSessionController | null,
    };
    const bootstrap = createAppControllerBootstrap({
        elements,
        gridView,
        getSyncState: () => (
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
                }
        ),
    });
    const { state, mutationRunner, appView } = bootstrap;
    const sync = createAppControllerSync({
        state,
        appView,
        onError,
        fetchRulesFn: fetchRules,
        fetchStateFn: fetchState,
        fetchTopologyFn: fetchTopology,
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
            postControlFn: postControl,
            toggleCellRequestFn: toggleCellRequest,
            setCellRequestFn: setCellRequest,
            setCellsRequestFn: setCellsRequest,
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

    return {
        init,
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
