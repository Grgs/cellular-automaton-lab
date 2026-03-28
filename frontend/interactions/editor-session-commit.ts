import { buildCommittedEdit, pushUndoEntry } from "../editor-history.js";
import type { EditorSessionOptions, PreviewPaintCell } from "../types/editor.js";
import type { SimulationSnapshot } from "../types/domain.js";

interface CreateEditorCommitRuntimeOptions {
    state: NonNullable<EditorSessionOptions["state"]>;
    postControl: EditorSessionOptions["postControl"];
    setCellsRequest: EditorSessionOptions["setCellsRequest"];
    renderControlPanel: NonNullable<EditorSessionOptions["renderControlPanel"]>;
    runStateMutation: EditorSessionOptions["runStateMutation"];
    supportsEditorTools: () => boolean;
    isRunning: () => boolean;
}

export interface EditorCommitRuntime {
    ensurePausedForEditing(): Promise<boolean>;
    commitEditorCells(cells: PreviewPaintCell[]): Promise<SimulationSnapshot | null>;
}

export function createEditorCommitRuntime({
    state,
    postControl,
    setCellsRequest,
    renderControlPanel,
    runStateMutation,
    supportsEditorTools,
    isRunning,
}: CreateEditorCommitRuntimeOptions): EditorCommitRuntime {
    async function ensurePausedForEditing(): Promise<boolean> {
        if (!supportsEditorTools() || !isRunning()) {
            return true;
        }

        const pausedState = await runStateMutation(
            () => postControl("/api/control/pause"),
            { source: "control" },
        ).catch(() => null);
        return Boolean(pausedState);
    }

    async function commitEditorCells(cells: PreviewPaintCell[]): Promise<SimulationSnapshot | null> {
        const edit = buildCommittedEdit(state, cells);
        if (!edit) {
            return null;
        }

        const simulationState = await runStateMutation(
            () => setCellsRequest(edit.forwardCells),
            { recoverWithRefresh: true, source: "editor" },
        ).catch(() => null);
        if (simulationState) {
            pushUndoEntry(state, edit);
            renderControlPanel();
        }
        return simulationState;
    }

    return {
        ensurePausedForEditing,
        commitEditorCells,
    };
}
