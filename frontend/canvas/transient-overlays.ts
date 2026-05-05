import { DRAG_GESTURE_FLASH_DURATION_MS } from "../interactions/constants.js";
import type { TopologyPayload } from "../types/domain.js";
import type { GestureOutlineTone, PaintableCell, PreviewPaintCell } from "../types/editor.js";

export interface TransientOverlaySnapshot {
    previewCells: Map<string, PreviewPaintCell>;
    hoveredCell: PaintableCell | null;
    selectedCells: PaintableCell[];
    gestureOutlineCells: PaintableCell[];
    gestureOutlineTone: GestureOutlineTone | null;
}

interface TransientOverlayControllerOptions {
    onChange: () => void;
    setTimeoutFn: (callback: () => void, delay: number) => number;
    clearTimeoutFn: (timerId: number) => void;
}

export function paintableCellKey(cell: PaintableCell | null | undefined): string | null {
    if (!cell) {
        return null;
    }
    if (typeof cell.id === "string" && cell.id.length > 0) {
        return cell.id;
    }
    if (typeof cell.x === "number" && typeof cell.y === "number") {
        return `${cell.x}:${cell.y}`;
    }
    return null;
}

function previewKey(cell: PreviewPaintCell | null | undefined): string | null {
    return cell?.id || null;
}

function clonePaintableCell(cell: PaintableCell): PaintableCell {
    return { ...cell };
}

function clonePreviewCell(cell: PreviewPaintCell): PreviewPaintCell {
    return { ...cell };
}

function normalizePaintableCells(cells: PaintableCell[]): Map<string, PaintableCell> {
    return new Map(
        cells
            .map((cell) => [paintableCellKey(cell), clonePaintableCell(cell)])
            .filter(
                (entry): entry is [string, PaintableCell] =>
                    typeof entry[0] === "string" && entry[0].length > 0,
            ),
    );
}

function normalizePreviewCells(cells: PreviewPaintCell[]): Map<string, PreviewPaintCell> {
    return new Map(
        cells
            .map((cell) => [previewKey(cell), clonePreviewCell(cell)])
            .filter(
                (entry): entry is [string, PreviewPaintCell] =>
                    typeof entry[0] === "string" && entry[0].length > 0,
            ),
    );
}

function sameCellKeys<T>(left: Map<string, T>, right: Map<string, T>): boolean {
    return left.size === right.size && Array.from(right.keys()).every((key) => left.has(key));
}

function topologyCellIds(topology: TopologyPayload | null): Set<string> | null {
    if (!Array.isArray(topology?.cells)) {
        return null;
    }
    return new Set(topology.cells.map((cell) => cell.id));
}

export function createTransientOverlayController({
    onChange,
    setTimeoutFn,
    clearTimeoutFn,
}: TransientOverlayControllerOptions) {
    let previewCells = new Map<string, PreviewPaintCell>();
    let hoveredCell: PaintableCell | null = null;
    let selectedCells = new Map<string, PaintableCell>();
    let gestureOutlineCells = new Map<string, PaintableCell>();
    let gestureOutlineTone: GestureOutlineTone | null = null;
    let gestureOutlineTimerId: number | null = null;
    let lastTopologyRevision: string | null = null;

    function clearGestureOutlineTimer(): void {
        if (gestureOutlineTimerId === null) {
            return;
        }
        clearTimeoutFn(gestureOutlineTimerId);
        gestureOutlineTimerId = null;
    }

    function clearGestureOutlineState(): void {
        clearGestureOutlineTimer();
        gestureOutlineCells = new Map();
        gestureOutlineTone = null;
    }

    function clearGestureOutline(): void {
        if (
            gestureOutlineCells.size === 0 &&
            gestureOutlineTone === null &&
            gestureOutlineTimerId === null
        ) {
            return;
        }
        clearGestureOutlineState();
        onChange();
    }

    function shouldClearGestureOutlineForTopology(nextIds: Set<string> | null): boolean {
        if (gestureOutlineCells.size === 0) {
            return false;
        }
        if (!nextIds) {
            return true;
        }
        return Array.from(gestureOutlineCells.keys()).some((cellId) => !nextIds.has(cellId));
    }

    function reconcileForRender(nextTopology: TopologyPayload | null): void {
        const nextTopologyRevision = nextTopology?.topology_revision ?? null;
        const topologyRevisionChanged =
            lastTopologyRevision !== null && nextTopologyRevision !== lastTopologyRevision;
        const nextIds = topologyCellIds(nextTopology);

        if (topologyRevisionChanged) {
            selectedCells = new Map();
            clearGestureOutlineState();
        } else {
            if (selectedCells.size > 0) {
                if (!nextIds) {
                    selectedCells = new Map();
                } else {
                    selectedCells = new Map(
                        Array.from(selectedCells.entries()).filter(([cellId]) =>
                            nextIds.has(cellId),
                        ),
                    );
                }
            }
            if (shouldClearGestureOutlineForTopology(nextIds)) {
                clearGestureOutlineState();
            }
        }

        lastTopologyRevision = nextTopologyRevision;
    }

    function setPreviewCells(cells: PreviewPaintCell[]): void {
        previewCells = normalizePreviewCells(cells);
        onChange();
    }

    function clearPreview(): void {
        if (previewCells.size === 0) {
            return;
        }
        previewCells = new Map();
        onChange();
    }

    function setHoveredCell(cell: PaintableCell | null): void {
        if (paintableCellKey(hoveredCell) === paintableCellKey(cell)) {
            return;
        }
        hoveredCell = cell ? clonePaintableCell(cell) : null;
        onChange();
    }

    function setSelectedCells(cells: PaintableCell[]): void {
        const nextSelectedCells = normalizePaintableCells(cells);
        if (sameCellKeys(selectedCells, nextSelectedCells)) {
            return;
        }
        selectedCells = nextSelectedCells;
        onChange();
    }

    function getSelectedCells(): PaintableCell[] {
        return Array.from(selectedCells.values()).map(clonePaintableCell);
    }

    function setGestureOutline(cells: PaintableCell[], tone: GestureOutlineTone): void {
        clearGestureOutlineTimer();
        const nextCells = normalizePaintableCells(cells);
        const sameTone = gestureOutlineTone === tone;
        if (sameTone && sameCellKeys(gestureOutlineCells, nextCells)) {
            return;
        }
        gestureOutlineCells = nextCells;
        gestureOutlineTone = nextCells.size > 0 ? tone : null;
        onChange();
    }

    function flashGestureOutline(
        cells: PaintableCell[],
        tone: GestureOutlineTone,
        durationMs = DRAG_GESTURE_FLASH_DURATION_MS,
    ): void {
        const nextCells = normalizePaintableCells(cells);
        clearGestureOutlineTimer();
        gestureOutlineCells = nextCells;
        gestureOutlineTone = nextCells.size > 0 ? tone : null;
        onChange();
        if (nextCells.size === 0) {
            return;
        }
        gestureOutlineTimerId = setTimeoutFn(() => {
            gestureOutlineTimerId = null;
            if (gestureOutlineCells.size === 0) {
                return;
            }
            gestureOutlineCells = new Map();
            gestureOutlineTone = null;
            onChange();
        }, durationMs);
    }

    function snapshot(): TransientOverlaySnapshot {
        const hoveredKey = paintableCellKey(hoveredCell);
        return {
            previewCells: new Map(previewCells),
            hoveredCell:
                hoveredKey && selectedCells.has(hoveredKey)
                    ? null
                    : hoveredCell
                      ? clonePaintableCell(hoveredCell)
                      : null,
            selectedCells: Array.from(selectedCells.values()).map(clonePaintableCell),
            gestureOutlineCells: Array.from(gestureOutlineCells.values()).map(clonePaintableCell),
            gestureOutlineTone,
        };
    }

    return {
        reconcileForRender,
        setPreviewCells,
        clearPreview,
        setHoveredCell,
        setSelectedCells,
        getSelectedCells,
        setGestureOutline,
        flashGestureOutline,
        clearGestureOutline,
        snapshot,
    };
}
