import { matchesGesturePointer } from "./helpers.js";
import type { PointerGestureSession, PaintDragGestureSessionOptions } from "./types.js";

export function createPaintDragGestureSession({
    pointerId,
    paintDrag,
    buttonMask,
    onCancel = () => {},
}: PaintDragGestureSessionOptions): PointerGestureSession {
    return {
        kind: "paint-drag",
        handleMove(event, cell) {
            if (!matchesGesturePointer(pointerId, event) || (event.buttons & buttonMask) === 0) {
                return;
            }
            paintDrag.update(cell);
        },
        handleUp(event) {
            if (!matchesGesturePointer(pointerId, event)) {
                return false;
            }
            void paintDrag.end();
            return true;
        },
        cancel(event) {
            if (!matchesGesturePointer(pointerId, event)) {
                return false;
            }
            onCancel();
            void paintDrag.cancel();
            return true;
        },
    };
}
