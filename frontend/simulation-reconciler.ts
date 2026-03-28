import {
    applyOverlayIntent,
    OVERLAY_INTENT_BOARD_REBUILT,
    OVERLAY_INTENT_RUN_STATE_SYNCED,
} from "./overlay-policy.js";
import { clearEditMode } from "./state/overlay-state.js";
import type { SimulationSnapshot, TopologySpec } from "./types/domain.js";
import type { SimulationReconcilerDependencies } from "./types/controller.js";

function topologySpecSignature(topologySpec: Partial<TopologySpec> = {}): string {
    return [
        topologySpec.tiling_family || "",
        topologySpec.adjacency_mode || "edge",
        topologySpec.width ?? "",
        topologySpec.height ?? "",
        topologySpec.patch_depth ?? "",
    ].join("|");
}

export function createSimulationReconciler({
    state,
    getConfigSyncController = () => null,
    getUiSessionController = () => null,
    getRefreshState = () => async () => {},
    applySimulationSnapshot,
    shouldClearHistoryForSimulationUpdate,
    clearEditorHistory,
    setEditorRule,
    syncPolling,
    renderAll,
    clearEditModeFn = clearEditMode,
}: SimulationReconcilerDependencies) {
    function apply(
        simulationState: SimulationSnapshot,
        { source = "external" }: { source?: string } = {},
    ): void {
        const previousRunning = Boolean(state.isRunning);
        const previousTopologySignature = topologySpecSignature(state.topologySpec);
        const previousTopologyRevision = state.topologyRevision;
        const previousOverlaysDismissed = Boolean(state.overlaysDismissed);
        const previousInspectorTemporarilyHidden = Boolean(state.inspectorTemporarilyHidden);
        if (shouldClearHistoryForSimulationUpdate(state, simulationState, source)) {
            clearEditorHistory(state);
        }

        applySimulationSnapshot(state, simulationState);
        const topologyRebuilt = source !== "editor"
            && !state.isRunning
            && (
                state.topologyRevision !== previousTopologyRevision
                || topologySpecSignature(state.topologySpec) !== previousTopologySignature
            );
        if (topologyRebuilt) {
            applyOverlayIntent(state, OVERLAY_INTENT_BOARD_REBUILT);
        } else if (previousRunning !== Boolean(state.isRunning)) {
            // Run-state toggles should not silently clear a prior overlay dismissal.
            state.overlaysDismissed = previousOverlaysDismissed;
            state.inspectorTemporarilyHidden = previousInspectorTemporarilyHidden;
        }
        applyOverlayIntent(state, OVERLAY_INTENT_RUN_STATE_SYNCED);
        if (topologyRebuilt || previousRunning !== Boolean(state.isRunning)) {
            clearEditModeFn(state);
        }

        const configSyncController = getConfigSyncController();
        configSyncController?.reconcile(simulationState);

        if (configSyncController?.shouldAdoptBackendRule() && simulationState.rule) {
            setEditorRule(state, simulationState.rule.name, { resetPaintState: false });
        }

        getUiSessionController()?.restorePaintStateForCurrentRule();
        syncPolling(state, state.isRunning, getRefreshState());
        renderAll();
    }

    return {
        apply,
    };
}
