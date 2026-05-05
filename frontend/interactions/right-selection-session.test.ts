import { describe, expect, it, vi } from "vitest";

import { createRightSelectionGestureSession } from "./gesture-sessions/right-selection-session.js";
import type { PaintableCell } from "../types/editor.js";

function pointerEvent({
    pointerId = 1,
    buttons = 2,
}: {
    pointerId?: number;
    buttons?: number;
} = {}) {
    return {
        pointerId,
        buttons,
    } as PointerEvent;
}

function createSubject(selectedCells: PaintableCell[] = []) {
    const setSelectedCells = vi.fn();
    const openInspectorDrawer = vi.fn();
    const renderControlPanel = vi.fn();
    const prepareDirectGridInteraction = vi.fn();
    const surfaceElement = document.createElement("canvas");
    surfaceElement.setPointerCapture = vi.fn();
    surfaceElement.releasePointerCapture = vi.fn();

    const session = createRightSelectionGestureSession({
        event: pointerEvent({ pointerId: 7 }),
        initialCell: { id: "cell:a" },
        surfaceElement,
        editPolicy: {
            runningBrushEditingEnabled: () => false,
            dismissEditingUi: () => Promise.resolve(false),
            prepareDirectGridInteraction,
            runningAdvancedToolBlocked: () => false,
            blockRunningAdvancedTool: vi.fn(),
            supportsEditorTools: () => true,
            editingBlockedByRun: () => false,
            isEditArmed: () => false,
            armEditingFromGrid: vi.fn(() => ({ consumeNextClick: false })),
            currentTool: () => "brush",
        },
        getSelectedCells: () => selectedCells,
        setSelectedCells,
        openInspectorDrawer,
        renderControlPanel,
        onSuppressContextMenu: vi.fn(),
        onScheduleContextMenuReset: vi.fn(),
        onClearContextMenuSuppression: vi.fn(),
    });

    return {
        session,
        setSelectedCells,
        openInspectorDrawer,
        renderControlPanel,
        prepareDirectGridInteraction,
        surfaceElement,
    };
}

describe("interactions/right-selection-session", () => {
    it("selects new cells and refreshes the drawer state", () => {
        const {
            session,
            setSelectedCells,
            openInspectorDrawer,
            renderControlPanel,
            prepareDirectGridInteraction,
        } = createSubject();

        session.handleMove(pointerEvent({ pointerId: 7, buttons: 2 }), { id: "cell:b" });

        expect(prepareDirectGridInteraction).toHaveBeenCalledTimes(1);
        expect(setSelectedCells).toHaveBeenNthCalledWith(1, [{ id: "cell:a" }]);
        expect(setSelectedCells).toHaveBeenNthCalledWith(2, [{ id: "cell:a" }, { id: "cell:b" }]);
        expect(openInspectorDrawer).toHaveBeenCalledTimes(2);
        expect(renderControlPanel).toHaveBeenCalledTimes(2);
    });

    it("deselects cells when the gesture starts from an existing selection", () => {
        const initialCells = [{ id: "cell:a" }, { id: "cell:b" }, { id: "cell:c" }];
        const { session, setSelectedCells } = createSubject(initialCells);

        session.handleMove(pointerEvent({ pointerId: 7, buttons: 2 }), { id: "cell:b" });

        expect(setSelectedCells).toHaveBeenNthCalledWith(1, [{ id: "cell:b" }, { id: "cell:c" }]);
        expect(setSelectedCells).toHaveBeenNthCalledWith(2, [{ id: "cell:c" }]);
    });

    it("restores the original selection snapshot on cancel", () => {
        const initialCells = [{ id: "cell:a" }, { id: "cell:b" }, { id: "cell:c" }];
        const onClearContextMenuSuppression = vi.fn();
        const setSelectedCells = vi.fn();
        const renderControlPanel = vi.fn();
        const surfaceElement = document.createElement("canvas");
        surfaceElement.setPointerCapture = vi.fn();
        surfaceElement.releasePointerCapture = vi.fn();

        const session = createRightSelectionGestureSession({
            event: pointerEvent({ pointerId: 7 }),
            initialCell: { id: "cell:a" },
            surfaceElement,
            editPolicy: {
                runningBrushEditingEnabled: () => false,
                dismissEditingUi: () => Promise.resolve(false),
                prepareDirectGridInteraction: vi.fn(),
                runningAdvancedToolBlocked: () => false,
                blockRunningAdvancedTool: vi.fn(),
                supportsEditorTools: () => true,
                editingBlockedByRun: () => false,
                isEditArmed: () => false,
                armEditingFromGrid: vi.fn(() => ({ consumeNextClick: false })),
                currentTool: () => "brush",
            },
            getSelectedCells: () => initialCells,
            setSelectedCells,
            openInspectorDrawer: vi.fn(),
            renderControlPanel,
            onSuppressContextMenu: vi.fn(),
            onScheduleContextMenuReset: vi.fn(),
            onClearContextMenuSuppression,
        });

        session.handleMove(pointerEvent({ pointerId: 7, buttons: 2 }), { id: "cell:b" });
        session.cancel(pointerEvent({ pointerId: 7, buttons: 0 }));

        expect(setSelectedCells).toHaveBeenLastCalledWith(initialCells);
        expect(onClearContextMenuSuppression).toHaveBeenCalledTimes(1);
        expect(renderControlPanel).toHaveBeenCalledTimes(3);
    });

    it("ignores pointer events from another pointer id", () => {
        const { session, setSelectedCells } = createSubject();

        session.handleMove(pointerEvent({ pointerId: 8, buttons: 2 }), { id: "cell:b" });
        expect(session.handleUp(pointerEvent({ pointerId: 8, buttons: 0 }))).toBe(false);
        expect(session.cancel(pointerEvent({ pointerId: 8, buttons: 0 }))).toBe(false);

        expect(setSelectedCells).toHaveBeenCalledTimes(1);
        expect(setSelectedCells).toHaveBeenCalledWith([{ id: "cell:a" }]);
    });
});
