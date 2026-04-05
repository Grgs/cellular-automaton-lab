import { createDragPaintSession } from "../drag-session.js";
import type { LegacyDragController, LegacyDragOptions } from "../types/editor.js";

export function createLegacyDragController({
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
    enableClickSuppression,
}: LegacyDragOptions): LegacyDragController {
    const dragSession = createDragPaintSession();
    let activePointerId: number | null = null;
    let activeGestureTone: "paint" | "erase" | null = null;

    function begin(
        cell: Parameters<typeof dragSession.start>[0],
        pointerId?: number | null,
        paintStateOverride?: number,
    ): void {
        const paintState = paintStateOverride ?? getPaintState();
        dragSession.start(cell, paintState, pointerId ?? null);
        activePointerId = pointerId ?? null;
        activeGestureTone = paintState === 0 ? "erase" : "paint";
        setPointerCapture(activePointerId);
    }

    function update(cell: Parameters<typeof dragSession.update>[0]): void {
        const updateState = dragSession.update(cell);
        if (updateState.changed) {
            previewPaintCells(updateState.previewCells);
            if (activeGestureTone) {
                setGestureOutline(updateState.previewCells, activeGestureTone);
            }
        }
    }

    async function end() {
        if (activePointerId === null) {
            return null;
        }

        const dragState = dragSession.end();
        const pointerId = activePointerId;
        const gestureTone = activeGestureTone;
        activePointerId = null;
        activeGestureTone = null;
        if (!dragState) {
            return null;
        }

        releasePointerCapture(pointerId);

        if (dragState.moved) {
            enableClickSuppression();
        }

        clearGestureOutline();
        try {
            if (dragState.moved && dragState.paintedCells.length > 0) {
                const result = await runStateMutation(
                    () => setCellsRequest(dragState.paintedCells),
                    { recoverWithRefresh: true, source: "editor" },
                );
                return result;
            }
            return null;
        } finally {
            clearPreview();
            if (dragState.moved && dragState.paintedCells.length > 0 && gestureTone) {
                flashGestureOutline(dragState.paintedCells, gestureTone, 150);
            }
        }
    }

    async function cancel(): Promise<null> {
        if (activePointerId === null) {
            clearGestureOutline();
            clearPreview();
            return null;
        }
        const pointerId = activePointerId;
        activePointerId = null;
        activeGestureTone = null;
        dragSession.end();
        releasePointerCapture(pointerId);
        clearGestureOutline();
        clearPreview();
        return null;
    }

    return {
        begin,
        update,
        end: () => end().catch(() => null),
        cancel: () => cancel().catch(() => null),
        isActive: () => activePointerId !== null,
        currentPointerId: () => activePointerId,
    };
}
