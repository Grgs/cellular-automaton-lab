import { matchesGesturePointer } from "./helpers.js";
import type { PointerGestureSession, LegacyDragGestureSessionOptions } from "./types.js";

export function createLegacyDragGestureSession({
    pointerId,
    legacyDrag,
    buttonMask,
    onCancel = () => {},
}: LegacyDragGestureSessionOptions): PointerGestureSession {
    return {
        kind: "legacy-drag",
        handleMove(event, cell) {
            if (!matchesGesturePointer(pointerId, event) || (event.buttons & buttonMask) === 0) {
                return;
            }
            legacyDrag.update(cell);
        },
        handleUp(event) {
            if (!matchesGesturePointer(pointerId, event)) {
                return false;
            }
            void legacyDrag.end();
            return true;
        },
        cancel(event) {
            if (!matchesGesturePointer(pointerId, event)) {
                return false;
            }
            onCancel();
            void legacyDrag.cancel();
            return true;
        },
    };
}
