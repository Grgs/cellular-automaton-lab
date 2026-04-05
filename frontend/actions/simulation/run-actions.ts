import {
    BLOCKING_ACTIVITY_RESET_BOARD,
} from "../../blocking-activity.js";
import {
    OVERLAY_INTENT_BOARD_RESET,
    OVERLAY_INTENT_RUN_STARTED,
    OVERLAY_INTENT_RUN_STATE_SYNCED,
} from "../../overlay-policy.js";
import type { SimulationActionRuntime, SimulationActionSet } from "../../types/actions.js";

export function createRunActions(runtime: SimulationActionRuntime): Pick<
    SimulationActionSet,
    "toggleRun" | "step" | "reset" | "randomReset" | "changeSpeed"
> {
    const {
        state,
        interactions,
        dismissHintsAndStatus,
        applyOverlayIntentAndRender,
        buildResetPayload,
        applySpeedSelection,
        resetRuleSelectionOrigin,
    } = runtime;

    return {
        toggleRun() {
            dismissHintsAndStatus();
            if (state.isRunning) {
                return interactions.sendControl("/api/control/pause");
            }

            const path = state.generation > 0
                ? "/api/control/resume"
                : "/api/control/start";
            applyOverlayIntentAndRender(OVERLAY_INTENT_RUN_STARTED);
            return interactions.sendControl(path).catch((error) => {
                applyOverlayIntentAndRender(OVERLAY_INTENT_RUN_STATE_SYNCED);
                throw error;
            });
        },

        step() {
            dismissHintsAndStatus();
            return interactions.sendControl("/api/control/step");
        },

        reset() {
            dismissHintsAndStatus();
            interactions.clearSelection?.();
            applyOverlayIntentAndRender(OVERLAY_INTENT_BOARD_RESET);
            return interactions.sendControl("/api/control/reset", buildResetPayload(false), {
                blockingActivity: BLOCKING_ACTIVITY_RESET_BOARD,
            }).then((simulationState) => {
                resetRuleSelectionOrigin();
                return simulationState;
            });
        },

        randomReset() {
            dismissHintsAndStatus();
            interactions.clearSelection?.();
            applyOverlayIntentAndRender(OVERLAY_INTENT_BOARD_RESET);
            return interactions.sendControl("/api/control/reset", buildResetPayload(true), {
                blockingActivity: BLOCKING_ACTIVITY_RESET_BOARD,
            }).then((simulationState) => {
                resetRuleSelectionOrigin();
                return simulationState;
            });
        },

        changeSpeed(nextSpeed) {
            applySpeedSelection(nextSpeed);
        },
    };
}
