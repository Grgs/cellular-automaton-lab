import type { AppState } from "../types/state.js";

interface BlockingActivityOptions {
    kind?: string | null;
    message?: string;
    detail?: string;
    visible?: boolean;
    startedAt?: number;
}

export function setDrawerOpen(state: AppState, drawerOpen: boolean): void {
    state.drawerOpen = drawerOpen;
}

export function setOverlaysDismissed(state: AppState, overlaysDismissed: boolean): void {
    state.overlaysDismissed = overlaysDismissed;
}

export function clearOverlaysDismissed(state: AppState): void {
    state.overlaysDismissed = false;
}

export function setInspectorTemporarilyHidden(state: AppState, inspectorTemporarilyHidden: boolean): void {
    state.inspectorTemporarilyHidden = inspectorTemporarilyHidden;
}

export function clearInspectorTemporarilyHidden(state: AppState): void {
    state.inspectorTemporarilyHidden = false;
}

export function setFirstRunHintDismissed(state: AppState, dismissed: boolean): void {
    state.firstRunHintDismissed = dismissed;
}

export function dismissFirstRunHint(state: AppState): void {
    setFirstRunHintDismissed(state, true);
}

export function setOverlayRunPending(state: AppState, overlayRunPending: boolean): void {
    state.overlayRunPending = overlayRunPending;
}

export function setRunningOverlayRestoreActive(state: AppState, runningOverlayRestoreActive: boolean): void {
    state.runningOverlayRestoreActive = runningOverlayRestoreActive;
}

export function clearRunningOverlayRestoreActive(state: AppState): void {
    state.runningOverlayRestoreActive = false;
}

export function setInspectorOccludesGrid(state: AppState, inspectorOccludesGrid: boolean): void {
    state.inspectorOccludesGrid = inspectorOccludesGrid;
}

export function setEditArmed(state: AppState, editArmed: boolean): void {
    state.editArmed = editArmed;
}

export function setEditCueVisible(state: AppState, editCueVisible: boolean): void {
    state.editCueVisible = editCueVisible;
}

export function armEditMode(
    state: AppState,
    { showCue = true }: { showCue?: boolean } = {},
): boolean {
    const nextEditArmed = true;
    const nextEditCueVisible = Boolean(showCue);
    const changed = state.editArmed !== nextEditArmed
        || state.editCueVisible !== nextEditCueVisible;
    state.editArmed = nextEditArmed;
    state.editCueVisible = nextEditCueVisible;
    return changed;
}

export function hideEditCue(state: AppState): boolean {
    if (!state.editCueVisible) {
        return false;
    }
    state.editCueVisible = false;
    return true;
}

export function clearEditMode(state: AppState): boolean {
    const changed = Boolean(state.editArmed || state.editCueVisible);
    state.editArmed = false;
    state.editCueVisible = false;
    return changed;
}

export function setBlockingActivity(
    state: AppState,
    {
        kind = null,
        message = "",
        detail = "",
        visible = false,
        startedAt = Date.now(),
    }: BlockingActivityOptions = {},
): void {
    state.blockingActivityKind = kind ? String(kind) : null;
    state.blockingActivityMessage = message ? String(message) : "";
    state.blockingActivityDetail = detail ? String(detail) : "";
    state.blockingActivityVisible = Boolean(visible && state.blockingActivityMessage);
    state.blockingActivityStartedAt = state.blockingActivityKind ? Number(startedAt) : null;
}

export function clearBlockingActivity(state: AppState): void {
    state.blockingActivityKind = null;
    state.blockingActivityMessage = "";
    state.blockingActivityDetail = "";
    state.blockingActivityVisible = false;
    state.blockingActivityStartedAt = null;
}

export function setPatternStatus(state: AppState, message = "", tone = "info"): void {
    state.patternStatus = {
        message: String(message ?? ""),
        tone,
    };
}

export function clearPatternStatus(state: AppState): void {
    setPatternStatus(state, "", "info");
}

export function hasPatternCells(state: AppState): boolean {
    return Array.isArray(state.cellStates)
        && state.cellStates.some((cellState) => Number(cellState) !== 0);
}
