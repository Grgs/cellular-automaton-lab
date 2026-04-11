import { describe, expect, it, vi } from "vitest";

import { createLegacyDragGestureSession } from "./gesture-sessions/legacy-drag-session.js";

describe("interactions/legacy-drag-session", () => {
    it("updates only while the expected button remains pressed", () => {
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

        session.handleMove({ buttons: 1 } as PointerEvent, { id: "cell:a" });
        session.handleMove({ buttons: 0 } as PointerEvent, { id: "cell:b" });

        expect(legacyDrag.update).toHaveBeenCalledTimes(1);
        expect(legacyDrag.update).toHaveBeenCalledWith({ id: "cell:a" });
    });

    it("ends the drag on pointer up", () => {
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

        session.handleUp({} as PointerEvent);

        expect(legacyDrag.end).toHaveBeenCalledTimes(1);
    });

    it("runs the cancel hook before cancelling the drag", () => {
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

        session.cancel({} as PointerEvent);

        expect(onCancel).toHaveBeenCalledTimes(1);
        expect(legacyDrag.cancel).toHaveBeenCalledTimes(1);
    });
});
