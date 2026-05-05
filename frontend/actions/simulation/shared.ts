import {
    clearEditMode,
    clearPatternStatus,
    dismissFirstRunHint,
} from "../../state/overlay-state.js";
import {
    clearPendingPatchDepth,
    setCellSize,
    setPatchDepth,
    setPendingPatchDepth,
} from "../../state/sizing-state.js";
import {
    setEditorRule,
    setRuleSelectionOrigin,
    setTopologySpec,
} from "../../state/simulation-state.js";
import { applyOverlayIntent } from "../../overlay-policy.js";
import type { BrowserClearTimeout, BrowserSetTimeout } from "../../types/controller.js";
import type { SimulationActionRuntime } from "../../types/actions.js";
import type { AppState } from "../../types/state.js";
import { createPatchDepthRuntime } from "./patch-depth-runtime.js";
import { createRuleSpeedRuntime } from "./rule-speed-runtime.js";
import { createSimulationRuntimeEffects } from "./runtime-effects.js";
import { createTopologySelectionRuntime } from "./topology-selection-runtime.js";

interface CreateSimulationActionRuntimeOptions {
    state: AppState;
    interactions: SimulationActionRuntime["interactions"];
    viewportController: SimulationActionRuntime["viewportController"];
    configSyncController: SimulationActionRuntime["configSyncController"];
    uiSessionController: SimulationActionRuntime["uiSessionController"];
    renderControlPanel: () => void;
    getViewportDimensions: SimulationActionRuntime["getViewportDimensions"];
    setEditorRuleFn?: typeof setEditorRule;
    setRuleSelectionOriginFn?: typeof setRuleSelectionOrigin;
    setPendingPatchDepthFn?: typeof setPendingPatchDepth;
    clearPendingPatchDepthFn?: typeof clearPendingPatchDepth;
    dismissFirstRunHintFn?: typeof dismissFirstRunHint;
    clearPatternStatusFn?: typeof clearPatternStatus;
    setCellSizeFn?: typeof setCellSize;
    setPatchDepthFn?: typeof setPatchDepth;
    setTimeoutFn?: BrowserSetTimeout;
    clearTimeoutFn?: BrowserClearTimeout;
    patchDepthDebounceMs?: number;
    applyOverlayIntentFn?: typeof applyOverlayIntent;
    clearEditModeFn?: typeof clearEditMode;
}

export function createSimulationActionRuntime({
    state,
    interactions,
    viewportController,
    configSyncController,
    uiSessionController,
    renderControlPanel,
    getViewportDimensions,
    setEditorRuleFn = setEditorRule,
    setRuleSelectionOriginFn = setRuleSelectionOrigin,
    setPendingPatchDepthFn = setPendingPatchDepth,
    clearPendingPatchDepthFn = clearPendingPatchDepth,
    dismissFirstRunHintFn = dismissFirstRunHint,
    clearPatternStatusFn = clearPatternStatus,
    setCellSizeFn = setCellSize,
    setPatchDepthFn = setPatchDepth,
    setTimeoutFn = (callback, delay) => window.setTimeout(callback, delay),
    clearTimeoutFn = (timerId) => window.clearTimeout(timerId),
    patchDepthDebounceMs = 180,
    applyOverlayIntentFn = applyOverlayIntent,
    clearEditModeFn = clearEditMode,
}: CreateSimulationActionRuntimeOptions): SimulationActionRuntime {
    const effects = createSimulationRuntimeEffects({
        state,
        uiSessionController,
        renderControlPanel,
        setRuleSelectionOriginFn,
        dismissFirstRunHintFn,
        clearPatternStatusFn,
        applyOverlayIntentFn,
        clearEditModeFn,
    });

    const patchDepthRuntime = createPatchDepthRuntime({
        state,
        interactions,
        renderControlPanel,
        dismissHintsAndStatus: effects.dismissHintsAndStatus,
        applyOverlayIntentAndRender: effects.applyOverlayIntentAndRender,
        reconcileTopologySelectionRuleOrigin: effects.reconcileTopologySelectionRuleOrigin,
        persistAppliedPatchDepth: effects.persistAppliedPatchDepth,
        clearPendingPatchDepthFn,
        setPendingPatchDepthFn,
        setTimeoutFn,
        clearTimeoutFn,
        patchDepthDebounceMs,
    });

    const ruleSpeedRuntime = createRuleSpeedRuntime({
        state,
        configSyncController,
        uiSessionController,
        renderControlPanel,
        getViewportDimensions,
        dismissHintsAndStatus: effects.dismissHintsAndStatus,
        setEditorRuleFn,
        setRuleSelectionOriginFn,
    });

    const topologyRuntime = createTopologySelectionRuntime({
        state,
        interactions,
        renderControlPanel,
        getViewportDimensions,
        dismissHintsAndStatus: effects.dismissHintsAndStatus,
        applyOverlayIntentAndRender: effects.applyOverlayIntentAndRender,
        preserveRuleOnTopologySelection: effects.preserveRuleOnTopologySelection,
        reconcileTopologySelectionRuleOrigin: effects.reconcileTopologySelectionRuleOrigin,
        clearScheduledPatchDepthCommit: patchDepthRuntime.clearScheduledPatchDepthCommit,
        setTopologySpecFn: setTopologySpec,
        setPatchDepthFn,
        setCellSizeFn,
    });

    return {
        state,
        interactions,
        viewportController,
        configSyncController,
        uiSessionController,
        renderControlPanel,
        getViewportDimensions,
        dismissHintsAndStatus: effects.dismissHintsAndStatus,
        applyOverlayIntentAndRender: effects.applyOverlayIntentAndRender,
        buildResetPayload: topologyRuntime.buildResetPayload,
        applyRuleSelection: ruleSpeedRuntime.applyRuleSelection,
        applySpeedSelection: ruleSpeedRuntime.applySpeedSelection,
        requestPatchDepth: patchDepthRuntime.requestPatchDepth,
        changeTilingFamily: topologyRuntime.changeTilingFamily,
        changeAdjacencyMode: topologyRuntime.changeAdjacencyMode,
        resetRuleSelectionOrigin: effects.resetRuleSelectionOrigin,
    };
}
