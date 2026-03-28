import { createDragPaintSession } from "../drag-session.js";
import type { LegacyDragController, LegacyDragOptions } from "../types/editor.js";

export function createLegacyDragController({
    getPaintState,
    previewPaintCells,
    clearPreview,
    setCellsRequest,
    runStateMutation,
    setPointerCapture,
    releasePointerCapture,
    enableClickSuppression,
}: LegacyDragOptions): LegacyDragController {
    const dragSession = createDragPaintSession();
    let activePointerId: number | null = null;

    function begin(cell: Parameters<typeof dragSession.start>[0], pointerId?: number | null): void {
        dragSession.start(cell, getPaintState(), pointerId ?? null);
        activePointerId = pointerId ?? null;
        setPointerCapture(activePointerId);
    }

    function update(cell: Parameters<typeof dragSession.update>[0]): void {
        const updateState = dragSession.update(cell);
        if (updateState.changed) {
            previewPaintCells(updateState.previewCells);
        }
    }

    async function end() {
        if (activePointerId === null) {
            return null;
        }

        const dragState = dragSession.end();
        const pointerId = activePointerId;
        activePointerId = null;
        if (!dragState) {
            return null;
        }

        releasePointerCapture(pointerId);

        if (dragState.moved) {
            enableClickSuppression();
        }

        try {
            if (dragState.moved && dragState.paintedCells.length > 0) {
                return await runStateMutation(
                    () => setCellsRequest(dragState.paintedCells),
                    { recoverWithRefresh: true, source: "editor" },
                );
            }
            return null;
        } finally {
            clearPreview();
        }
    }

    return {
        begin,
        update,
        end: () => end().catch(() => null),
        isActive: () => activePointerId !== null,
        currentPointerId: () => activePointerId,
    };
}
