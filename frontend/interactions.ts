import {
    DEFAULT_BRUSH_SIZE,
    DEFAULT_EDITOR_TOOL,
} from "./editor-tools.js";
import type { EditorTool } from "./editor-tools.js";
import { createDragPaintSession } from "./drag-session.js";
import { createEditorSessionController } from "./interactions/editor-session.js";
import { createHistoryCommands } from "./interactions/history-commands.js";
import { createPaintDragController } from "./interactions/paint-drag.js";
import { createSimulationMutations } from "./interactions/simulation-mutations.js";
import {
    createInteractionCommandSurface,
    createInteractionEditorRuntime,
    createInteractionMutationRuntime,
} from "./interaction-groups.js";
import type {
    CreateSimulationMutationsFunction,
    InteractionController,
} from "./types/controller.js";
import type { GridInteractionBindings, InteractionControllerOptions, PaintableCell } from "./types/editor.js";
import type { AppState } from "./types/state.js";

export { cellKey, interpolateCellPath, createDragPaintSession } from "./drag-session.js";

export function createInteractionController({
    surfaceElement,
    state = null,
    resolveCellFromEvent,
    previewPaintCells,
    clearPreview,
    setHoveredCell,
        setSelectedCells,
        getSelectedCells,
        setGestureOutline,
        flashGestureOutline,
        clearGestureOutline,
        openInspectorDrawer = () => {},
        mutationRunner,
        onError,
    applySimulationState,
    refreshState,
    toggleCellRequest,
    setCellRequest,
    setCellsRequest,
    postControl,
    getPaintState,
    simulationMutations = null,
    createSimulationMutationsFn,
    createHistoryCommandsFn,
    createPaintDragControllerFn,
    createEditorSessionControllerFn,
    bindGridInteractionsFn,
    dismissOverlays = () => false,
    armEditMode = null,
    hideEditCue = null,
    setPatternStatus = null,
    getEditorTool = () => state?.selectedEditorTool ?? DEFAULT_EDITOR_TOOL,
    getBrushSize = () => state?.brushSize ?? DEFAULT_BRUSH_SIZE,
    renderControlPanel = () => {},
    setTimeoutFn = (callback, delay) => window.setTimeout(callback, delay),
}: InteractionControllerOptions & {
    createSimulationMutationsFn?: CreateSimulationMutationsFunction;
    createHistoryCommandsFn?: typeof createHistoryCommands;
    createPaintDragControllerFn?: typeof createPaintDragController;
    createEditorSessionControllerFn?: typeof createEditorSessionController;
    bindGridInteractionsFn?: (options: GridInteractionBindings) => void;
    state?: AppState | null;
}): InteractionController {
    const { mutations, editPolicy } = createInteractionMutationRuntime({
        state,
        createSimulationMutationsFn,
        simulationMutations,
        mutationRunner,
        onError,
        applySimulationState,
        refreshState,
        dismissOverlays,
        armEditMode,
        hideEditCue,
        setPatternStatus,
        getEditorTool: getEditorTool as () => EditorTool,
        getBrushSize,
        renderControlPanel,
        setTimeoutFn,
    });

    const sessionRuntime = createInteractionEditorRuntime({
        surfaceElement,
        state,
        getPaintState,
        getEditorTool: getEditorTool as () => EditorTool,
        getBrushSize,
        previewPaintCells,
        clearPreview,
        setGestureOutline,
        flashGestureOutline,
        clearGestureOutline,
        setCellsRequest,
        postControl,
        renderControlPanel,
        supportsEditorTools: editPolicy.supportsEditorTools,
        runStateMutation: mutations.runStateMutation,
        createHistoryCommandsFn,
        createPaintDragControllerFn,
        createEditorSessionControllerFn,
    });

    const { commandDispatch, surfaceBindings } = createInteractionCommandSurface({
        surfaceElement,
        resolveCellFromEvent,
        state,
        editPolicy,
        editorSession: sessionRuntime.editorSession,
        paintDrag: sessionRuntime.paintDrag,
        mutations,
        setHoveredCell,
        setSelectedCells,
        getSelectedCells,
        clearGestureOutline,
        openInspectorDrawer,
        renderControlPanel,
        toggleCellRequest,
        setCellRequest,
        postControl,
        getPaintState,
        getCellState: (cell: PaintableCell) => {
            if (typeof cell.state === "number") {
                return cell.state;
            }
            if (!state || typeof cell.id !== "string" || cell.id.length === 0) {
                return 0;
            }
            const indexedCell = state.topologyIndex?.byId?.get(cell.id);
            if (!indexedCell || typeof indexedCell.index !== "number") {
                return 0;
            }
            return Number(state.cellStates[indexedCell.index] ?? 0);
        },
        bindGridInteractionsFn,
        setTimeoutFn,
    });

    return {
        bindGridInteractions: surfaceBindings.bindGridInteractions,
        toggleCell: commandDispatch.toggleCell,
        clearSelection: () => {
            setSelectedCells([]);
            renderControlPanel();
        },
        sendControl: commandDispatch.sendControl,
        undo: () => sessionRuntime.historyCommands.undo(),
        redo: () => sessionRuntime.historyCommands.redo(),
        cancelActivePreview: () => sessionRuntime.editorSession.cancelActivePreview(),
        runSerialized: commandDispatch.runSerialized,
    };
}
