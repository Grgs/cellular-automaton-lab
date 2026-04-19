import { describe, expect, it, vi } from "vitest";

import { createLegacyDragGestureSession } from "./gesture-sessions/legacy-drag-session.js";

describe("interactions/legacy-drag-session", () => {
    it("updates only while the expected button remains pressed for the active pointer", () => {
        const legacyDrag = {
            isActive: vi.fn(() => true),
            begin: vi.fn(),
            update: vi.fn(),
            end: vi.fn().mockResolvedValue(null),
            cancel: vi.fn().mockResolvedValue(null),
        };
        const session = createLegacyDragGestureSession({
            pointerId: 4,
            legacyDrag,
            buttonMask: 1,
        });

        session.handleMove({ buttons: 1, pointerId: 4 } as PointerEvent, { id: "cell:a" });
        session.handleMove({ buttons: 1, pointerId: 7 } as PointerEvent, { id: "cell:c" });
        session.handleMove({ buttons: 0 } as PointerEvent, { id: "cell:b" });

        expect(legacyDrag.update).toHaveBeenCalledTimes(1);
        expect(legacyDrag.update).toHaveBeenCalledWith({ id: "cell:a" });
    });

    it("ends the drag only for the active pointer", () => {
        const legacyDrag = {
            isActive: vi.fn(() => true),
            begin: vi.fn(),
            update: vi.fn(),
            end: vi.fn().mockResolvedValue(null),
            cancel: vi.fn().mockResolvedValue(null),
        };
        const session = createLegacyDragGestureSession({
            pointerId: 4,
            legacyDrag,
            buttonMask: 1,
        });

        expect(session.handleUp({ pointerId: 7 } as PointerEvent)).toBe(false);
        expect(session.handleUp({ pointerId: 4 } as PointerEvent)).toBe(true);

        expect(legacyDrag.end).toHaveBeenCalledTimes(1);
    });

    it("runs the cancel hook before cancelling the drag for the active pointer", () => {
        const legacyDrag = {
            isActive: vi.fn(() => true),
            begin: vi.fn(),
            update: vi.fn(),
            end: vi.fn().mockResolvedValue(null),
            cancel: vi.fn().mockResolvedValue(null),
        };
        const onCancel = vi.fn();
        const session = createLegacyDragGestureSession({
            pointerId: 4,
            legacyDrag,
            buttonMask: 1,
            onCancel,
        });

        expect(session.cancel({ pointerId: 8 } as PointerEvent)).toBe(false);
        expect(session.cancel({ pointerId: 4 } as PointerEvent)).toBe(true);

        expect(onCancel).toHaveBeenCalledTimes(1);
        expect(legacyDrag.cancel).toHaveBeenCalledTimes(1);
    });
});
