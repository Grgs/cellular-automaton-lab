import { BLOCKING_ACTIVITY_BUILD_TILING } from "../../blocking-activity.js";
import { OVERLAY_INTENT_BOARD_REBUILT } from "../../overlay-policy.js";
import {
    buildTopologySpecRequest,
    clearPendingPatchDepth,
    normalizePatchDepthForTilingFamily,
    setPendingPatchDepth,
} from "../../state/sizing-state.js";
import { topologyUsesPatchDepth } from "../../topology-catalog.js";
import type {
    BrowserClearTimeout,
    BrowserSetTimeout,
    BrowserTimerId,
    InteractionController,
} from "../../types/controller.js";
import type { SimulationActionRuntime } from "../../types/actions.js";
import type { SimulationSnapshot } from "../../types/domain.js";
import type { AppState } from "../../types/state.js";

interface CreatePatchDepthRuntimeOptions {
    state: AppState;
    interactions: InteractionController;
    renderControlPanel: () => void;
    dismissHintsAndStatus: () => void;
    applyOverlayIntentAndRender: SimulationActionRuntime["applyOverlayIntentAndRender"];
    reconcileTopologySelectionRuleOrigin: (
        simulationState: SimulationSnapshot | null | void,
        requestedRuleName?: string | null,
    ) => void;
    persistAppliedPatchDepth: (simulationState: SimulationSnapshot | null | void) => void;
    clearPendingPatchDepthFn?: typeof clearPendingPatchDepth;
    setPendingPatchDepthFn?: typeof setPendingPatchDepth;
    setTimeoutFn?: BrowserSetTimeout;
    clearTimeoutFn?: BrowserClearTimeout;
    patchDepthDebounceMs?: number;
}

export interface PatchDepthRuntime {
    requestPatchDepth(nextPatchDepth: number, options?: { immediate?: boolean }): Promise<boolean>;
    clearScheduledPatchDepthCommit(options?: { clearPending?: boolean }): void;
}

export function createPatchDepthRuntime({
    state,
    interactions,
    renderControlPanel,
    dismissHintsAndStatus,
    applyOverlayIntentAndRender,
    reconcileTopologySelectionRuleOrigin,
    persistAppliedPatchDepth,
    clearPendingPatchDepthFn = clearPendingPatchDepth,
    setPendingPatchDepthFn = setPendingPatchDepth,
    setTimeoutFn = (callback, delay) => window.setTimeout(callback, delay),
    clearTimeoutFn = (timerId) => window.clearTimeout(timerId),
    patchDepthDebounceMs = 180,
}: CreatePatchDepthRuntimeOptions): PatchDepthRuntime {
    let patchDepthTimer: BrowserTimerId | null = null;
    let inflightPatchDepth: number | null = null;

    function clearScheduledPatchDepthCommit({ clearPending = false }: { clearPending?: boolean } = {}): void {
        if (patchDepthTimer !== null) {
            clearTimeoutFn(patchDepthTimer);
            patchDepthTimer = null;
        }
        if (clearPending) {
            clearPendingPatchDepthFn(state);
        }
    }

    async function commitPendingPatchDepth(): Promise<boolean> {
        const requestedDepth = Number(state.pendingPatchDepth ?? state.patchDepth);
        const targetDepth = normalizePatchDepthForTilingFamily(
            state.topologySpec?.tiling_family,
            Number.isFinite(requestedDepth) ? requestedDepth : Number(state.patchDepth),
            { unsafe: state.unsafeSizingEnabled },
        );
        if (
            !topologyUsesPatchDepth(state.topologySpec)
            || !Number.isFinite(targetDepth)
            || targetDepth === Number(state.patchDepth)
        ) {
            clearPendingPatchDepthFn(state);
            renderControlPanel();
            return false;
        }
        if (inflightPatchDepth !== null) {
            return false;
        }

        dismissHintsAndStatus();
        applyOverlayIntentAndRender(OVERLAY_INTENT_BOARD_REBUILT);
        inflightPatchDepth = targetDepth;
        try {
            const simulationState = await interactions.sendControl(
                "/api/control/reset",
                {
                    topology_spec: buildTopologySpecRequest({
                        ...state.topologySpec,
                        patch_depth: targetDepth,
                    }, state.unsafeSizingEnabled),
                    speed: state.speed,
                    rule: state.activeRule?.name ?? null,
                    randomize: false,
                },
                {
                    blockingActivity: BLOCKING_ACTIVITY_BUILD_TILING,
                },
            );
            persistAppliedPatchDepth(simulationState);
            reconcileTopologySelectionRuleOrigin(simulationState, null);
            return true;
        } finally {
            inflightPatchDepth = null;
            if (
                Number(state.pendingPatchDepth) === targetDepth
                && Number(state.patchDepth) === targetDepth
            ) {
                clearPendingPatchDepthFn(state);
                renderControlPanel();
            } else if (
                Number.isFinite(state.pendingPatchDepth)
                && Number(state.pendingPatchDepth) !== Number(state.patchDepth)
            ) {
                queuePatchDepthCommit({ immediate: true });
            }
        }
    }

    function queuePatchDepthCommit({ immediate = false }: { immediate?: boolean } = {}): void {
        clearScheduledPatchDepthCommit();
        if (immediate) {
            void commitPendingPatchDepth();
            return;
        }
        patchDepthTimer = setTimeoutFn(() => {
            patchDepthTimer = null;
            void commitPendingPatchDepth();
        }, patchDepthDebounceMs);
    }

    function requestPatchDepth(
        nextPatchDepth: number,
        { immediate = false }: { immediate?: boolean } = {},
    ): Promise<boolean> {
        if (!topologyUsesPatchDepth(state.topologySpec)) {
            return Promise.resolve(false);
        }
        setPendingPatchDepthFn(state, nextPatchDepth);
        renderControlPanel();

        if (Number(state.pendingPatchDepth) === Number(state.patchDepth)) {
            clearScheduledPatchDepthCommit({ clearPending: true });
            renderControlPanel();
            return Promise.resolve(false);
        }

        queuePatchDepthCommit({ immediate });
        return Promise.resolve(true);
    }

    return {
        requestPatchDepth,
        clearScheduledPatchDepthCommit,
    };
}
