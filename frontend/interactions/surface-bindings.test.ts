import { beforeEach, describe, expect, it, vi } from "vitest";

import { createInteractionSurfaceBindings } from "./surface-bindings.js";
import type { GridInteractionBindings, PaintableCell } from "../types/editor.js";

function createEventStub({
    button = 0,
    buttons = button === 2 ? 2 : 1,
    pointerId = 1,
}: {
    button?: number;
    buttons?: number;
    pointerId?: number;
} = {}) {
    return {
        preventDefault: vi.fn(),
        stopPropagation: vi.fn(),
        button,
        buttons,
        pointerId,
    } as unknown as PointerEvent & MouseEvent;
}

interface SurfaceBindingSubjectOptions {
    supportsEditorTools?: boolean;
    isEditArmed?: boolean;
    editingBlockedByRun?: boolean;
    runningAdvancedToolBlocked?: boolean;
    runningBrushEditingEnabled?: boolean;
}

function createSubject({
    supportsEditorTools = false,
    isEditArmed = true,
    editingBlockedByRun = false,
    runningAdvancedToolBlocked = false,
    runningBrushEditingEnabled = false,
}: SurfaceBindingSubjectOptions = {}): {
    handlers: GridInteractionBindings;
    setHoveredCell: ReturnType<typeof vi.fn>;
    setSelectedCells: ReturnType<typeof vi.fn>;
    getSelectedCells: ReturnType<typeof vi.fn>;
    clearGestureOutline: ReturnType<typeof vi.fn>;
    openInspectorDrawer: ReturnType<typeof vi.fn>;
    renderControlPanel: ReturnType<typeof vi.fn>;
    paintCell: ReturnType<typeof vi.fn>;
    resolveDirectGestureTargetState: ReturnType<typeof vi.fn>;
    beginPointerSession: ReturnType<typeof vi.fn>;
    legacyBegin: ReturnType<typeof vi.fn>;
    armEditingFromGrid: ReturnType<typeof vi.fn>;
    prepareDirectGridInteraction: ReturnType<typeof vi.fn>;
    blockRunningAdvancedTool: ReturnType<typeof vi.fn>;
    editorPointerActive: ReturnType<typeof vi.fn>;
    legacyPointerActive: ReturnType<typeof vi.fn>;
} {
    let handlers: GridInteractionBindings | null = null;
    const setHoveredCell = vi.fn();
    const setSelectedCells = vi.fn();
    const getSelectedCells = vi.fn(() => []);
    const clearGestureOutline = vi.fn(() => undefined);
    const openInspectorDrawer = vi.fn();
    const renderControlPanel = vi.fn();
    const editorPointerActive = vi.fn(() => false);
    const legacyPointerActive = vi.fn(() => false);
    const paintCell = vi.fn().mockResolvedValue(undefined);
    const resolveDirectGestureTargetState = vi.fn((cell: PaintableCell) => (cell.state ?? 0) === 0 ? 2 : 0);
    const beginPointerSession = vi.fn().mockResolvedValue(true);
    const legacyBegin = vi.fn();
    const armEditingFromGrid = vi.fn(() => ({ consumeNextClick: false }));
    const prepareDirectGridInteraction = vi.fn();
    const blockRunningAdvancedTool = vi.fn();

    const bindings = createInteractionSurfaceBindings({
        surfaceElement: document.createElement("canvas"),
        resolveCellFromEvent: () => ({ id: "square:1:1", x: 1, y: 1 }),
        editPolicy: {
            runningBrushEditingEnabled: () => runningBrushEditingEnabled,
            dismissEditingUi: () => Promise.resolve(false),
            prepareDirectGridInteraction,
            runningAdvancedToolBlocked: () => runningAdvancedToolBlocked,
            blockRunningAdvancedTool,
            supportsEditorTools: () => supportsEditorTools,
            editingBlockedByRun: () => editingBlockedByRun,
            isEditArmed: () => isEditArmed,
            armEditingFromGrid,
            currentTool: () => "brush",
        },
        editorSession: {
            isPointerActive: editorPointerActive,
            beginPointerSession,
            handlePointerMove: vi.fn(),
            handlePointerUp: vi.fn().mockResolvedValue(null),
            cancelActivePreview: vi.fn().mockResolvedValue(undefined),
            isClickSuppressed: vi.fn(() => false),
            handleClick: vi.fn().mockResolvedValue({ handled: true }),
        },
        legacyDrag: {
            isActive: legacyPointerActive,
            begin: legacyBegin,
            update: vi.fn(),
            end: vi.fn().mockResolvedValue(null),
            cancel: vi.fn().mockResolvedValue(null),
        },
        setHoveredCell,
        setSelectedCells,
        getSelectedCells,
        clearGestureOutline,
        openInspectorDrawer,
        renderControlPanel,
        paintCell,
        resolveDirectGestureTargetState,
        bindGridInteractionsFn(options) {
            handlers = options;
        },
    });
    bindings.bindGridInteractions();

    const capturedHandlers = handlers;
    if (!capturedHandlers) {
        throw new Error("Expected interaction handlers to be captured.");
    }

    return {
        handlers: capturedHandlers,
        setHoveredCell,
        setSelectedCells,
        getSelectedCells,
        clearGestureOutline,
        openInspectorDrawer,
        renderControlPanel,
        paintCell,
        resolveDirectGestureTargetState,
        beginPointerSession,
        legacyBegin,
        armEditingFromGrid,
        prepareDirectGridInteraction,
        blockRunningAdvancedTool,
        editorPointerActive,
        legacyPointerActive,
    };
}

describe("interactions/surface-bindings", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
    });

    it("clears hover on pointer down before interaction handling", () => {
        const { handlers, setHoveredCell, clearGestureOutline } = createSubject();

        handlers.onPointerDown(createEventStub(), { id: "square:1:1", x: 1, y: 1 });

        expect(setHoveredCell).toHaveBeenCalledWith(null);
        expect(clearGestureOutline).toHaveBeenCalledTimes(1);
    });

    it("suppresses hover updates while a pointer interaction is active", () => {
        const { handlers, setHoveredCell, editorPointerActive, legacyPointerActive } = createSubject();
        const cell: PaintableCell = { id: "square:1:1", x: 1, y: 1 };

        editorPointerActive.mockReturnValue(true);
        handlers.onHoverChange(cell);
        expect(setHoveredCell).toHaveBeenLastCalledWith(null);

        editorPointerActive.mockReturnValue(false);
        legacyPointerActive.mockReturnValue(true);
        handlers.onHoverChange(cell);
        expect(setHoveredCell).toHaveBeenLastCalledWith(null);
    });

    it("restores hover updates when the surface is idle again", () => {
        const { handlers, setHoveredCell } = createSubject();
        const cell: PaintableCell = { id: "square:1:1", x: 1, y: 1 };

        handlers.onHoverChange(cell);

        expect(setHoveredCell).toHaveBeenLastCalledWith(cell);
    });

    it("does not arm edit mode or start pointer editing on unarmed pointer down", () => {
        const { handlers, beginPointerSession, legacyBegin, armEditingFromGrid, prepareDirectGridInteraction } = createSubject({
            supportsEditorTools: true,
            isEditArmed: false,
        });
        const deadCell: PaintableCell = { id: "square:1:1", x: 1, y: 1, state: 0 };

        handlers.onPointerDown(createEventStub(), deadCell);

        expect(beginPointerSession).not.toHaveBeenCalled();
        expect(prepareDirectGridInteraction).toHaveBeenCalledTimes(1);
        expect(legacyBegin).toHaveBeenCalledWith(deadCell, 1, 2);
        expect(armEditingFromGrid).not.toHaveBeenCalled();
    });

    it("applies the first-cell target state on unarmed left click", () => {
        const { handlers, paintCell, prepareDirectGridInteraction } = createSubject({
            supportsEditorTools: true,
            isEditArmed: false,
        });
        const cell: PaintableCell = { id: "square:1:1", x: 1, y: 1, state: 0 };

        handlers.onPointerDown(createEventStub(), cell);
        handlers.onClick(createEventStub(), cell);

        expect(prepareDirectGridInteraction).toHaveBeenCalledTimes(1);
        expect(paintCell).toHaveBeenCalledWith(cell, 2);
    });

    it("erases from the first-cell target state on unarmed left click", () => {
        const { handlers, paintCell } = createSubject({
            supportsEditorTools: true,
            isEditArmed: false,
        });
        const liveCell: PaintableCell = { id: "square:1:1", x: 1, y: 1, state: 3 };

        handlers.onPointerDown(createEventStub(), liveCell);
        handlers.onClick(createEventStub(), liveCell);

        expect(paintCell).toHaveBeenCalledWith(liveCell, 0);
    });

    it("does not block unarmed gestures with running advanced-tool messaging", () => {
        const { handlers, legacyBegin, blockRunningAdvancedTool } = createSubject({
            supportsEditorTools: true,
            isEditArmed: false,
            runningAdvancedToolBlocked: true,
            editingBlockedByRun: true,
        });
        const cell: PaintableCell = { id: "square:1:1", x: 1, y: 1, state: 0 };

        handlers.onPointerDown(createEventStub(), cell);

        expect(blockRunningAdvancedTool).not.toHaveBeenCalled();
        expect(legacyBegin).toHaveBeenCalledWith(cell, 1, 2);
    });

    it("uses the original pointer-down target state for a mixed unarmed drag gesture", () => {
        const { handlers, legacyBegin, resolveDirectGestureTargetState } = createSubject({
            supportsEditorTools: true,
            isEditArmed: false,
        });
        const originCell: PaintableCell = { id: "square:1:1", x: 1, y: 1, state: 5 };

        handlers.onPointerDown(createEventStub(), originCell);
        handlers.onPointerMove({ buttons: 1 } as PointerEvent, { id: "square:2:1", x: 2, y: 1, state: 0 });

        expect(resolveDirectGestureTargetState).toHaveBeenCalledWith(originCell);
        expect(legacyBegin).toHaveBeenCalledWith(originCell, 1, 0);
    });

    it("keeps armed clicks on the editor-session path", () => {
        const { handlers, resolveDirectGestureTargetState, paintCell } = createSubject({
            supportsEditorTools: true,
            isEditArmed: true,
        });

        const event = createEventStub();
        handlers.onClick(event, { id: "square:1:1", x: 1, y: 1 });

        expect(resolveDirectGestureTargetState).not.toHaveBeenCalled();
        expect(paintCell).not.toHaveBeenCalled();
    });

    it("keeps the persistent selection unchanged during left-click interactions", () => {
        const { handlers, setSelectedCells } = createSubject({
            supportsEditorTools: true,
            isEditArmed: false,
        });
        const cell: PaintableCell = { id: "square:1:1", x: 1, y: 1, state: 0 };

        handlers.onPointerDown(createEventStub(), cell);
        handlers.onClick(createEventStub(), cell);

        expect(setSelectedCells).not.toHaveBeenCalled();
    });

    it("keeps armed running brush interactions on the legacy paint path", () => {
        const { handlers, legacyBegin, resolveDirectGestureTargetState } = createSubject({
            supportsEditorTools: true,
            isEditArmed: true,
            editingBlockedByRun: true,
            runningBrushEditingEnabled: true,
        });
        const cell: PaintableCell = { id: "square:1:1", x: 1, y: 1, state: 5 };

        handlers.onPointerDown(createEventStub(), cell);

        expect(legacyBegin).toHaveBeenCalledWith(cell, 1);
        expect(resolveDirectGestureTargetState).not.toHaveBeenCalled();
    });

    it("clears the gesture outline and cancels legacy drag on pointer cancel", () => {
        const clearGestureOutlineSpy = vi.fn(() => undefined);
        const cancel = vi.fn().mockResolvedValue(null);
        const legacyActive = vi.fn(() => true);
        const localHandlers = createInteractionSurfaceBindings({
            surfaceElement: document.createElement("canvas"),
            resolveCellFromEvent: () => ({ id: "square:1:1", x: 1, y: 1 }),
            editPolicy: {
                runningBrushEditingEnabled: () => false,
                dismissEditingUi: () => Promise.resolve(false),
                prepareDirectGridInteraction: vi.fn(),
                runningAdvancedToolBlocked: () => false,
                blockRunningAdvancedTool: vi.fn(),
                supportsEditorTools: () => false,
                editingBlockedByRun: () => false,
                isEditArmed: () => false,
                armEditingFromGrid: vi.fn(() => ({ consumeNextClick: false })),
                currentTool: () => "brush",
            },
            editorSession: {
                isPointerActive: vi.fn(() => false),
                beginPointerSession: vi.fn().mockResolvedValue(true),
                handlePointerMove: vi.fn(),
                handlePointerUp: vi.fn().mockResolvedValue(null),
                cancelActivePreview: vi.fn().mockResolvedValue(undefined),
                isClickSuppressed: vi.fn(() => false),
                handleClick: vi.fn().mockResolvedValue({ handled: true }),
            },
            legacyDrag: {
                isActive: legacyActive,
                begin: vi.fn(),
                update: vi.fn(),
                end: vi.fn().mockResolvedValue(null),
                cancel,
            },
            setHoveredCell: vi.fn(),
            setSelectedCells: vi.fn(),
            getSelectedCells: vi.fn(() => []),
            clearGestureOutline: clearGestureOutlineSpy,
            openInspectorDrawer: vi.fn(),
            renderControlPanel: vi.fn(),
            paintCell: vi.fn().mockResolvedValue(undefined),
            resolveDirectGestureTargetState: vi.fn(() => 1),
            bindGridInteractionsFn(options) {
                options.onPointerCancel({} as PointerEvent);
            },
        });

        localHandlers.bindGridInteractions();

        expect(clearGestureOutlineSpy).toHaveBeenCalled();
        expect(cancel).toHaveBeenCalledTimes(1);
    });

    it("selects a cell on right-button pointer down", () => {
        const { handlers, setSelectedCells, openInspectorDrawer, renderControlPanel } = createSubject();
        const cell: PaintableCell = { id: "square:1:1", x: 1, y: 1 };

        handlers.onPointerDown({ button: 2, pointerId: 7 } as PointerEvent, cell);

        expect(setSelectedCells).toHaveBeenCalledWith([cell]);
        expect(openInspectorDrawer).toHaveBeenCalledTimes(1);
        expect(renderControlPanel).toHaveBeenCalledTimes(1);
    });

    it("adds multiple cells during a right-drag select gesture", () => {
        const { handlers, setSelectedCells, openInspectorDrawer, renderControlPanel } = createSubject();
        const firstCell: PaintableCell = { id: "square:1:1", x: 1, y: 1 };
        const secondCell: PaintableCell = { id: "square:2:1", x: 2, y: 1 };

        handlers.onPointerDown({ button: 2, pointerId: 9 } as PointerEvent, firstCell);
        handlers.onPointerMove({ buttons: 2, pointerId: 9 } as PointerEvent, secondCell);
        handlers.onPointerUp({ button: 2, pointerId: 9 } as PointerEvent);
        handlers.onContextMenu(secondCell);

        expect(setSelectedCells).toHaveBeenNthCalledWith(1, [firstCell]);
        expect(setSelectedCells).toHaveBeenNthCalledWith(2, [firstCell, secondCell]);
        expect(setSelectedCells).toHaveBeenCalledTimes(2);
        expect(openInspectorDrawer).toHaveBeenCalledTimes(2);
        expect(renderControlPanel).toHaveBeenCalledTimes(2);
    });

    it("removes multiple cells during a right-drag deselect gesture", () => {
        const firstCell: PaintableCell = { id: "square:1:1", x: 1, y: 1 };
        const secondCell: PaintableCell = { id: "square:2:2", x: 2, y: 2 };
        const thirdCell: PaintableCell = { id: "square:3:3", x: 3, y: 3 };
        const { handlers, setSelectedCells, getSelectedCells } = createSubject();
        getSelectedCells.mockReturnValue([firstCell, secondCell, thirdCell]);

        handlers.onPointerDown({ button: 2, pointerId: 5 } as PointerEvent, firstCell);
        handlers.onPointerMove({ buttons: 2, pointerId: 5 } as PointerEvent, secondCell);

        expect(setSelectedCells).toHaveBeenNthCalledWith(1, [secondCell, thirdCell]);
        expect(setSelectedCells).toHaveBeenNthCalledWith(2, [thirdCell]);
    });

    it("clears the selection on empty-space right click", () => {
        const { handlers, setSelectedCells, openInspectorDrawer, renderControlPanel } = createSubject();

        handlers.onContextMenu(null);

        expect(setSelectedCells).toHaveBeenCalledWith([]);
        expect(openInspectorDrawer).not.toHaveBeenCalled();
        expect(renderControlPanel).toHaveBeenCalledTimes(1);
    });

    it("reverts an in-progress right-drag selection on pointer cancel", () => {
        const firstCell: PaintableCell = { id: "square:1:1", x: 1, y: 1 };
        const secondCell: PaintableCell = { id: "square:2:1", x: 2, y: 1 };
        const thirdCell: PaintableCell = { id: "square:3:1", x: 3, y: 1 };
        const { handlers, setSelectedCells, getSelectedCells } = createSubject();
        getSelectedCells.mockReturnValue([firstCell, secondCell, thirdCell]);

        handlers.onPointerDown({ button: 2, pointerId: 12 } as PointerEvent, firstCell);
        handlers.onPointerMove({ buttons: 2, pointerId: 12 } as PointerEvent, secondCell);
        handlers.onPointerCancel({ pointerId: 12 } as PointerEvent);

        expect(setSelectedCells).toHaveBeenNthCalledWith(1, [secondCell, thirdCell]);
        expect(setSelectedCells).toHaveBeenNthCalledWith(2, [thirdCell]);
        expect(setSelectedCells).toHaveBeenNthCalledWith(3, [firstCell, secondCell, thirdCell]);
    });
});
