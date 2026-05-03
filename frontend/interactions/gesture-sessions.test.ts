import { describe, expect, it, vi } from "vitest";

import { createPointerGestureRouter } from "./gesture-sessions.js";
import type { EditorTool } from "../editor-tools.js";
import type { PaintableCell } from "../types/editor.js";

function pointerEvent({
    button = 0,
    buttons = button === 2 ? 2 : 1,
    pointerId = 1,
}: {
    button?: number;
    buttons?: number;
    pointerId?: number;
} = {}) {
    const event: Partial<PointerEvent & MouseEvent> = {
        button,
        buttons,
        pointerId,
        preventDefault: vi.fn(),
        stopPropagation: vi.fn(),
    };
    return event as PointerEvent & MouseEvent;
}

function createRouter({
    supportsEditorTools = true,
    isEditArmed = false,
    currentTool = "brush",
    selectedCells = [],
}: {
    supportsEditorTools?: boolean;
    isEditArmed?: boolean;
    currentTool?: EditorTool;
    selectedCells?: PaintableCell[];
} = {}) {
    const paintDrag = {
        isActive: vi.fn(() => false),
        begin: vi.fn(),
        update: vi.fn(),
        end: vi.fn().mockResolvedValue(null),
        cancel: vi.fn().mockResolvedValue(null),
    };
    const editorSession = {
        isPointerActive: vi.fn(() => false),
        beginPointerSession: vi.fn().mockResolvedValue(true),
        handlePointerMove: vi.fn(),
        handlePointerUp: vi.fn().mockResolvedValue(null),
        cancelActivePreview: vi.fn().mockResolvedValue(undefined),
        isClickSuppressed: vi.fn(() => false),
        handleClick: vi.fn().mockResolvedValue({ handled: true }),
    };
    const getSelectedCells = vi.fn(() => selectedCells);
    const setSelectedCells = vi.fn();
    const setHoveredCell = vi.fn();
    const router = createPointerGestureRouter({
        surfaceElement: document.createElement("canvas"),
        editPolicy: {
            runningBrushEditingEnabled: () => false,
            dismissEditingUi: () => Promise.resolve(false),
            prepareDirectGridInteraction: vi.fn(),
            runningAdvancedToolBlocked: () => false,
            blockRunningAdvancedTool: vi.fn(),
            supportsEditorTools: () => supportsEditorTools,
            editingBlockedByRun: () => false,
            isEditArmed: () => isEditArmed,
            armEditingFromGrid: vi.fn(() => ({ consumeNextClick: false })),
            currentTool: () => currentTool,
        },
        editorSession,
        paintDrag,
        setHoveredCell,
        setSelectedCells,
        getSelectedCells,
        clearGestureOutline: vi.fn(),
        openInspectorDrawer: vi.fn(),
        renderControlPanel: vi.fn(),
        paintCell: vi.fn().mockResolvedValue(undefined),
        resolveDirectGestureTargetState: vi.fn(() => 2),
        setTimeoutFn: vi.fn(() => 1),
    });

    return {
        router,
        paintDrag,
        editorSession,
        getSelectedCells,
        setSelectedCells,
        setHoveredCell,
    };
}

describe("interactions/gesture-sessions", () => {
    it("starts unarmed left gestures with the selected paint state", () => {
        const { router, paintDrag } = createRouter({ isEditArmed: false });
        const firstCell: PaintableCell = { id: "cell:a", state: 0 };
        const secondCell: PaintableCell = { id: "cell:b", state: 9 };

        router.beginPointerDown(pointerEvent(), firstCell);
        router.handlePointerMove(pointerEvent({ buttons: 1 }), secondCell);

        expect(paintDrag.begin).toHaveBeenCalledWith(firstCell, 1, 2);
        expect(paintDrag.update).toHaveBeenCalledWith(secondCell);
    });

    it("routes armed pointer sessions through the editor session controller", () => {
        const { router, editorSession } = createRouter({ isEditArmed: true, currentTool: "line" });
        const firstCell: PaintableCell = { id: "cell:a" };
        const secondCell: PaintableCell = { id: "cell:b" };

        router.beginPointerDown(pointerEvent(), firstCell);
        router.handlePointerMove(pointerEvent({ buttons: 1 }), secondCell);
        router.handlePointerUp(pointerEvent());

        expect(editorSession.beginPointerSession).toHaveBeenCalledWith(firstCell, 1);
        expect(editorSession.handlePointerMove).toHaveBeenCalledWith(secondCell);
        expect(editorSession.handlePointerUp).toHaveBeenCalledTimes(1);
    });

    it("keeps left-button sessions bound to their original pointer id", () => {
        const { router, editorSession } = createRouter({ isEditArmed: true, currentTool: "line" });

        router.beginPointerDown(pointerEvent({ pointerId: 3 }), { id: "cell:a" });
        router.handlePointerMove(pointerEvent({ pointerId: 7, buttons: 1 }), { id: "cell:b" });
        router.handlePointerUp(pointerEvent({ pointerId: 7 }));
        router.handlePointerMove(pointerEvent({ pointerId: 3, buttons: 1 }), { id: "cell:c" });
        router.handlePointerUp(pointerEvent({ pointerId: 3 }));

        expect(editorSession.handlePointerMove).toHaveBeenCalledTimes(1);
        expect(editorSession.handlePointerMove).toHaveBeenCalledWith({ id: "cell:c" });
        expect(editorSession.handlePointerUp).toHaveBeenCalledTimes(1);
    });

    it("selects cells during right-drag and suppresses the follow-up context menu", () => {
        const firstCell: PaintableCell = { id: "cell:a" };
        const secondCell: PaintableCell = { id: "cell:b" };
        const { router, setSelectedCells } = createRouter();

        router.beginPointerDown(pointerEvent({ button: 2, pointerId: 9 }), firstCell);
        router.handlePointerMove(pointerEvent({ buttons: 2, pointerId: 9 }), secondCell);
        router.handlePointerUp(pointerEvent({ button: 2, pointerId: 9 }));
        router.handleContextMenu(secondCell);

        expect(setSelectedCells).toHaveBeenNthCalledWith(1, [firstCell]);
        expect(setSelectedCells).toHaveBeenNthCalledWith(2, [firstCell, secondCell]);
        expect(setSelectedCells).toHaveBeenCalledTimes(2);
    });

    it("reverts in-progress right-drag deselection on cancel", () => {
        const firstCell: PaintableCell = { id: "cell:a" };
        const secondCell: PaintableCell = { id: "cell:b" };
        const thirdCell: PaintableCell = { id: "cell:c" };
        const { router, setSelectedCells } = createRouter({
            selectedCells: [firstCell, secondCell, thirdCell],
        });

        router.beginPointerDown(pointerEvent({ button: 2, pointerId: 5 }), firstCell);
        router.handlePointerMove(pointerEvent({ buttons: 2, pointerId: 5 }), secondCell);
        router.handlePointerCancel(pointerEvent({ pointerId: 5 }));

        expect(setSelectedCells).toHaveBeenNthCalledWith(1, [secondCell, thirdCell]);
        expect(setSelectedCells).toHaveBeenNthCalledWith(2, [thirdCell]);
        expect(setSelectedCells).toHaveBeenNthCalledWith(3, [firstCell, secondCell, thirdCell]);
    });

    it("suppresses hover while a pointer session is active", () => {
        const { router, setHoveredCell } = createRouter();

        router.beginPointerDown(pointerEvent({ button: 2, pointerId: 1 }), { id: "cell:a" });
        router.handleHoverChange({ id: "cell:b" });

        expect(setHoveredCell).toHaveBeenLastCalledWith(null);
    });
});
