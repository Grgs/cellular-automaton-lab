import { clearEditMode } from "../../state/overlay-state.js";
import { clearPatternStatus, dismissFirstRunHint } from "../../state/overlay-state.js";
import { RULE_SELECTION_ORIGIN_DEFAULT, RULE_SELECTION_ORIGIN_USER } from "../../state/constants.js";
import { currentRuleSelectionOrigin, setRuleSelectionOrigin } from "../../state/simulation-state.js";
import { applyOverlayIntent } from "../../overlay-policy.js";
import {
    describeTopologySpec,
    topologyUsesPatchDepth,
} from "../../topology-catalog.js";
import {
    rememberPatchDepthForTilingFamily,
} from "../../state/sizing-state.js";
import type { SimulationSnapshot } from "../../types/domain.js";
import type { AppState } from "../../types/state.js";
import type { UiSessionController } from "../../types/controller.js";

interface CreateSimulationRuntimeEffectsOptions {
    state: AppState;
    uiSessionController: UiSessionController;
    renderControlPanel: () => void;
    setRuleSelectionOriginFn?: typeof setRuleSelectionOrigin;
    dismissFirstRunHintFn?: typeof dismissFirstRunHint;
    clearPatternStatusFn?: typeof clearPatternStatus;
    applyOverlayIntentFn?: typeof applyOverlayIntent;
    clearEditModeFn?: typeof clearEditMode;
}

export interface SimulationRuntimeEffects {
    dismissHintsAndStatus(): void;
    applyOverlayIntentAndRender(intent: Parameters<typeof applyOverlayIntent>[1]): boolean;
    preserveRuleOnTopologySelection(): boolean;
    reconcileTopologySelectionRuleOrigin(
        simulationState: SimulationSnapshot | null | void,
        requestedRuleName?: string | null,
    ): void;
    persistAppliedPatchDepth(simulationState: SimulationSnapshot | null | void): void;
    resetRuleSelectionOrigin(): void;
}

export function createSimulationRuntimeEffects({
    state,
    uiSessionController,
    renderControlPanel,
    setRuleSelectionOriginFn = setRuleSelectionOrigin,
    dismissFirstRunHintFn = dismissFirstRunHint,
    clearPatternStatusFn = clearPatternStatus,
    applyOverlayIntentFn = applyOverlayIntent,
    clearEditModeFn = clearEditMode,
}: CreateSimulationRuntimeEffectsOptions): SimulationRuntimeEffects {
    function clearSharedStatus(): boolean {
        if (state.patternStatus?.message) {
            clearPatternStatusFn(state);
            return true;
        }
        return false;
    }

    function dismissHintsAndStatus(): void {
        dismissFirstRunHintFn(state);
        clearSharedStatus();
    }

    function applyOverlayIntentAndRender(intent: Parameters<typeof applyOverlayIntent>[1]): boolean {
        const changed = applyOverlayIntentFn(state, intent);
        const editChanged = clearEditModeFn(state);
        if (changed || editChanged) {
            renderControlPanel();
        }
        return changed || editChanged;
    }

    function preserveRuleOnTopologySelection(): boolean {
        return currentRuleSelectionOrigin(state) === RULE_SELECTION_ORIGIN_USER;
    }

    function reconcileTopologySelectionRuleOrigin(
        simulationState: SimulationSnapshot | null | void,
        requestedRuleName: string | null = null,
    ): void {
        if (requestedRuleName && simulationState?.rule?.name === requestedRuleName) {
            setRuleSelectionOriginFn(state, RULE_SELECTION_ORIGIN_USER);
            return;
        }
        setRuleSelectionOriginFn(state, RULE_SELECTION_ORIGIN_DEFAULT);
    }

    function persistAppliedPatchDepth(simulationState: SimulationSnapshot | null | void): void {
        const topologySpec = describeTopologySpec(
            simulationState?.topology_spec || state.topologySpec,
        );
        if (!topologyUsesPatchDepth(topologySpec)) {
            return;
        }
        const patchDepth = Number(topologySpec.patch_depth) || 0;
        rememberPatchDepthForTilingFamily(state, topologySpec.tiling_family, patchDepth);
        uiSessionController.persistPatchDepthForTilingFamily?.(topologySpec.tiling_family, patchDepth);
    }

    function resetRuleSelectionOrigin(): void {
        setRuleSelectionOriginFn(state, RULE_SELECTION_ORIGIN_DEFAULT);
    }

    return {
        dismissHintsAndStatus,
        applyOverlayIntentAndRender,
        preserveRuleOnTopologySelection,
        reconcileTopologySelectionRuleOrigin,
        persistAppliedPatchDepth,
        resetRuleSelectionOrigin,
    };
}
