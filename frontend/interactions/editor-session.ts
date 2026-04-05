import { buildBrushCells, buildEditorToolCells } from "../editor-operations.js";
import {
    DEFAULT_BRUSH_SIZE,
    DEFAULT_EDITOR_TOOL,
    EDITOR_TOOL_BRUSH,
    EDITOR_TOOL_FILL,
    EDITOR_TOOL_LINE,
    EDITOR_TOOL_RECTANGLE,
} from "../editor-tools.js";
import type { EditorTool } from "../editor-tools.js";
import type {
    EditorSessionController,
    EditorSessionOptions,
    PaintableCell,
} from "../types/editor.js";
import { createEditorCommitRuntime } from "./editor-session-commit.js";
import { createEditorPointerState } from "./editor-session-state.js";
import type { ShapeEditorSession } from "./editor-session-state.js";

export function createEditorSessionController({
    state = null,
    getPaintState,
    getEditorTool = () => state?.selectedEditorTool ?? DEFAULT_EDITOR_TOOL,
    getBrushSize = () => state?.brushSize ?? DEFAULT_BRUSH_SIZE,
    previewPaintCells,
    clearPreview,
    setGestureOutline,
    flashGestureOutline,
    clearGestureOutline,
    setCellsRequest,
    postControl,
    renderControlPanel = () => {},
    setPointerCapture,
    releasePointerCapture,
    runStateMutation,
}: EditorSessionOptions): EditorSessionController {
    const runtimeState = state as NonNullable<EditorSessionOptions["state"]>;
    const pointerState = createEditorPointerState();

    function supportsEditorTools(): boolean {
        return Boolean(state?.topology && state?.topologyIndex && Array.isArray(state?.cellStates));
    }

    function currentTool(): EditorTool {
        return supportsEditorTools() ? getEditorTool() : EDITOR_TOOL_BRUSH;
    }

    const commitRuntime = createEditorCommitRuntime({
        state: runtimeState,
        postControl,
        setCellsRequest,
        renderControlPanel,
        runStateMutation,
        supportsEditorTools,
        isRunning: () => Boolean(state?.isRunning),
    });

    async function beginPointerSession(cell: PaintableCell, pointerId: number | null): Promise<boolean> {
        if (!await commitRuntime.ensurePausedForEditing()) {
            return false;
        }

        if (currentTool() === EDITOR_TOOL_BRUSH) {
            pointerState.beginBrushSession(cell, pointerId);
            setPointerCapture(pointerId ?? null);
            return true;
        }

        const tool = currentTool();
        if (tool === EDITOR_TOOL_LINE || tool === EDITOR_TOOL_RECTANGLE) {
            pointerState.beginShapeSession(tool, cell, pointerId);
            setPointerCapture(pointerId ?? null);
            return true;
        }

        return false;
    }

    async function commitBrushClick(cell: PaintableCell) {
        if (!await commitRuntime.ensurePausedForEditing()) {
            return null;
        }
        clearGestureOutline();
        return commitRuntime.commitEditorCells(
            buildBrushCells(runtimeState, cell, getPaintState(), getBrushSize()),
        );
    }

    async function commitFillClick(cell: PaintableCell) {
        if (!await commitRuntime.ensurePausedForEditing()) {
            return null;
        }
        clearGestureOutline();
        return commitRuntime.commitEditorCells(
            buildEditorToolCells(runtimeState, EDITOR_TOOL_FILL, cell, cell, getPaintState(), getBrushSize()),
        );
    }

    function buildShapeCells(session: ShapeEditorSession) {
        return session.previewCells.length > 0
            ? session.previewCells
            : buildEditorToolCells(
                runtimeState,
                session.kind,
                session.anchorCell,
                session.currentCell || session.anchorCell,
                getPaintState(),
                getBrushSize(),
            );
    }

    async function handleClick(cell: PaintableCell): Promise<{ handled: boolean }> {
        const tool = currentTool();
        if (tool === EDITOR_TOOL_BRUSH) {
            await commitBrushClick(cell);
            return { handled: true };
        }
        if (tool === EDITOR_TOOL_FILL) {
            await commitFillClick(cell);
            return { handled: true };
        }
        return { handled: false };
    }

    async function cancelActivePreview(): Promise<void> {
        const pointerId = pointerState.cancelActiveSession();
        if (pointerId !== null) {
            releasePointerCapture(pointerId);
        }
        clearGestureOutline();
        clearPreview();
    }

    return {
        supportsEditorTools,
        currentTool,
        beginPointerSession: (cell, pointerId) => beginPointerSession(cell, pointerId ?? null),
        handlePointerMove(cell) {
            const activeSession = pointerState.activeSession();
            if (!activeSession) {
                return;
            }
            if (activeSession.kind === EDITOR_TOOL_BRUSH) {
                const nextCells = buildEditorToolCells(
                    runtimeState,
                    EDITOR_TOOL_LINE,
                    activeSession.currentCell,
                    cell,
                    getPaintState(),
                    getBrushSize(),
                );
                const previewCells = pointerState.updateBrushSession(cell, nextCells);
                if (previewCells.length > 0) {
                    previewPaintCells(previewCells);
                    setGestureOutline(previewCells, "paint");
                }
                return;
            }
            const previewCells = pointerState.updateShapeSession(
                cell,
                buildEditorToolCells(
                    runtimeState,
                    activeSession.kind,
                    activeSession.anchorCell,
                    cell,
                    getPaintState(),
                    getBrushSize(),
                ),
            );
            previewPaintCells(previewCells);
            if (previewCells.length > 0) {
                setGestureOutline(previewCells, "paint");
            }
        },
        handlePointerUp() {
            const activeSession = pointerState.activeSession();
            if (!activeSession) {
                return Promise.resolve(null);
            }
            if (activeSession.kind === EDITOR_TOOL_BRUSH) {
                const session = pointerState.endBrushSession();
                if (!session) {
                    return Promise.resolve(null);
                }
                releasePointerCapture(session.pointerId);
                clearGestureOutline();
                return commitRuntime.commitEditorCells(
                    !session.moved || session.paintedCells.size === 0
                        ? []
                        : Array.from(session.paintedCells.values()),
                ).then((result) => {
                    if (session.moved && session.paintedCells.size > 0) {
                        pointerState.enableClickSuppression();
                    }
                    return result;
                }).catch(() => null).finally(() => {
                    clearPreview();
                    if (session.moved && session.paintedCells.size > 0) {
                        flashGestureOutline(Array.from(session.paintedCells.values()), "paint", 150);
                    }
                });
            }

            const session = pointerState.endShapeSession();
            if (!session) {
                return Promise.resolve(null);
            }
            releasePointerCapture(session.pointerId);
            const shapeCells = buildShapeCells(session);
            clearGestureOutline();
            return commitRuntime.commitEditorCells(shapeCells).catch(() => null).finally(() => {
                clearPreview();
                if (session.moved && shapeCells.length > 0) {
                    flashGestureOutline(shapeCells, "paint", 150);
                }
            });
        },
        handleClick: (cell) => handleClick(cell),
        cancelActivePreview,
        enableClickSuppression: () => pointerState.enableClickSuppression(),
        isClickSuppressed: () => pointerState.isClickSuppressed(),
        isPointerActive: () => pointerState.isPointerActive(),
    };
}
