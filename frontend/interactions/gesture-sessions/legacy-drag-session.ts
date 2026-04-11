import type { PointerGestureSession, LegacyDragGestureSessionOptions } from "./types.js";

export function createLegacyDragGestureSession({
    pointerId,
    legacyDrag,
    buttonMask,
    onCancel = () => {},
}: LegacyDragGestureSessionOptions): PointerGestureSession {
    return {
        pointerId,
        handleMove(event, cell) {
            if ((event.buttons & buttonMask) === 0) {
                return;
            }
            legacyDrag.update(cell);
        },
        handleUp() {
            void legacyDrag.end();
        },
        cancel() {
            onCancel();
            void legacyDrag.cancel();
        },
        isActive: () => legacyDrag.isActive(),
    };
}
