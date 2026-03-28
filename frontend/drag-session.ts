import type {
    CoordinateCell,
    DragPaintCommit,
    DragPaintResult,
    DragPaintSession,
    PaintableCell,
    PreviewPaintCell,
} from "./types/editor.js";

export function cellKey(x: number, y: number): string {
    return `${x}:${y}`;
}

function identifyCell(cell: PaintableCell): string {
    if (cell?.id) {
        return cell.id;
    }
    return cellKey(cell.x ?? 0, cell.y ?? 0);
}

function interpolatedCells(fromCell: PaintableCell, toCell: PaintableCell): PaintableCell[] {
    const canInterpolate = Number.isFinite(fromCell?.x)
        && Number.isFinite(fromCell?.y)
        && Number.isFinite(toCell?.x)
        && Number.isFinite(toCell?.y)
        && (!fromCell?.kind || fromCell.kind === "cell")
        && (!toCell?.kind || toCell.kind === "cell");

    if (!canInterpolate) {
        return [toCell];
    }

    return interpolateCellPath(
        fromCell.x ?? 0,
        fromCell.y ?? 0,
        toCell.x ?? 0,
        toCell.y ?? 0,
    ).map((cell) => ({
        ...toCell,
        ...cell,
        ...(toCell?.id ? { id: `c:${cell.x}:${cell.y}` } : {}),
    }));
}

export function interpolateCellPath(fromX: number, fromY: number, toX: number, toY: number): CoordinateCell[] {
    const steps = Math.max(Math.abs(toX - fromX), Math.abs(toY - fromY));
    if (steps === 0) {
        return [{ x: toX, y: toY }];
    }

    const cells: CoordinateCell[] = [];
    for (let step = 0; step <= steps; step += 1) {
        cells.push({
            x: Math.round(fromX + ((toX - fromX) * step) / steps),
            y: Math.round(fromY + ((toY - fromY) * step) / steps),
        });
    }
    return cells;
}

export function createDragPaintSession(): DragPaintSession {
    let activeDrag: {
        origin: PaintableCell;
        last: PaintableCell;
        painted: Map<string, PreviewPaintCell>;
        moved: boolean;
        paintState: number;
        pointerId: number | null;
    } | null = null;

    function getPreviewCells(): PreviewPaintCell[] {
        return activeDrag ? Array.from(activeDrag.painted.values()) : [];
    }

    function paintCell(cell: PaintableCell): boolean {
        const key = identifyCell(cell);
        if (!activeDrag || activeDrag.painted.has(key)) {
            return false;
        }

        activeDrag.painted.set(key, { ...cell, state: activeDrag.paintState });
        return true;
    }

    function start(cell: PaintableCell, paintState = 1, pointerId: number | null = null): void {
        activeDrag = {
            origin: { ...cell },
            last: { ...cell },
            painted: new Map(),
            moved: false,
            paintState,
            pointerId,
        };
    }

    function update(cell: PaintableCell): DragPaintResult {
        if (!activeDrag) {
            return {
                changed: false,
                previewCells: [],
            };
        }

        const isOrigin = identifyCell(activeDrag.origin) === identifyCell(cell);
        if (!activeDrag.moved && !isOrigin) {
            activeDrag.moved = true;
            paintCell(activeDrag.origin);
        }

        let changed = false;
        if (activeDrag.moved) {
            interpolatedCells(activeDrag.last, cell).forEach((paintableCell) => {
                changed = paintCell(paintableCell) || changed;
            });
        }

        activeDrag.last = { ...cell };
        return {
            changed,
            previewCells: getPreviewCells(),
        };
    }

    function end(): DragPaintCommit | null {
        if (!activeDrag) {
            return null;
        }

        const dragState = activeDrag;
        activeDrag = null;
        return {
            moved: dragState.moved,
            pointerId: dragState.pointerId,
            paintedCells: Array.from(dragState.painted.values()),
        };
    }

    return {
        start,
        update,
        end,
        getPreviewCells,
    };
}
