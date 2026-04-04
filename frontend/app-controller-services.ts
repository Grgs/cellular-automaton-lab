import { createConfigSyncController } from "./config-sync-controller.js";
import { createSimulationMutations } from "./interactions/simulation-mutations.js";
import { createUiSessionController } from "./ui-session-controller.js";
import { createUiSessionStorage } from "./ui-session.js";
import type { PostControlFunction } from "./types/controller-api.js";
import type { MutationRunner, SimulationMutations } from "./types/controller-runtime.js";
import type { ConfigSyncController, UiSessionController } from "./types/controller-sync-session.js";
import type { AppControllerSync } from "./types/controller-app.js";
import type { AppView } from "./types/controller-view.js";
import type { DomElements } from "./types/dom.js";
import type { AppState } from "./types/state.js";

export interface AppControllerServicePhaseResult {
    configSyncController: ConfigSyncController;
    uiSessionController: UiSessionController;
    getSimulationMutations: () => SimulationMutations;
}

export function createAppControllerServices({
    state,
    elements,
    mutationRunner,
    appView,
    onError,
    postControlFn,
    sync,
}: {
    state: AppState;
    elements: DomElements;
    mutationRunner: MutationRunner;
    appView: AppView;
    onError: (error: unknown) => void;
    postControlFn: PostControlFunction;
    sync: AppControllerSync;
}): AppControllerServicePhaseResult {
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

    return {
        configSyncController,
        uiSessionController,
        getSimulationMutations,
    };
}
