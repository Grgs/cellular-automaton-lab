import {
    DEFAULT_BRUSH_SIZE,
    DEFAULT_EDITOR_TOOL,
} from "./editor-tools.js";
import type { EditorTool } from "./editor-tools.js";
import { createDragPaintSession } from "./drag-session.js";
import { createEditorSessionController } from "./interactions/editor-session.js";
import { createHistoryCommands } from "./interactions/history-commands.js";
import { createLegacyDragController } from "./interactions/legacy-drag.js";
import { createInteractionCommandDispatch } from "./interactions/command-dispatch.js";
import { createInteractionEditPolicy } from "./interactions/edit-policy.js";
import { createInteractionSessionRuntime } from "./interactions/session-runtime.js";
import { createInteractionSurfaceBindings } from "./interactions/surface-bindings.js";
import { createSimulationMutations } from "./interactions/simulation-mutations.js";
import type {
    CreateSimulationMutationsFunction,
    InteractionController,
} from "./types/controller.js";
import type { GridInteractionBindings, InteractionControllerOptions } from "./types/editor.js";
import type { AppState } from "./types/state.js";

export { cellKey, interpolateCellPath, createDragPaintSession } from "./drag-session.js";

export function createInteractionController({
    surfaceElement,
    state = null,
    resolveCellFromEvent,
    previewPaintCells,
    clearPreview,
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
    createSimulationMutationsFn = createSimulationMutations,
    createHistoryCommandsFn,
    createLegacyDragControllerFn,
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
    createLegacyDragControllerFn?: typeof createLegacyDragController;
    createEditorSessionControllerFn?: typeof createEditorSessionController;
    bindGridInteractionsFn?: (options: GridInteractionBindings) => void;
    state?: AppState | null;
}): InteractionController {
    const mutations = simulationMutations || createSimulationMutationsFn({
        mutationRunner,
        onError,
        applySimulationState,
        refreshState,
    });

    const editPolicy = createInteractionEditPolicy({
        state,
        dismissOverlays,
        armEditMode,
        hideEditCue,
        setPatternStatus,
        getEditorTool: getEditorTool as () => EditorTool,
        getBrushSize,
        renderControlPanel,
        setTimeoutFn,
    });

    const sessionRuntime = createInteractionSessionRuntime({
        surfaceElement,
        state,
        getPaintState,
        getEditorTool: getEditorTool as () => EditorTool,
        getBrushSize,
        previewPaintCells,
        clearPreview,
        setCellsRequest,
        postControl,
        renderControlPanel,
        supportsEditorTools: editPolicy.supportsEditorTools,
        runStateMutation: mutations.runStateMutation,
        createHistoryCommandsFn,
        createLegacyDragControllerFn,
        createEditorSessionControllerFn,
    });

    const commandDispatch = createInteractionCommandDispatch({
        mutations,
        toggleCellRequest,
        setCellRequest,
        postControl,
        getPaintState,
    });

    const surfaceBindings = createInteractionSurfaceBindings({
        surfaceElement,
        resolveCellFromEvent,
        editPolicy,
        editorSession: sessionRuntime.editorSession,
        legacyDrag: sessionRuntime.legacyDrag,
        paintCell: commandDispatch.paintCell,
        bindGridInteractionsFn,
        setTimeoutFn,
    });

    return {
        bindGridInteractions: surfaceBindings.bindGridInteractions,
        toggleCell: commandDispatch.toggleCell,
        sendControl: commandDispatch.sendControl,
        undo: () => sessionRuntime.historyCommands.undo(),
        redo: () => sessionRuntime.historyCommands.redo(),
        cancelActivePreview: () => sessionRuntime.editorSession.cancelActivePreview(),
        runSerialized: commandDispatch.runSerialized,
    };
}
