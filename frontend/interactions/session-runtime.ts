import { createEditorSessionController } from "./editor-session.js";
import { createHistoryCommands } from "./history-commands.js";
import { createLegacyDragController } from "./legacy-drag.js";
import type { EditorTool } from "../editor-tools.js";
import type {
    EditorHistoryCommands,
    EditorSessionController,
    GestureOutlineTone,
    LegacyDragController,
    PaintableCell,
    PreviewPaintCells,
} from "../types/editor.js";
import type {
    MutationRunnerOptions,
    PostControlFunction,
    SetCellsRequestFunction,
} from "../types/controller.js";
import type { AppState } from "../types/state.js";
import type { SimulationSnapshot } from "../types/domain.js";

export interface InteractionSessionRuntime {
    editorSession: EditorSessionController;
    legacyDrag: LegacyDragController;
    historyCommands: EditorHistoryCommands;
}

export function createInteractionSessionRuntime({
    surfaceElement,
    state,
    getPaintState,
    getEditorTool,
    getBrushSize,
    previewPaintCells,
    clearPreview,
    setGestureOutline,
    flashGestureOutline,
    clearGestureOutline,
    setCellsRequest,
    postControl,
    renderControlPanel,
    supportsEditorTools,
    runStateMutation,
    createHistoryCommandsFn = createHistoryCommands,
    createLegacyDragControllerFn = createLegacyDragController,
    createEditorSessionControllerFn = createEditorSessionController,
}: {
    surfaceElement: HTMLElement | null;
    state: AppState | null;
    getPaintState: () => number;
    getEditorTool: () => EditorTool;
    getBrushSize: () => number;
    previewPaintCells: (cells: PreviewPaintCells) => void;
    clearPreview: () => void;
    setGestureOutline: (cells: PaintableCell[], tone: GestureOutlineTone) => void;
    flashGestureOutline: (
        cells: PaintableCell[],
        tone: GestureOutlineTone,
        durationMs?: number,
    ) => void;
    clearGestureOutline: () => void;
    setCellsRequest: SetCellsRequestFunction;
    postControl: PostControlFunction;
    renderControlPanel: () => void;
    supportsEditorTools: () => boolean;
    runStateMutation: (
        task: () => Promise<SimulationSnapshot>,
        options?: MutationRunnerOptions & { recoverWithRefresh?: boolean; source?: string },
    ) => Promise<SimulationSnapshot>;
    createHistoryCommandsFn?: typeof createHistoryCommands | undefined;
    createLegacyDragControllerFn?: typeof createLegacyDragController | undefined;
    createEditorSessionControllerFn?: typeof createEditorSessionController | undefined;
}): InteractionSessionRuntime {
    function setPointerCapture(pointerId: number | null): void {
        if (!surfaceElement || typeof surfaceElement.setPointerCapture !== "function" || pointerId === null) {
            return;
        }
        try {
            surfaceElement.setPointerCapture(pointerId);
        } catch {
            // Ignore capture errors for browsers that do not support it fully.
        }
    }

    function releasePointerCapture(pointerId: number | null): void {
        if (!surfaceElement || typeof surfaceElement.releasePointerCapture !== "function" || pointerId === null) {
            return;
        }
        try {
            surfaceElement.releasePointerCapture(pointerId);
        } catch {
            // Pointer capture might already be released.
        }
    }

    const editorSession = createEditorSessionControllerFn({
        state,
        getPaintState,
        getEditorTool,
        getBrushSize,
        previewPaintCells,
        clearPreview,
        setGestureOutline,
        flashGestureOutline,
        clearGestureOutline,
        setCellsRequest,
        postControl,
        renderControlPanel,
        setPointerCapture,
        releasePointerCapture,
        runStateMutation,
    });

    const legacyDrag = createLegacyDragControllerFn({
        getPaintState,
        previewPaintCells,
        clearPreview,
        setGestureOutline,
        flashGestureOutline,
        clearGestureOutline,
        setCellsRequest,
        runStateMutation,
        setPointerCapture,
        releasePointerCapture,
        enableClickSuppression: () => editorSession.enableClickSuppression(),
    });

    const historyCommands = createHistoryCommandsFn({
        state: state as AppState,
        setCellsRequest,
        renderControlPanel,
        supportsEditorTools,
        runStateMutation,
    });

    return {
        editorSession,
        legacyDrag,
        historyCommands,
    };
}
