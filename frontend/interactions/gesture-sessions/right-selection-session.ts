import type { PaintableCell } from "../../types/editor.js";
import {
    cloneSelectedCells,
    identifyGestureCell,
    matchesGesturePointer,
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
        kind: "right-selection",
        handleMove(moveEvent, cell) {
            if (!matchesGesturePointer(pointerId, moveEvent) || (moveEvent.buttons & 2) === 0) {
                return;
            }
            updateSelection(cell);
        },
        handleUp(upEvent) {
            if (!matchesGesturePointer(pointerId, upEvent)) {
                return false;
            }
            releaseSurfacePointerCapture(surfaceElement, pointerId);
            onScheduleContextMenuReset();
            return true;
        },
        cancel(cancelEvent) {
            if (!matchesGesturePointer(pointerId, cancelEvent)) {
                return false;
            }
            setSelectedCells(Array.from(initialCells.values()));
            releaseSurfacePointerCapture(surfaceElement, pointerId);
            onClearContextMenuSuppression();
            renderControlPanel();
            return true;
        },
    };
}
