import { BLOCKING_ACTIVITY_RESTORE_DEFAULTS } from "../blocking-activity.js";
import { FRONTEND_DEFAULTS } from "../defaults.js";
import { RULE_SELECTION_ORIGIN_DEFAULT } from "../state/constants.js";
import {
    clearPendingPatchDepth,
    rememberedCellSizeForTilingFamily,
    setCellSize,
    setPatchDepth,
} from "../state/sizing-state.js";
import { dismissFirstRunHint } from "../state/overlay-state.js";
import {
    findRule,
    setActiveRule,
    setEditorRule,
    setRuleSelectionOrigin,
    setSpeed,
    setTopologySpec,
} from "../state/simulation-state.js";
import type {
    InteractionController,
    ResetControlBody,
    UiSessionController,
} from "../types/controller.js";
import type { AppState } from "../types/state.js";
import type { SimulationSnapshot } from "../types/domain.js";

export interface DefaultResetRuntime {
    buildDefaultResetPayload(): ResetControlBody;
    applyDefaultBoardPreview(): void;
    resetAllSettings(): Promise<SimulationSnapshot | null>;
}

interface CreateDefaultResetRuntimeOptions {
    state: AppState;
    interactions: InteractionController;
    uiSessionController: UiSessionController;
    renderCurrentGrid: () => void;
    renderControlPanel: () => void;
    refreshState: () => Promise<void>;
    resetThemeToDefault: () => void;
}

export function createDefaultResetRuntime({
    state,
    interactions,
    uiSessionController,
    renderCurrentGrid,
    renderControlPanel,
    refreshState,
    resetThemeToDefault,
}: CreateDefaultResetRuntimeOptions): DefaultResetRuntime {
    function buildDefaultResetPayload(): ResetControlBody {
        return {
            topology_spec: FRONTEND_DEFAULTS.simulation.topology_spec,
            speed: FRONTEND_DEFAULTS.simulation.speed,
            rule: FRONTEND_DEFAULTS.simulation.rule,
            randomize: false,
        };
    }

    function applyDefaultBoardPreview(): void {
        const defaultTopologySpec = FRONTEND_DEFAULTS.simulation.topology_spec;
        const defaultRule = findRule(state, FRONTEND_DEFAULTS.simulation.rule) || null;

        setTopologySpec(state, defaultTopologySpec);
        state.width = Number(defaultTopologySpec.width) || 0;
        state.height = Number(defaultTopologySpec.height) || 0;
        setPatchDepth(state, defaultTopologySpec.patch_depth, defaultTopologySpec.tiling_family);
        clearPendingPatchDepth(state);
        setCellSize(
            state,
            rememberedCellSizeForTilingFamily(state, defaultTopologySpec.tiling_family),
            defaultTopologySpec.tiling_family,
        );
        setSpeed(state, FRONTEND_DEFAULTS.simulation.speed);
        setRuleSelectionOrigin(state, RULE_SELECTION_ORIGIN_DEFAULT);
        if (defaultRule) {
            setActiveRule(state, defaultRule);
            setEditorRule(state, defaultRule.name, { resetPaintState: true });
        }
    }

    async function resetAllSettings(): Promise<SimulationSnapshot | null> {
        dismissFirstRunHint(state);
        uiSessionController.resetSessionPreferences?.();
        resetThemeToDefault();
        renderCurrentGrid();
        applyDefaultBoardPreview();
        renderControlPanel();
        const simulationState = await interactions.sendControl(
            "/api/control/reset",
            buildDefaultResetPayload(),
            {
                blockingActivity: BLOCKING_ACTIVITY_RESTORE_DEFAULTS,
            },
        );
        if (!simulationState) {
            await refreshState();
        }
        return simulationState ?? null;
    }

    return {
        buildDefaultResetPayload,
        applyDefaultBoardPreview,
        resetAllSettings,
    };
}
