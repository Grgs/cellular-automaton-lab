import type { GridInteractionBindings } from "../types/editor.js";

export function bindGridInteractions({
    surfaceElement,
    resolveCellFromEvent,
    onPointerDown,
    onPointerMove,
    onPointerUp,
    onPointerCancel,
    onClick,
}: GridInteractionBindings): void {
    if (!surfaceElement) {
        return;
    }

    surfaceElement.addEventListener("pointerdown", (event) => {
        if (event.button !== 0) {
            return;
        }

        const cell = resolveCellFromEvent(event);
        if (!cell) {
            return;
        }

        onPointerDown(event, cell);
    });

    surfaceElement.addEventListener("pointermove", (event) => {
        const cell = resolveCellFromEvent(event);
        if (!cell) {
            return;
        }
        onPointerMove(event, cell);
    });

    surfaceElement.addEventListener("pointerup", (event) => {
        onPointerUp(event);
    });

    surfaceElement.addEventListener("pointercancel", (event) => {
        onPointerCancel(event);
    });

    surfaceElement.addEventListener("click", (event) => {
        const cell = resolveCellFromEvent(event);
        if (!cell) {
            return;
        }

        onClick(event, cell);
    });
}
