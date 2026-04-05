import { beforeEach, describe, expect, it, vi } from "vitest";

import { createInteractionSurfaceBindings } from "./surface-bindings.js";
import type { GridInteractionBindings, PaintableCell } from "../types/editor.js";

function createEventStub() {
    return {
        preventDefault: vi.fn(),
        stopPropagation: vi.fn(),
    } as unknown as PointerEvent & MouseEvent;
}

function createSubject(): {
    handlers: GridInteractionBindings;
    setHoveredCell: ReturnType<typeof vi.fn>;
    editorPointerActive: ReturnType<typeof vi.fn>;
    legacyPointerActive: ReturnType<typeof vi.fn>;
} {
    let handlers: GridInteractionBindings | null = null;
    const setHoveredCell = vi.fn();
    const editorPointerActive = vi.fn(() => false);
    const legacyPointerActive = vi.fn(() => false);

    const bindings = createInteractionSurfaceBindings({
        surfaceElement: document.createElement("canvas"),
        resolveCellFromEvent: () => ({ id: "square:1:1", x: 1, y: 1 }),
        editPolicy: {
            runningBrushEditingEnabled: () => false,
            dismissEditingUi: () => Promise.resolve(false),
            runningAdvancedToolBlocked: () => false,
            blockRunningAdvancedTool: vi.fn(),
            supportsEditorTools: () => false,
            editingBlockedByRun: () => false,
            isEditArmed: () => true,
            armEditingFromGrid: () => ({ consumeNextClick: false }),
            currentTool: () => "brush",
        },
        editorSession: {
            isPointerActive: editorPointerActive,
            beginPointerSession: vi.fn().mockResolvedValue(true),
            handlePointerMove: vi.fn(),
            handlePointerUp: vi.fn().mockResolvedValue(null),
            cancelActivePreview: vi.fn().mockResolvedValue(undefined),
            isClickSuppressed: vi.fn(() => false),
            handleClick: vi.fn().mockResolvedValue({ handled: true }),
        },
        legacyDrag: {
            isActive: legacyPointerActive,
            begin: vi.fn(),
            update: vi.fn(),
            end: vi.fn().mockResolvedValue(null),
        },
        setHoveredCell,
        paintCell: vi.fn().mockResolvedValue(undefined),
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
        editorPointerActive,
        legacyPointerActive,
    };
}

describe("interactions/surface-bindings", () => {
    beforeEach(() => {
        document.body.innerHTML = "";
    });

    it("clears hover on pointer down before interaction handling", () => {
        const { handlers, setHoveredCell } = createSubject();

        handlers.onPointerDown(createEventStub(), { id: "square:1:1", x: 1, y: 1 });

        expect(setHoveredCell).toHaveBeenCalledWith(null);
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
});
