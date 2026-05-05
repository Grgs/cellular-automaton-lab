import type { PaintableCell } from "../../types/editor.js";

export function identifyGestureCell(cell: PaintableCell): string {
    if (typeof cell.id === "string" && cell.id.length > 0) {
        return cell.id;
    }
    return `${cell.x ?? 0}:${cell.y ?? 0}`;
}

export function cloneSelectedCells(cells: PaintableCell[]): Map<string, PaintableCell> {
    return new Map(
        cells
            .map((cell) => [identifyGestureCell(cell), { ...cell }])
            .filter(
                (entry): entry is [string, PaintableCell] =>
                    typeof entry[0] === "string" && entry[0].length > 0,
            ),
    );
}

export function matchesGesturePointer(pointerId: number | null, event: PointerEvent): boolean {
    return pointerId === null || event.pointerId === pointerId;
}

export function setSurfacePointerCapture(
    surfaceElement: HTMLElement | null,
    pointerId: number | null,
): void {
    if (
        !surfaceElement ||
        typeof surfaceElement.setPointerCapture !== "function" ||
        pointerId === null
    ) {
        return;
    }
    try {
        surfaceElement.setPointerCapture(pointerId);
    } catch {
        // Ignore unsupported pointer capture implementations.
    }
}

export function releaseSurfacePointerCapture(
    surfaceElement: HTMLElement | null,
    pointerId: number | null,
): void {
    if (
        !surfaceElement ||
        typeof surfaceElement.releasePointerCapture !== "function" ||
        pointerId === null
    ) {
        return;
    }
    try {
        surfaceElement.releasePointerCapture(pointerId);
    } catch {
        // Pointer capture may already be released.
    }
}
