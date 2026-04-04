import {
    EDITOR_TOOL_BRUSH,
    EDITOR_TOOL_LINE,
    EDITOR_TOOL_RECTANGLE,
} from "../editor-tools.js";
import type { PaintableCell, PreviewPaintCell } from "../types/editor.js";

function identifyCell(cell: PaintableCell): string | null {
    if (typeof cell?.id === "string" && cell.id.length > 0) {
        return cell.id;
    }
    return null;
}

export interface BrushEditorSession {
    kind: typeof EDITOR_TOOL_BRUSH;
    anchorCell: PaintableCell;
    currentCell: PaintableCell;
    pointerId: number | null;
    paintedCells: Map<string | null, PreviewPaintCell>;
    moved: boolean;
}

export interface ShapeEditorSession {
    kind: typeof EDITOR_TOOL_LINE | typeof EDITOR_TOOL_RECTANGLE;
    anchorCell: PaintableCell;
    currentCell: PaintableCell;
    pointerId: number | null;
    previewCells: PreviewPaintCell[];
}

export type ActiveEditorSession = BrushEditorSession | ShapeEditorSession;

export interface EditorPointerState {
    activeSession(): ActiveEditorSession | null;
    enableClickSuppression(): void;
    isClickSuppressed(): boolean;
    isPointerActive(): boolean;
    beginBrushSession(cell: PaintableCell, pointerId: number | null): void;
    updateBrushSession(cell: PaintableCell, nextCells: PreviewPaintCell[]): PreviewPaintCell[];
    endBrushSession(): BrushEditorSession | null;
    beginShapeSession(
        kind: typeof EDITOR_TOOL_LINE | typeof EDITOR_TOOL_RECTANGLE,
        cell: PaintableCell,
        pointerId: number | null,
    ): void;
    updateShapeSession(cell: PaintableCell, nextCells: PreviewPaintCell[]): PreviewPaintCell[];
    endShapeSession(): ShapeEditorSession | null;
    cancelActiveSession(): number | null;
}

export function createEditorPointerState(): EditorPointerState {
    let activePointerId: number | null = null;
    let suppressClick = false;
    let activeEditorSession: ActiveEditorSession | null = null;

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

    function updateBrushSession(cell: PaintableCell, nextCells: PreviewPaintCell[]): PreviewPaintCell[] {
        const session = activeEditorSession;
        if (!session || session.kind !== EDITOR_TOOL_BRUSH || nextCells.length === 0) {
            return [];
        }
        session.moved = true;
        nextCells.forEach((nextCell) => {
            session.paintedCells.set(nextCell.id || identifyCell(nextCell), nextCell);
        });
        session.currentCell = cell;
        return Array.from(session.paintedCells.values());
    }

    function endBrushSession(): BrushEditorSession | null {
        if (!activeEditorSession || activeEditorSession.kind !== EDITOR_TOOL_BRUSH) {
            return null;
        }
        const session = activeEditorSession;
        clearActiveEditorSession();
        return session;
    }

    function beginShapeSession(
        kind: typeof EDITOR_TOOL_LINE | typeof EDITOR_TOOL_RECTANGLE,
        cell: PaintableCell,
        pointerId: number | null,
    ): void {
        activeEditorSession = {
            kind,
            anchorCell: cell,
            currentCell: cell,
            pointerId: pointerId ?? null,
            previewCells: [],
        };
        activePointerId = pointerId ?? null;
    }

    function updateShapeSession(cell: PaintableCell, nextCells: PreviewPaintCell[]): PreviewPaintCell[] {
        const session = activeEditorSession;
        if (!session || (session.kind !== EDITOR_TOOL_LINE && session.kind !== EDITOR_TOOL_RECTANGLE)) {
            return [];
        }
        session.currentCell = cell;
        session.previewCells = nextCells;
        return session.previewCells;
    }

    function endShapeSession(): ShapeEditorSession | null {
        if (!activeEditorSession || (activeEditorSession.kind !== EDITOR_TOOL_LINE && activeEditorSession.kind !== EDITOR_TOOL_RECTANGLE)) {
            return null;
        }
        const session = activeEditorSession;
        clearActiveEditorSession();
        return session;
    }

    function cancelActiveSession(): number | null {
        const pointerId = activeEditorSession?.pointerId ?? activePointerId;
        clearActiveEditorSession();
        return pointerId ?? null;
    }

    return {
        activeSession: () => activeEditorSession,
        enableClickSuppression,
        isClickSuppressed: () => suppressClick,
        isPointerActive: () => activePointerId !== null,
        beginBrushSession,
        updateBrushSession,
        endBrushSession,
        beginShapeSession,
        updateShapeSession,
        endShapeSession,
        cancelActiveSession,
    };
}
