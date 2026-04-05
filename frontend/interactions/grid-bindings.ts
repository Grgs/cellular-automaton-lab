import type { GridInteractionBindings } from "../types/editor.js";

export function bindGridInteractions({
    surfaceElement,
    resolveCellFromEvent,
    onPointerDown,
    onPointerMove,
    onPointerUp,
    onPointerCancel,
    onClick,
    onHoverChange,
}: GridInteractionBindings): void {
    if (!surfaceElement) {
        return;
    }

    function shouldTrackHover(event: PointerEvent): boolean {
        const pointerType = event.pointerType || "mouse";
        return pointerType !== "touch";
    }

    surfaceElement.addEventListener("pointerdown", (event) => {
        onHoverChange(null);
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
        if (shouldTrackHover(event) && event.buttons === 0) {
            onHoverChange(cell);
        }
        if (!cell) {
            return;
        }
        onPointerMove(event, cell);
    });

    surfaceElement.addEventListener("pointerup", (event) => {
        onPointerUp(event);
    });

    surfaceElement.addEventListener("pointercancel", (event) => {
        onHoverChange(null);
        onPointerCancel(event);
    });

    surfaceElement.addEventListener("pointerleave", () => {
        onHoverChange(null);
    });

    surfaceElement.addEventListener("click", (event) => {
        const cell = resolveCellFromEvent(event);
        if (!cell) {
            return;
        }

        onClick(event, cell);
    });
}
