import { RULE_SELECTION_ORIGIN_USER } from "../../state/constants.js";
import {
    currentTopologyVariantKey,
    setEditorRule,
    setRuleSelectionOrigin,
} from "../../state/simulation-state.js";
import { ruleRequiresSquareDimensions } from "../../rule-constraints.js";
import type {
    ConfigSyncBody,
    ConfigSyncController,
    UiSessionController,
    ViewportDimensions,
} from "../../types/controller.js";
import type { SimulationActionRuleSyncOptions } from "../../types/actions.js";
import type { AppState } from "../../types/state.js";

interface CreateRuleSpeedRuntimeOptions {
    state: AppState;
    configSyncController: ConfigSyncController;
    uiSessionController: UiSessionController;
    renderControlPanel: () => void;
    getViewportDimensions: (
        geometry: string,
        ruleName: string | null,
        cellSize: number,
    ) => ViewportDimensions;
    dismissHintsAndStatus: () => void;
    setEditorRuleFn?: typeof setEditorRule;
    setRuleSelectionOriginFn?: typeof setRuleSelectionOrigin;
}

export interface RuleSpeedRuntime {
    applyRuleSelection(nextRuleName: string | null): void;
    applySpeedSelection(nextSpeed: number): void;
}

export function createRuleSpeedRuntime({
    state,
    configSyncController,
    uiSessionController,
    renderControlPanel,
    getViewportDimensions,
    dismissHintsAndStatus,
    setEditorRuleFn = setEditorRule,
    setRuleSelectionOriginFn = setRuleSelectionOrigin,
}: CreateRuleSpeedRuntimeOptions): RuleSpeedRuntime {
    function applyRuleSelection(nextRuleName: string | null): void {
        dismissHintsAndStatus();
        setEditorRuleFn(state, nextRuleName);
        setRuleSelectionOriginFn(state, RULE_SELECTION_ORIGIN_USER);
        uiSessionController.restorePaintStateForCurrentRule();
        renderControlPanel();
        const options: SimulationActionRuleSyncOptions = { running: state.isRunning };
        if (ruleRequiresSquareDimensions(nextRuleName)) {
            const body: ConfigSyncBody = {
                topology_spec: {
                    ...getViewportDimensions(
                        currentTopologyVariantKey(state),
                        nextRuleName,
                        state.cellSize,
                    ),
                    ...(state.unsafeSizingEnabled ? { unsafe_size_override: true } : {}),
                },
            };
            options.body = body;
        }
        configSyncController.requestRuleSync(nextRuleName, options);
    }

    function applySpeedSelection(nextSpeed: number): void {
        configSyncController.scheduleSpeedSync(nextSpeed);
        renderControlPanel();
    }

    return {
        applyRuleSelection,
        applySpeedSelection,
    };
}
