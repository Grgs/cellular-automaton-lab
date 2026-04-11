import type { PointerGestureSession, EditorPointerSessionOptions } from "./types.js";

export function createEditorPointerSession({
    pointerId,
    editorSession,
}: EditorPointerSessionOptions): PointerGestureSession {
    return {
        pointerId,
        handleMove(event, cell) {
            if ((event.buttons & 1) === 0) {
                return;
            }
            editorSession.handlePointerMove(cell);
        },
        handleUp() {
            void editorSession.handlePointerUp();
        },
        cancel() {
            void editorSession.cancelActivePreview();
        },
        isActive: () => editorSession.isPointerActive(),
    };
}
