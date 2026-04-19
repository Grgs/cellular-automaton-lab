import { describe, expect, it, vi } from "vitest";

import { createEditorPointerSession } from "./gesture-sessions/editor-pointer-session.js";

describe("interactions/editor-pointer-session", () => {
    it("delegates pointer moves only for the active pointer while the left button is still pressed", () => {
        const editorSession = {
            isPointerActive: vi.fn(() => true),
            beginPointerSession: vi.fn().mockResolvedValue(true),
            handlePointerMove: vi.fn(),
            handlePointerUp: vi.fn().mockResolvedValue(null),
            cancelActivePreview: vi.fn().mockResolvedValue(undefined),
            isClickSuppressed: vi.fn(() => false),
            handleClick: vi.fn().mockResolvedValue({ handled: true }),
        };
        const session = createEditorPointerSession({
            pointerId: 3,
            editorSession,
        });

        session.handleMove({ buttons: 1, pointerId: 3 } as PointerEvent, { id: "cell:a" });
        session.handleMove({ buttons: 1, pointerId: 9 } as PointerEvent, { id: "cell:c" });
        session.handleMove({ buttons: 0 } as PointerEvent, { id: "cell:b" });

        expect(editorSession.handlePointerMove).toHaveBeenCalledTimes(1);
        expect(editorSession.handlePointerMove).toHaveBeenCalledWith({ id: "cell:a" });
    });

    it("delegates pointer up and cancel only for the active pointer", () => {
        const editorSession = {
            isPointerActive: vi.fn(() => true),
            beginPointerSession: vi.fn().mockResolvedValue(true),
            handlePointerMove: vi.fn(),
            handlePointerUp: vi.fn().mockResolvedValue(null),
            cancelActivePreview: vi.fn().mockResolvedValue(undefined),
            isClickSuppressed: vi.fn(() => false),
            handleClick: vi.fn().mockResolvedValue({ handled: true }),
        };
        const session = createEditorPointerSession({
            pointerId: 3,
            editorSession,
        });

        expect(session.handleUp({ pointerId: 7 } as PointerEvent)).toBe(false);
        expect(session.cancel({ pointerId: 7 } as PointerEvent)).toBe(false);
        expect(session.handleUp({ pointerId: 3 } as PointerEvent)).toBe(true);
        expect(session.cancel({ pointerId: 3 } as PointerEvent)).toBe(true);

        expect(editorSession.handlePointerUp).toHaveBeenCalledTimes(1);
        expect(editorSession.cancelActivePreview).toHaveBeenCalledTimes(1);
    });
});
