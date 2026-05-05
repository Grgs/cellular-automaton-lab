import {
    DEFAULT_EDITOR_TOOL,
    EDITOR_TOOL_BRUSH,
    EDITOR_TOOL_FILL,
    EDITOR_TOOL_LINE,
    EDITOR_TOOL_RECTANGLE,
} from "../editor-tools.js";
import type { EditorTool } from "../editor-tools.js";
import {
    armEditMode as armEditModeState,
    dismissFirstRunHint as dismissFirstRunHintState,
    hideEditCue as hideEditCueState,
    setPatternStatus as setPatternStatusState,
} from "../state/overlay-state.js";
import { EDIT_CUE_HIDE_DELAY_MS } from "./constants.js";
import type { AppState } from "../types/state.js";

export interface InteractionEditPolicy {
    supportsEditorTools(): boolean;
    editingBlockedByRun(): boolean;
    isEditArmed(): boolean;
    currentTool(): EditorTool;
    prepareDirectGridInteraction(event?: PointerEvent | MouseEvent | null): void;
    runningBrushEditingEnabled(): boolean;
    runningAdvancedToolBlocked(): boolean;
    armEditingFromGrid(
        event: PointerEvent | MouseEvent | null,
        options?: { suppressFollowupClick?: boolean },
    ): { consumeNextClick: boolean };
    blockRunningAdvancedTool(event?: PointerEvent | MouseEvent | null): void;
    dismissEditingUi(): Promise<boolean>;
}

export function createInteractionEditPolicy({
    state = null,
    dismissOverlays = () => false,
    armEditMode = null,
    hideEditCue = null,
    setPatternStatus = null,
    getEditorTool = () => state?.selectedEditorTool ?? DEFAULT_EDITOR_TOOL,
    renderControlPanel = () => {},
    setTimeoutFn = (callback, delay) => window.setTimeout(callback, delay),
}: {
    state?: AppState | null;
    dismissOverlays?: () => Promise<boolean> | boolean;
    armEditMode?: (() => boolean) | null;
    hideEditCue?: (() => boolean) | null;
    setPatternStatus?: ((message: string, tone?: string) => void) | null;
    getEditorTool?: () => EditorTool;
    getBrushSize?: () => number;
    renderControlPanel?: () => void;
    setTimeoutFn?: (callback: () => void, delay: number) => number;
}): InteractionEditPolicy {
    const runtimeState = state as AppState;
    const armEditModeAction =
        typeof armEditMode === "function"
            ? armEditMode
            : () => {
                  if (!state) {
                      return false;
                  }
                  const changed = armEditModeState(runtimeState);
                  if (changed) {
                      renderControlPanel();
                  }
                  return changed;
              };
    const hideEditCueAction =
        typeof hideEditCue === "function"
            ? hideEditCue
            : () => {
                  if (!state) {
                      return false;
                  }
                  const changed = hideEditCueState(runtimeState);
                  if (changed) {
                      renderControlPanel();
                  }
                  return changed;
              };
    const setPatternStatusAction =
        typeof setPatternStatus === "function"
            ? setPatternStatus
            : (message: string, tone = "info") => {
                  if (!state) {
                      return;
                  }
                  setPatternStatusState(runtimeState, message, tone);
                  renderControlPanel();
              };
    let editCueToken = 0;

    function supportsEditorTools(): boolean {
        return Boolean(state?.topology && state?.topologyIndex && Array.isArray(state?.cellStates));
    }

    function editingBlockedByRun(): boolean {
        return Boolean(state?.isRunning || state?.overlayRunPending);
    }

    function isEditArmed(): boolean {
        return Boolean(state?.editArmed);
    }

    function currentTool(): EditorTool {
        return supportsEditorTools() ? getEditorTool() : EDITOR_TOOL_BRUSH;
    }

    function scheduleEditCueHide(): void {
        editCueToken += 1;
        const cueToken = editCueToken;
        setTimeoutFn(() => {
            if (cueToken !== editCueToken || !runtimeState.editArmed) {
                return;
            }
            hideEditCueAction();
        }, EDIT_CUE_HIDE_DELAY_MS);
    }

    async function dismissEditingUi(): Promise<boolean> {
        const overlayDismissed = await dismissOverlays();
        const cueHidden = hideEditCueAction();
        return Boolean(overlayDismissed || cueHidden);
    }

    function prepareDirectGridInteraction(event: PointerEvent | MouseEvent | null = null): void {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        const hintDismissedChanged = Boolean(state && !runtimeState.firstRunHintDismissed);
        if (hintDismissedChanged) {
            dismissFirstRunHintState(runtimeState);
        }
        void dismissOverlays();
        const cueHidden = hideEditCueAction();
        if (hintDismissedChanged && !cueHidden) {
            renderControlPanel();
        }
    }

    function armEditingFromGrid(
        event: PointerEvent | MouseEvent | null,
        { suppressFollowupClick = false }: { suppressFollowupClick?: boolean } = {},
    ): { consumeNextClick: boolean } {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        const hintDismissedChanged = Boolean(state && !runtimeState.firstRunHintDismissed);
        if (hintDismissedChanged) {
            dismissFirstRunHintState(runtimeState);
        }
        void dismissOverlays();
        const changed = armEditModeAction();
        if (changed) {
            scheduleEditCueHide();
        } else if (hintDismissedChanged) {
            renderControlPanel();
        }
        return { consumeNextClick: Boolean(suppressFollowupClick) };
    }

    function runningBrushEditingEnabled(): boolean {
        return (
            supportsEditorTools() && editingBlockedByRun() && currentTool() === EDITOR_TOOL_BRUSH
        );
    }

    function runningAdvancedToolBlocked(): boolean {
        if (!supportsEditorTools() || !editingBlockedByRun()) {
            return false;
        }
        const tool = currentTool();
        return (
            tool === EDITOR_TOOL_LINE || tool === EDITOR_TOOL_RECTANGLE || tool === EDITOR_TOOL_FILL
        );
    }

    function runningToolLabel(tool = currentTool()): string {
        switch (tool) {
            case EDITOR_TOOL_LINE:
                return "Line";
            case EDITOR_TOOL_RECTANGLE:
                return "Rectangle";
            case EDITOR_TOOL_FILL:
                return "Fill";
            default:
                return "Tool";
        }
    }

    function blockRunningAdvancedTool(event: PointerEvent | MouseEvent | null = null): void {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        void dismissOverlays();
        hideEditCueAction();
        setPatternStatusAction(`Pause to use ${runningToolLabel()}.`, "info");
    }

    return {
        supportsEditorTools,
        editingBlockedByRun,
        isEditArmed,
        currentTool,
        prepareDirectGridInteraction,
        runningBrushEditingEnabled,
        runningAdvancedToolBlocked,
        armEditingFromGrid,
        blockRunningAdvancedTool,
        dismissEditingUi,
    };
}
