import { hasRedoHistory, hasUndoHistory } from "../editor-history.js";
import {
    BRUSH_SIZE_OPTIONS,
    DEFAULT_BRUSH_SIZE,
    EDITOR_SHORTCUT_HINT,
    EDITOR_TOOL_OPTIONS,
} from "./shared.js";
import type { AppState } from "../types/state.js";
import type { EditorViewModel } from "../types/ui.js";

export function buildEditorViewModel({ state }: { state: AppState }): EditorViewModel {
    const editingBlocked = Boolean(state.isRunning || state.overlayRunPending);
    const gridEditMode = editingBlocked
        ? "running"
        : state.editArmed
            ? "armed"
            : "idle";
    return {
        editorTools: EDITOR_TOOL_OPTIONS,
        selectedEditorTool: state.selectedEditorTool,
        brushSizeOptions: BRUSH_SIZE_OPTIONS,
        selectedBrushSize: state.brushSize ?? DEFAULT_BRUSH_SIZE,
        undoDisabled: !hasUndoHistory(state),
        redoDisabled: !hasRedoHistory(state),
        editorShortcutHint: EDITOR_SHORTCUT_HINT,
        gridEditMode,
        canvasEditCueVisible: Boolean(state.editCueVisible && state.editArmed && !editingBlocked),
        canvasEditCueText: "Edit mode active. Click or drag to paint.",
    };
}
