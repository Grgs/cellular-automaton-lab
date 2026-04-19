import { matchesGesturePointer } from "./helpers.js";
import type { PointerGestureSession, EditorPointerSessionOptions } from "./types.js";

export function createEditorPointerSession({
    pointerId,
    editorSession,
}: EditorPointerSessionOptions): PointerGestureSession {
    return {
        kind: "editor-pointer",
        handleMove(event, cell) {
            if (!matchesGesturePointer(pointerId, event) || (event.buttons & 1) === 0) {
                return;
            }
            editorSession.handlePointerMove(cell);
        },
        handleUp(event) {
            if (!matchesGesturePointer(pointerId, event)) {
                return false;
            }
            void editorSession.handlePointerUp();
            return true;
        },
        cancel(event) {
            if (!matchesGesturePointer(pointerId, event)) {
                return false;
            }
            void editorSession.cancelActivePreview();
            return true;
        },
    };
}
