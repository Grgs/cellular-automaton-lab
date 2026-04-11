import { describe, expect, it, vi } from "vitest";

import { createEditorPointerSession } from "./gesture-sessions/editor-pointer-session.js";

describe("interactions/editor-pointer-session", () => {
    it("delegates pointer moves while the left button is still pressed", () => {
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

        session.handleMove({ buttons: 1 } as PointerEvent, { id: "cell:a" });
        session.handleMove({ buttons: 0 } as PointerEvent, { id: "cell:b" });

        expect(editorSession.handlePointerMove).toHaveBeenCalledTimes(1);
        expect(editorSession.handlePointerMove).toHaveBeenCalledWith({ id: "cell:a" });
    });

    it("delegates pointer up and cancel to the editor session", () => {
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

        session.handleUp({} as PointerEvent);
        session.cancel({} as PointerEvent);

        expect(editorSession.handlePointerUp).toHaveBeenCalledTimes(1);
        expect(editorSession.cancelActivePreview).toHaveBeenCalledTimes(1);
    });
});
