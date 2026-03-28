import type { AppState } from "../types/state.js";

interface BlockingActivityOptions {
    kind?: string | null;
    message?: string;
    detail?: string;
    visible?: boolean;
    startedAt?: number;
}

export function setDrawerOpen(state: AppState, drawerOpen: unknown): void {
    state.drawerOpen = Boolean(drawerOpen);
}

export function setOverlaysDismissed(state: AppState, overlaysDismissed: unknown): void {
    state.overlaysDismissed = Boolean(overlaysDismissed);
}

export function clearOverlaysDismissed(state: AppState): void {
    state.overlaysDismissed = false;
}

export function setInspectorTemporarilyHidden(state: AppState, inspectorTemporarilyHidden: unknown): void {
    state.inspectorTemporarilyHidden = Boolean(inspectorTemporarilyHidden);
}

export function clearInspectorTemporarilyHidden(state: AppState): void {
    state.inspectorTemporarilyHidden = false;
}

export function setFirstRunHintDismissed(state: AppState, dismissed: unknown): void {
    state.firstRunHintDismissed = Boolean(dismissed);
}

export function dismissFirstRunHint(state: AppState): void {
    setFirstRunHintDismissed(state, true);
}

export function setOverlayRunPending(state: AppState, overlayRunPending: unknown): void {
    state.overlayRunPending = Boolean(overlayRunPending);
}

export function setRunningOverlayRestoreActive(state: AppState, runningOverlayRestoreActive: unknown): void {
    state.runningOverlayRestoreActive = Boolean(runningOverlayRestoreActive);
}

export function clearRunningOverlayRestoreActive(state: AppState): void {
    state.runningOverlayRestoreActive = false;
}

export function setInspectorOccludesGrid(state: AppState, inspectorOccludesGrid: unknown): void {
    state.inspectorOccludesGrid = Boolean(inspectorOccludesGrid);
}

export function setEditArmed(state: AppState, editArmed: unknown): void {
    state.editArmed = Boolean(editArmed);
}

export function setEditCueVisible(state: AppState, editCueVisible: unknown): void {
    state.editCueVisible = Boolean(editCueVisible);
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
