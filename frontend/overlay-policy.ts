import {
    clearRunningOverlayRestoreActive,
    clearOverlaysDismissed,
    clearInspectorTemporarilyHidden,
    setInspectorOccludesGrid,
    setInspectorTemporarilyHidden,
    setOverlayRunPending,
    setOverlaysDismissed,
    setRunningOverlayRestoreActive,
} from "./state/overlay-state.js";
import type { AppState } from "./types/state.js";

export const OVERLAY_INTENT_CANVAS_INTERACTION = "canvas_interaction";
export const OVERLAY_INTENT_TOP_BAR_EMPTY_CLICK = "top_bar_empty_click";
export const OVERLAY_INTENT_INSPECTOR_EMPTY_CLICK = "inspector_empty_click";
export const OVERLAY_INTENT_WORKSPACE_EMPTY_CLICK = "workspace_empty_click";
export const OVERLAY_INTENT_RUN_STARTED = "run_started";
export const OVERLAY_INTENT_RUN_STATE_SYNCED = "run_state_synced";
export const OVERLAY_INTENT_BOARD_RESET = "board_reset";
export const OVERLAY_INTENT_BOARD_REBUILT = "board_rebuilt";
export const OVERLAY_INTENT_MANUAL_RESTORE = "manual_restore";
export const OVERLAY_INTENT_MANUAL_HIDE_INSPECTOR = "manual_hide_inspector";
export const OVERLAY_INTENT_LAYOUT_OCCLUSION_CHANGED = "layout_occlusion_changed";

type OverlayIntent =
    | typeof OVERLAY_INTENT_CANVAS_INTERACTION
    | typeof OVERLAY_INTENT_TOP_BAR_EMPTY_CLICK
    | typeof OVERLAY_INTENT_INSPECTOR_EMPTY_CLICK
    | typeof OVERLAY_INTENT_WORKSPACE_EMPTY_CLICK
    | typeof OVERLAY_INTENT_RUN_STARTED
    | typeof OVERLAY_INTENT_RUN_STATE_SYNCED
    | typeof OVERLAY_INTENT_BOARD_RESET
    | typeof OVERLAY_INTENT_BOARD_REBUILT
    | typeof OVERLAY_INTENT_MANUAL_RESTORE
    | typeof OVERLAY_INTENT_MANUAL_HIDE_INSPECTOR
    | typeof OVERLAY_INTENT_LAYOUT_OCCLUSION_CHANGED;

interface OverlayIntentContext {
    inspectorOccludesGrid?: boolean;
}

function setDismissed(state: AppState, dismissed: boolean): boolean {
    if (dismissed) {
        if (state.overlaysDismissed) {
            return false;
        }
        setOverlaysDismissed(state, true);
        return true;
    }
    if (!state.overlaysDismissed) {
        return false;
    }
    clearOverlaysDismissed(state);
    return true;
}

function setRunPending(state: AppState, pending: boolean): boolean {
    if (Boolean(state.overlayRunPending) === Boolean(pending)) {
        return false;
    }
    setOverlayRunPending(state, pending);
    return true;
}

function setInspectorHidden(state: AppState, hidden: boolean): boolean {
    if (hidden) {
        if (state.inspectorTemporarilyHidden) {
            return false;
        }
        setInspectorTemporarilyHidden(state, true);
        return true;
    }
    if (!state.inspectorTemporarilyHidden) {
        return false;
    }
    clearInspectorTemporarilyHidden(state);
    return true;
}

function setRunningRestoreActive(state: AppState, active: boolean): boolean {
    if (Boolean(state.runningOverlayRestoreActive) === Boolean(active)) {
        return false;
    }
    if (active) {
        setRunningOverlayRestoreActive(state, true);
        return true;
    }
    clearRunningOverlayRestoreActive(state);
    return true;
}

export function applyOverlayIntent(
    state: AppState,
    intent: OverlayIntent,
    context: OverlayIntentContext = {},
): boolean {
    switch (intent) {
        case OVERLAY_INTENT_CANVAS_INTERACTION: {
            const dismissalChanged = setDismissed(state, true);
            const runningRestoreChanged = setRunningRestoreActive(state, false);
            return dismissalChanged || runningRestoreChanged;
        }
        case OVERLAY_INTENT_TOP_BAR_EMPTY_CLICK: {
            const dismissalChanged = setDismissed(state, false);
            const inspectorChanged = setInspectorHidden(state, false);
            return dismissalChanged || inspectorChanged;
        }
        case OVERLAY_INTENT_INSPECTOR_EMPTY_CLICK:
            return setDismissed(state, false);
        case OVERLAY_INTENT_WORKSPACE_EMPTY_CLICK: {
            const dismissalChanged = setDismissed(state, true);
            const inspectorChanged = setInspectorHidden(state, true);
            const runningRestoreChanged = setRunningRestoreActive(state, false);
            return dismissalChanged || inspectorChanged || runningRestoreChanged;
        }
        case OVERLAY_INTENT_RUN_STARTED: {
            const runPendingChanged = setRunPending(state, true);
            const runningRestoreChanged = setRunningRestoreActive(state, false);
            return runPendingChanged || runningRestoreChanged;
        }
        case OVERLAY_INTENT_RUN_STATE_SYNCED: {
            const runPendingChanged = setRunPending(state, false);
            const runningRestoreChanged = state.isRunning
                ? false
                : setRunningRestoreActive(state, false);
            return runPendingChanged || runningRestoreChanged;
        }
        case OVERLAY_INTENT_BOARD_RESET:
        case OVERLAY_INTENT_BOARD_REBUILT: {
            const dismissalChanged = setDismissed(state, false);
            const inspectorChanged = setInspectorHidden(state, false);
            const runPendingChanged = setRunPending(state, false);
            const runningRestoreChanged = setRunningRestoreActive(state, false);
            return dismissalChanged || inspectorChanged || runPendingChanged || runningRestoreChanged;
        }
        case OVERLAY_INTENT_MANUAL_RESTORE: {
            const dismissalChanged = setDismissed(state, false);
            const inspectorChanged = setInspectorHidden(state, false);
            const runningRestoreChanged = (state.isRunning || state.overlayRunPending)
                ? setRunningRestoreActive(state, true)
                : false;
            return dismissalChanged || inspectorChanged || runningRestoreChanged;
        }
        case OVERLAY_INTENT_MANUAL_HIDE_INSPECTOR: {
            const dismissalChanged = setDismissed(state, false);
            const inspectorChanged = setInspectorHidden(state, false);
            return dismissalChanged || inspectorChanged;
        }
        case OVERLAY_INTENT_LAYOUT_OCCLUSION_CHANGED: {
            const nextOccludesGrid = context.inspectorOccludesGrid ?? false;
            if (state.inspectorOccludesGrid === nextOccludesGrid) {
                return false;
            }
            setInspectorOccludesGrid(state, nextOccludesGrid);
            return true;
        }
        default:
            return false;
    }
}
