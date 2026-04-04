import {
    commitRedoSuccess,
    commitUndoSuccess,
    peekRedoEntry,
    peekUndoEntry,
} from "../editor-history.js";
import type { EditorHistoryCommands, HistoryCommandsOptions } from "../types/editor.js";

export function createHistoryCommands({
    state,
    setCellsRequest,
    renderControlPanel = () => {},
    supportsEditorTools = () => false,
    runStateMutation,
}: HistoryCommandsOptions): EditorHistoryCommands {
    async function applyHistoryEntry(direction: "undo" | "redo") {
        if (!supportsEditorTools()) {
            return null;
        }

        const entry = direction === "undo" ? peekUndoEntry(state) : peekRedoEntry(state);
        if (!entry) {
            return null;
        }

        const cells = direction === "undo" ? entry.inverseCells : entry.forwardCells;
        const simulationState = await runStateMutation(
            () => setCellsRequest(cells),
            { recoverWithRefresh: true, source: "editor" },
        ).catch(() => null);
        if (!simulationState) {
            return null;
        }

        if (direction === "undo") {
            commitUndoSuccess(state);
        } else {
            commitRedoSuccess(state);
        }
        renderControlPanel();
        return simulationState;
    }

    return {
        undo: () => applyHistoryEntry("undo"),
        redo: () => applyHistoryEntry("redo"),
    };
}
