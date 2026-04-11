import type { PaintableCell } from "../../types/editor.js";
import {
    cloneSelectedCells,
    identifyGestureCell,
    releaseSurfacePointerCapture,
    setSurfacePointerCapture,
} from "./helpers.js";
import type { PointerGestureSession, RightSelectionGestureSessionOptions } from "./types.js";

export function createRightSelectionGestureSession({
    event,
    initialCell,
    surfaceElement,
    editPolicy,
    getSelectedCells,
    setSelectedCells,
    openInspectorDrawer,
    renderControlPanel,
    onSuppressContextMenu,
    onScheduleContextMenuReset,
    onClearContextMenuSuppression,
}: RightSelectionGestureSessionOptions): PointerGestureSession {
    const pointerId = event.pointerId ?? null;
    const initialCells = cloneSelectedCells(getSelectedCells());
    const workingCells = new Map(initialCells);
    const initialCellKey = identifyGestureCell(initialCell);
    const mode: "select" | "deselect" = initialCells.has(initialCellKey) ? "deselect" : "select";

    function updateSelection(cell: PaintableCell): void {
        const cellKey = identifyGestureCell(cell);
        const hasCell = workingCells.has(cellKey);
        if (mode === "select") {
            if (hasCell) {
                return;
            }
            workingCells.set(cellKey, { ...cell });
        } else {
            if (!hasCell) {
                return;
            }
            workingCells.delete(cellKey);
        }
        const nextSelectedCells = Array.from(workingCells.values());
        setSelectedCells(nextSelectedCells);
        if (nextSelectedCells.length > 0) {
            openInspectorDrawer();
        }
        renderControlPanel();
    }

    editPolicy.prepareDirectGridInteraction(event);
    onSuppressContextMenu();
    setSurfacePointerCapture(surfaceElement, pointerId);
    updateSelection(initialCell);

    return {
        pointerId,
        handleMove(moveEvent, cell) {
            if (moveEvent.pointerId !== pointerId || (moveEvent.buttons & 2) === 0) {
                return;
            }
            updateSelection(cell);
        },
        handleUp(upEvent) {
            if (upEvent.pointerId !== pointerId) {
                return;
            }
            releaseSurfacePointerCapture(surfaceElement, pointerId);
            onScheduleContextMenuReset();
        },
        cancel(cancelEvent) {
            if (cancelEvent.pointerId !== pointerId) {
                return;
            }
            setSelectedCells(Array.from(initialCells.values()));
            releaseSurfacePointerCapture(surfaceElement, pointerId);
            onClearContextMenuSuppression();
            renderControlPanel();
        },
        isActive: () => true,
    };
}
