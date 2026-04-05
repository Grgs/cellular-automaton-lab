import { createEditorSessionController } from "./interactions/editor-session.js";
import { createHistoryCommands } from "./interactions/history-commands.js";
import { createLegacyDragController } from "./interactions/legacy-drag.js";
import { createInteractionCommandDispatch } from "./interactions/command-dispatch.js";
import { createInteractionEditPolicy } from "./interactions/edit-policy.js";
import { createInteractionSessionRuntime } from "./interactions/session-runtime.js";
import { createInteractionSurfaceBindings } from "./interactions/surface-bindings.js";
import { createSimulationMutations } from "./interactions/simulation-mutations.js";
import type { CreateSimulationMutationsFunction } from "./types/controller-runtime.js";
import type { GridInteractionBindings, InteractionControllerOptions, PaintableCell } from "./types/editor.js";
import type { AppState } from "./types/state.js";

interface InteractionMutationRuntimeOptions {
    state: AppState | null;
    createSimulationMutationsFn?: CreateSimulationMutationsFunction | undefined;
    simulationMutations?: InteractionControllerOptions["simulationMutations"] | null;
    mutationRunner: InteractionControllerOptions["mutationRunner"];
    onError: InteractionControllerOptions["onError"];
    applySimulationState: InteractionControllerOptions["applySimulationState"];
    refreshState: InteractionControllerOptions["refreshState"];
    dismissOverlays: NonNullable<InteractionControllerOptions["dismissOverlays"]>;
    armEditMode: InteractionControllerOptions["armEditMode"];
    hideEditCue: InteractionControllerOptions["hideEditCue"];
    setPatternStatus: InteractionControllerOptions["setPatternStatus"];
    getEditorTool: NonNullable<InteractionControllerOptions["getEditorTool"]>;
    getBrushSize: NonNullable<InteractionControllerOptions["getBrushSize"]>;
    renderControlPanel: NonNullable<InteractionControllerOptions["renderControlPanel"]>;
    setTimeoutFn: NonNullable<InteractionControllerOptions["setTimeoutFn"]>;
}

interface InteractionEditorRuntimeOptions {
    surfaceElement: InteractionControllerOptions["surfaceElement"];
    state: AppState | null;
    getPaintState: InteractionControllerOptions["getPaintState"];
    getEditorTool: NonNullable<InteractionControllerOptions["getEditorTool"]>;
    getBrushSize: NonNullable<InteractionControllerOptions["getBrushSize"]>;
    previewPaintCells: InteractionControllerOptions["previewPaintCells"];
    clearPreview: InteractionControllerOptions["clearPreview"];
    setCellsRequest: InteractionControllerOptions["setCellsRequest"];
    postControl: InteractionControllerOptions["postControl"];
    renderControlPanel: NonNullable<InteractionControllerOptions["renderControlPanel"]>;
    supportsEditorTools: () => boolean;
    runStateMutation: NonNullable<InteractionControllerOptions["simulationMutations"]>["runStateMutation"];
    createHistoryCommandsFn?: typeof createHistoryCommands | undefined;
    createLegacyDragControllerFn?: typeof createLegacyDragController | undefined;
    createEditorSessionControllerFn?: typeof createEditorSessionController | undefined;
}

interface InteractionCommandSurfaceOptions {
    surfaceElement: InteractionControllerOptions["surfaceElement"];
    resolveCellFromEvent: InteractionControllerOptions["resolveCellFromEvent"];
    editPolicy: ReturnType<typeof createInteractionEditPolicy>;
    editorSession: ReturnType<typeof createInteractionSessionRuntime>["editorSession"];
    legacyDrag: ReturnType<typeof createInteractionSessionRuntime>["legacyDrag"];
    mutations: NonNullable<InteractionControllerOptions["simulationMutations"]>;
    setHoveredCell: InteractionControllerOptions["setHoveredCell"];
    setSelectedCell: InteractionControllerOptions["setSelectedCell"];
    getSelectedCell: InteractionControllerOptions["getSelectedCell"];
    toggleCellRequest: InteractionControllerOptions["toggleCellRequest"];
    setCellRequest: InteractionControllerOptions["setCellRequest"];
    postControl: InteractionControllerOptions["postControl"];
    getPaintState: InteractionControllerOptions["getPaintState"];
    getCellState: (cell: PaintableCell) => number;
    bindGridInteractionsFn?: ((options: GridInteractionBindings) => void) | undefined;
    setTimeoutFn?: InteractionControllerOptions["setTimeoutFn"] | undefined;
}

export function createInteractionMutationRuntime({
    state,
    createSimulationMutationsFn = createSimulationMutations,
    simulationMutations = null,
    mutationRunner,
    onError,
    applySimulationState,
    refreshState,
    dismissOverlays,
    armEditMode,
    hideEditCue,
    setPatternStatus,
    getEditorTool,
    getBrushSize,
    renderControlPanel,
    setTimeoutFn,
}: InteractionMutationRuntimeOptions): {
    mutations: NonNullable<InteractionControllerOptions["simulationMutations"]>;
    editPolicy: ReturnType<typeof createInteractionEditPolicy>;
} {
    const mutations = simulationMutations || createSimulationMutationsFn({
        mutationRunner,
        onError,
        applySimulationState,
        refreshState,
    });

    const editPolicy = createInteractionEditPolicy({
        state,
        dismissOverlays,
        getEditorTool,
        getBrushSize,
        renderControlPanel,
        setTimeoutFn,
        ...(armEditMode === undefined ? {} : { armEditMode }),
        ...(hideEditCue === undefined ? {} : { hideEditCue }),
        ...(setPatternStatus === undefined ? {} : { setPatternStatus }),
    });

    return {
        mutations,
        editPolicy,
    };
}

export function createInteractionEditorRuntime({
    surfaceElement,
    state,
    getPaintState,
    getEditorTool,
    getBrushSize,
    previewPaintCells,
    clearPreview,
    setCellsRequest,
    postControl,
    renderControlPanel,
    supportsEditorTools,
    runStateMutation,
    createHistoryCommandsFn,
    createLegacyDragControllerFn,
    createEditorSessionControllerFn,
}: InteractionEditorRuntimeOptions) {
    return createInteractionSessionRuntime({
        surfaceElement,
        state,
        getPaintState,
        getEditorTool,
        getBrushSize,
        previewPaintCells,
        clearPreview,
        setCellsRequest,
        postControl,
        renderControlPanel,
        supportsEditorTools,
        runStateMutation,
        ...(createHistoryCommandsFn === undefined ? {} : { createHistoryCommandsFn }),
        ...(createLegacyDragControllerFn === undefined ? {} : { createLegacyDragControllerFn }),
        ...(createEditorSessionControllerFn === undefined ? {} : { createEditorSessionControllerFn }),
    });
}

export function createInteractionCommandSurface({
    surfaceElement,
    resolveCellFromEvent,
    editPolicy,
    editorSession,
    legacyDrag,
    mutations,
    setHoveredCell,
    setSelectedCell,
    getSelectedCell,
    toggleCellRequest,
    setCellRequest,
    postControl,
    getPaintState,
    getCellState,
    bindGridInteractionsFn,
    setTimeoutFn,
}: InteractionCommandSurfaceOptions) {
    const commandDispatch = createInteractionCommandDispatch({
        mutations,
        toggleCellRequest,
        setCellRequest,
        postControl,
        getPaintState,
        getCellState,
    });

    const surfaceBindings = createInteractionSurfaceBindings({
        surfaceElement,
        resolveCellFromEvent,
        editPolicy,
        editorSession,
        legacyDrag,
        setHoveredCell,
        setSelectedCell,
        getSelectedCell,
        paintCell: commandDispatch.paintCell,
        resolveDirectGestureTargetState: commandDispatch.resolveDirectGestureTargetState,
        bindGridInteractionsFn,
        setTimeoutFn,
    });

    return {
        commandDispatch,
        surfaceBindings,
    };
}
