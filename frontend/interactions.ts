import {
    DEFAULT_BRUSH_SIZE,
    DEFAULT_EDITOR_TOOL,
    EDITOR_TOOL_BRUSH,
    EDITOR_TOOL_FILL,
    EDITOR_TOOL_LINE,
    EDITOR_TOOL_RECTANGLE,
} from "./editor-tools.js";
import { createDragPaintSession } from "./drag-session.js";
import { bindGridInteractions as bindGridInteractionsToSurface } from "./interactions/grid-bindings.js";
import { createEditorSessionController } from "./interactions/editor-session.js";
import { createHistoryCommands } from "./interactions/history-commands.js";
import { createLegacyDragController } from "./interactions/legacy-drag.js";
import { createSimulationMutations } from "./interactions/simulation-mutations.js";
import {
    armEditMode as armEditModeState,
    dismissFirstRunHint as dismissFirstRunHintState,
    hideEditCue as hideEditCueState,
    setPatternStatus as setPatternStatusState,
} from "./state/overlay-state.js";
import type {
    ConfigSyncBody,
    CreateSimulationMutationsFunction,
    EmptyControlCommandPath,
    InteractionController,
    ResetControlBody,
    SimulationMutationOptions,
} from "./types/controller.js";
import type {
    EditorHistoryCommands,
    EditorSessionController,
    GridInteractionBindings,
    InteractionControllerOptions,
    LegacyDragController,
    PaintableCell,
} from "./types/editor.js";
import type { SimulationSnapshot } from "./types/domain.js";
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
    createHistoryCommandsFn = createHistoryCommands,
    createLegacyDragControllerFn = createLegacyDragController,
    createEditorSessionControllerFn = createEditorSessionController,
    bindGridInteractionsFn = bindGridInteractionsToSurface,
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
    const runtimeState = state as AppState;
    const mutations = simulationMutations || createSimulationMutationsFn({
        mutationRunner,
        onError,
        applySimulationState,
        refreshState,
    });
    const armEditModeAction = typeof armEditMode === "function"
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
    const hideEditCueAction = typeof hideEditCue === "function"
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
    const setPatternStatusAction = typeof setPatternStatus === "function"
        ? setPatternStatus
        : (message: string, tone = "info") => {
            if (!state) {
                return;
            }
            setPatternStatusState(runtimeState, message, tone);
            renderControlPanel();
        };
    let consumeNextClick = false;
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

    function scheduleEditCueHide(): void {
        editCueToken += 1;
        const cueToken = editCueToken;
        setTimeoutFn(() => {
            if (cueToken !== editCueToken || !runtimeState.editArmed) {
                return;
            }
            hideEditCueAction();
        }, 2000);
    }

    function armEditingFromGrid(
        event: PointerEvent | MouseEvent | null,
        { suppressFollowupClick = false }: { suppressFollowupClick?: boolean } = {},
    ): true {
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
        consumeNextClick = Boolean(suppressFollowupClick);
        return true;
    }

    function currentTool(): string {
        return supportsEditorTools() ? getEditorTool() : EDITOR_TOOL_BRUSH;
    }

    function runningBrushEditingEnabled(): boolean {
        return supportsEditorTools() && editingBlockedByRun() && currentTool() === EDITOR_TOOL_BRUSH;
    }

    function runningAdvancedToolBlocked(): boolean {
        if (!supportsEditorTools() || !editingBlockedByRun()) {
            return false;
        }
        const tool = currentTool();
        return tool === EDITOR_TOOL_LINE || tool === EDITOR_TOOL_RECTANGLE || tool === EDITOR_TOOL_FILL;
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
        setCellsRequest,
        postControl,
        renderControlPanel,
        setPointerCapture,
        releasePointerCapture,
        runStateMutation: mutations.runStateMutation,
    }) as EditorSessionController;

    const legacyDrag = createLegacyDragControllerFn({
        getPaintState,
        previewPaintCells,
        clearPreview,
        setCellsRequest,
        runStateMutation: mutations.runStateMutation,
        setPointerCapture,
        releasePointerCapture,
        enableClickSuppression: () => editorSession.enableClickSuppression(),
    }) as LegacyDragController;

    const historyCommands = createHistoryCommandsFn({
        state: runtimeState,
        setCellsRequest,
        renderControlPanel,
        supportsEditorTools,
        runStateMutation: mutations.runStateMutation,
    }) as EditorHistoryCommands;

    function bindGridInteractions(): void {
        bindGridInteractionsFn({
            surfaceElement,
            resolveCellFromEvent,
            onPointerDown(event: PointerEvent, cell: PaintableCell) {
                if (runningBrushEditingEnabled()) {
                    void dismissOverlays();
                    hideEditCueAction();
                    event.preventDefault();
                    legacyDrag.begin(cell, event.pointerId);
                    return;
                }
                if (runningAdvancedToolBlocked()) {
                    blockRunningAdvancedTool(event);
                    consumeNextClick = true;
                    return;
                }
                if (supportsEditorTools() && editingBlockedByRun()) {
                    return;
                }
                if (supportsEditorTools() && !isEditArmed()) {
                    armEditingFromGrid(event, { suppressFollowupClick: true });
                    return;
                }
                void dismissOverlays();
                hideEditCueAction();
                if (!supportsEditorTools()) {
                    event.preventDefault();
                    legacyDrag.begin(cell, event.pointerId);
                    return;
                }

                if (currentTool() === EDITOR_TOOL_FILL) {
                    return;
                }

                event.preventDefault();
                void editorSession.beginPointerSession(cell, event.pointerId);
            },
            onPointerMove(event: PointerEvent, cell: PaintableCell) {
                const hasActivePointer = editorSession.isPointerActive() || legacyDrag.isActive();
                if (!hasActivePointer || (event.buttons & 1) === 0) {
                    return;
                }

                if (legacyDrag.isActive()) {
                    legacyDrag.update(cell);
                    return;
                }

                editorSession.handlePointerMove(cell);
            },
            onPointerUp() {
                if (consumeNextClick && supportsEditorTools() && !editorSession.isPointerActive() && !legacyDrag.isActive()) {
                    setTimeoutFn(() => {
                        consumeNextClick = false;
                    }, 0);
                }
                if (legacyDrag.isActive()) {
                    void legacyDrag.end();
                    return;
                }
                if (!supportsEditorTools()) {
                    void legacyDrag.end();
                    return;
                }

                void editorSession.handlePointerUp();
            },
            onPointerCancel() {
                consumeNextClick = false;
                if (legacyDrag.isActive()) {
                    void legacyDrag.end();
                    return;
                }
                if (!supportsEditorTools()) {
                    void legacyDrag.end();
                    return;
                }

                void editorSession.cancelActivePreview();
            },
            onClick(event: MouseEvent, cell: PaintableCell) {
                if (editorSession.isClickSuppressed()) {
                    event.preventDefault();
                    event.stopPropagation();
                    return;
                }
                if (consumeNextClick) {
                    consumeNextClick = false;
                    event.preventDefault();
                    event.stopPropagation();
                    return;
                }
                if (runningAdvancedToolBlocked()) {
                    blockRunningAdvancedTool(event);
                    return;
                }
                if (supportsEditorTools() && editingBlockedByRun()) {
                    event.preventDefault();
                    event.stopPropagation();
                    void dismissOverlays();
                    hideEditCueAction();
                    void paintCell(cell);
                    return;
                }
                if (supportsEditorTools() && !isEditArmed()) {
                    armEditingFromGrid(event);
                    return;
                }

                void dismissOverlays();
                hideEditCueAction();
                if (!supportsEditorTools()) {
                    void paintCell(cell);
                    return;
                }

                void editorSession.handleClick(cell);
            },
        });
    }

    async function paintCell(cell: PaintableCell, stateValue = getPaintState()): Promise<void> {
        if (typeof cell !== "object" || cell === null) {
            throw new Error("Cell painting requires a resolved topology cell.");
        }
        await mutations.runStateMutation(() => setCellRequest(cell, stateValue), { source: "editor" }).catch(() => null);
    }

    async function toggleCell(cell: PaintableCell): Promise<void> {
        if (typeof cell !== "object" || cell === null) {
            throw new Error("Cell toggles require a resolved topology cell.");
        }
        await mutations.runStateMutation(() => toggleCellRequest(cell), { source: "editor" }).catch(() => null);
    }

    async function sendControl(path: EmptyControlCommandPath, options?: SimulationMutationOptions): Promise<SimulationSnapshot | null>;
    async function sendControl(
        path: "/api/control/reset",
        body: ResetControlBody,
        options?: SimulationMutationOptions,
    ): Promise<SimulationSnapshot | null>;
    async function sendControl(
        path: "/api/config",
        body: ConfigSyncBody,
        options?: SimulationMutationOptions,
    ): Promise<SimulationSnapshot | null>;
    async function sendControl(
        path: EmptyControlCommandPath | "/api/control/reset" | "/api/config",
        bodyOrOptions?: ResetControlBody | ConfigSyncBody | SimulationMutationOptions,
        maybeOptions: SimulationMutationOptions = {},
    ): Promise<SimulationSnapshot | null> {
        if (path === "/api/control/reset") {
            const body = bodyOrOptions as ResetControlBody;
            return await mutations.runStateMutation(
                () => postControl(path, body),
                { source: "control", ...maybeOptions },
            ).catch(() => null);
        }
        if (path === "/api/config") {
            const body = bodyOrOptions as ConfigSyncBody;
            return await mutations.runStateMutation(
                () => postControl(path, body),
                { source: "control", ...maybeOptions },
            ).catch(() => null);
        }

        const options = (bodyOrOptions as SimulationMutationOptions | undefined) ?? {};
        return await mutations.runStateMutation(
            () => postControl(path),
            { source: "control", ...options },
        ).catch(() => null);
    }

    async function cancelActivePreview() {
        await editorSession.cancelActivePreview();
    }

    return {
        bindGridInteractions,
        toggleCell,
        sendControl,
        undo: () => historyCommands.undo(),
        redo: () => historyCommands.redo(),
        cancelActivePreview,
        runSerialized: (task, options = {}) => mutations.runSerialized(task, options),
    };
}
