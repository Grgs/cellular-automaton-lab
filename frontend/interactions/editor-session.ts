import { buildBrushCells, buildEditorToolCells } from "../editor-operations.js";
import { buildCommittedEdit, pushUndoEntry } from "../editor-history.js";
import {
    DEFAULT_BRUSH_SIZE,
    DEFAULT_EDITOR_TOOL,
    EDITOR_TOOL_BRUSH,
    EDITOR_TOOL_FILL,
    EDITOR_TOOL_LINE,
    EDITOR_TOOL_RECTANGLE,
} from "../editor-tools.js";
import type {
    EditorSessionController,
    EditorSessionOptions,
    PaintableCell,
    PreviewPaintCell,
} from "../types/editor.js";
import type { SimulationSnapshot } from "../types/domain.js";

function identifyCell(cell: PaintableCell): string | null {
    if (typeof cell?.id === "string" && cell.id.length > 0) {
        return cell.id;
    }
    return null;
}

export function createEditorSessionController({
    state = null,
    getPaintState,
    getEditorTool = () => state?.selectedEditorTool ?? DEFAULT_EDITOR_TOOL,
    getBrushSize = () => state?.brushSize ?? DEFAULT_BRUSH_SIZE,
    previewPaintCells,
    clearPreview,
    setCellsRequest,
    postControl,
    renderControlPanel = () => {},
    setPointerCapture,
    releasePointerCapture,
    runStateMutation,
}: EditorSessionOptions): EditorSessionController {
    const runtimeState = state as NonNullable<EditorSessionOptions["state"]>;
    let activePointerId: number | null = null;
    let suppressClick = false;
    let activeEditorSession: (
        | {
            kind: typeof EDITOR_TOOL_BRUSH;
            anchorCell: PaintableCell;
            currentCell: PaintableCell;
            pointerId: number | null;
            paintedCells: Map<string | null, PreviewPaintCell>;
            moved: boolean;
        }
        | {
            kind: typeof EDITOR_TOOL_LINE | typeof EDITOR_TOOL_RECTANGLE;
            anchorCell: PaintableCell;
            currentCell: PaintableCell;
            pointerId: number | null;
            previewCells: PreviewPaintCell[];
        }
    ) | null = null;

    function supportsEditorTools(): boolean {
        return Boolean(state?.topology && state?.topologyIndex && Array.isArray(state?.cellStates));
    }

    function currentTool(): string {
        return supportsEditorTools() ? getEditorTool() : EDITOR_TOOL_BRUSH;
    }

    function clearActiveEditorSession(): void {
        activeEditorSession = null;
        activePointerId = null;
    }

    function enableClickSuppression(): void {
        suppressClick = true;
        window.setTimeout(() => {
            suppressClick = false;
        }, 0);
    }

    async function ensurePausedForEditing(): Promise<boolean> {
        if (!supportsEditorTools() || !state?.isRunning) {
            return true;
        }

        const pausedState = await runStateMutation(
            () => postControl("/api/control/pause"),
            { source: "control" },
        ).catch(() => null);
        return Boolean(pausedState);
    }

    async function commitEditorCells(cells: PreviewPaintCell[]): Promise<SimulationSnapshot | null> {
        const edit = buildCommittedEdit(runtimeState, cells);
        if (!edit) {
            return null;
        }

        const simulationState = await runStateMutation(
            () => setCellsRequest(edit.forwardCells),
            { recoverWithRefresh: true, source: "editor" },
        ).catch(() => null);
        if (simulationState) {
            pushUndoEntry(runtimeState, edit);
            renderControlPanel();
        }
        return simulationState;
    }

    function beginBrushSession(cell: PaintableCell, pointerId: number | null): void {
        activeEditorSession = {
            kind: EDITOR_TOOL_BRUSH,
            anchorCell: cell,
            currentCell: cell,
            pointerId: pointerId ?? null,
            paintedCells: new Map(),
            moved: false,
        };
        activePointerId = pointerId ?? null;
    }

    function updateBrushSession(cell: PaintableCell): void {
        const session = activeEditorSession;
        if (!session || session.kind !== EDITOR_TOOL_BRUSH) {
            return;
        }

        const nextCells = buildEditorToolCells(
            runtimeState,
            EDITOR_TOOL_LINE,
            session.currentCell,
            cell,
            getPaintState(),
            getBrushSize(),
        );
        if (nextCells.length === 0) {
            return;
        }

        session.moved = true;
        nextCells.forEach((nextCell) => {
            session.paintedCells.set(nextCell.id || identifyCell(nextCell), nextCell);
        });
        session.currentCell = cell;
        previewPaintCells(Array.from(session.paintedCells.values()));
    }

    async function endBrushSession(): Promise<SimulationSnapshot | null> {
        if (!activeEditorSession || activeEditorSession.kind !== EDITOR_TOOL_BRUSH) {
            return null;
        }

        const session = activeEditorSession;
        clearActiveEditorSession();
        releasePointerCapture(session.pointerId);

        try {
            if (!session.moved || session.paintedCells.size === 0) {
                return null;
            }
            enableClickSuppression();
            return await commitEditorCells(Array.from(session.paintedCells.values()));
        } finally {
            clearPreview();
        }
    }

    function beginShapeSession(
        tool: typeof EDITOR_TOOL_LINE | typeof EDITOR_TOOL_RECTANGLE,
        cell: PaintableCell,
        pointerId: number | null,
    ): void {
        activeEditorSession = {
            kind: tool,
            anchorCell: cell,
            currentCell: cell,
            pointerId: pointerId ?? null,
            previewCells: [],
        };
        activePointerId = pointerId ?? null;
    }

    function updateShapeSession(cell: PaintableCell): void {
        const session = activeEditorSession;
        if (!session || (session.kind !== EDITOR_TOOL_LINE && session.kind !== EDITOR_TOOL_RECTANGLE)) {
            return;
        }

        session.currentCell = cell;
        session.previewCells = buildEditorToolCells(
            runtimeState,
            session.kind,
            session.anchorCell,
            cell,
            getPaintState(),
            getBrushSize(),
        );
        previewPaintCells(session.previewCells);
    }

    async function endShapeSession(): Promise<SimulationSnapshot | null> {
        if (!activeEditorSession || (activeEditorSession.kind !== EDITOR_TOOL_LINE && activeEditorSession.kind !== EDITOR_TOOL_RECTANGLE)) {
            return null;
        }

        const session = activeEditorSession;
        clearActiveEditorSession();
        releasePointerCapture(session.pointerId);

        try {
            const cells = session.previewCells.length > 0
                ? session.previewCells
                : buildEditorToolCells(
                    runtimeState,
                    session.kind,
                    session.anchorCell,
                    session.currentCell || session.anchorCell,
                    getPaintState(),
                    getBrushSize(),
                );
            return await commitEditorCells(cells);
        } finally {
            clearPreview();
        }
    }

    async function beginPointerSession(cell: PaintableCell, pointerId: number | null): Promise<boolean> {
        if (!await ensurePausedForEditing()) {
            return false;
        }

        if (currentTool() === EDITOR_TOOL_BRUSH) {
            beginBrushSession(cell, pointerId);
            setPointerCapture(pointerId ?? null);
            return true;
        }

        const tool = currentTool();
        if (tool === EDITOR_TOOL_LINE || tool === EDITOR_TOOL_RECTANGLE) {
            beginShapeSession(tool, cell, pointerId);
            setPointerCapture(pointerId ?? null);
            return true;
        }

        return false;
    }

    async function commitBrushClick(cell: PaintableCell): Promise<SimulationSnapshot | null> {
        if (!await ensurePausedForEditing()) {
            return null;
        }
        return commitEditorCells(
            buildBrushCells(runtimeState, cell, getPaintState(), getBrushSize()),
        );
    }

    async function commitFillClick(cell: PaintableCell): Promise<SimulationSnapshot | null> {
        if (!await ensurePausedForEditing()) {
            return null;
        }
        return commitEditorCells(
            buildEditorToolCells(runtimeState, EDITOR_TOOL_FILL, cell, cell, getPaintState(), getBrushSize()),
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
        if (!activeEditorSession) {
            return;
        }
        releasePointerCapture((activeEditorSession.pointerId ?? activePointerId) ?? null);
        clearActiveEditorSession();
        clearPreview();
    }

    return {
        supportsEditorTools,
        currentTool,
        beginPointerSession: (cell, pointerId) => beginPointerSession(cell, pointerId ?? null),
        handlePointerMove(cell) {
            if (activeEditorSession?.kind === EDITOR_TOOL_BRUSH) {
                updateBrushSession(cell);
                return;
            }
            updateShapeSession(cell);
        },
        handlePointerUp() {
            if (activeEditorSession?.kind === EDITOR_TOOL_BRUSH) {
                return endBrushSession().catch(() => null);
            }
            return endShapeSession().catch(() => null);
        },
        handleClick: (cell) => handleClick(cell),
        cancelActivePreview,
        enableClickSuppression,
        isClickSuppressed: () => suppressClick,
        isPointerActive: () => activePointerId !== null,
    };
}
