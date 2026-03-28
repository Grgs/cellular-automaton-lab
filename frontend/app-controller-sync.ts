import {
    applySimulationSnapshot,
    simulationSnapshotNeedsTopology,
} from "./state/snapshot-reducer.js";
import {
    setEditorRule,
    setRules,
} from "./state/simulation-state.js";
import { syncPolling } from "./state/polling.js";
import { createSimulationReconciler } from "./simulation-reconciler.js";
import { clearEditorHistory, shouldClearHistoryForSimulationUpdate } from "./editor-history.js";
import type {
    AppControllerSync,
    AppView,
    ConfigSyncController,
    FetchRulesFunction,
    FetchStateFunction,
    FetchTopologyFunction,
    UiSessionController,
} from "./types/controller.js";
import type { RulesResponse, SimulationSnapshot } from "./types/domain.js";
import type { AppState } from "./types/state.js";

export function createAppControllerSync({
    state,
    appView,
    onError,
    fetchRulesFn,
    fetchStateFn,
    fetchTopologyFn,
    getConfigSyncController,
    getUiSessionController,
    getRefreshState,
    createSimulationReconcilerFn = createSimulationReconciler,
}: {
    state: AppState;
    appView: AppView;
    onError: (error: unknown) => void;
    fetchRulesFn: FetchRulesFunction;
    fetchStateFn: FetchStateFunction;
    fetchTopologyFn: FetchTopologyFunction;
    getConfigSyncController: () => ConfigSyncController | null;
    getUiSessionController: () => UiSessionController | null;
    getRefreshState: () => (() => Promise<void>);
    createSimulationReconcilerFn?: typeof createSimulationReconciler;
}): AppControllerSync {
    let simulationReconciler: ReturnType<typeof createSimulationReconciler> | null = null;

    function getSimulationReconciler(): ReturnType<typeof createSimulationReconciler> {
        if (!simulationReconciler) {
            simulationReconciler = createSimulationReconcilerFn({
                state,
                getConfigSyncController,
                getUiSessionController,
                getRefreshState,
                applySimulationSnapshot,
                shouldClearHistoryForSimulationUpdate,
                clearEditorHistory,
                setEditorRule,
                syncPolling,
                renderAll: appView.renderAll,
            });
        }
        return simulationReconciler;
    }

    async function resolveSimulationState(simulationState: SimulationSnapshot): Promise<SimulationSnapshot> {
        if (!simulationState.topology && !state.topology) {
            return fetchStateFn();
        }

        if (!simulationSnapshotNeedsTopology(state, simulationState)) {
            return simulationState;
        }

        try {
            const topology = await fetchTopologyFn();
            if (topology?.topology_revision === simulationState.topology_revision) {
                return {
                    ...simulationState,
                    topology: topology ?? undefined,
                };
            }
        } catch (error) {
            onError(error);
        }

        return fetchStateFn();
    }

    function applySimulationState(
        simulationState: SimulationSnapshot,
        { source = "external" }: { source?: string } = {},
    ): void {
        getSimulationReconciler().apply(simulationState, { source });
    }

    async function refreshState(): Promise<void> {
        try {
            const simulationState = await fetchStateFn();
            applySimulationState(simulationState);
        } catch (error) {
            onError(error);
        }
    }

    async function loadRules(): Promise<void> {
        const payload: RulesResponse = await fetchRulesFn();
        setRules(state, payload.rules);
        appView.renderControlsPanel();
    }

    return {
        applySimulationState,
        resolveSimulationState,
        refreshState,
        loadRules,
        getSimulationReconciler,
    };
}
