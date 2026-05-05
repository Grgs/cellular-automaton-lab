import {
    brushRadiusForSize,
    EDITOR_TOOL_FILL,
    EDITOR_TOOL_LINE,
    EDITOR_TOOL_RECTANGLE,
} from "./editor-tools.js";
import { findTopologyCellById } from "./topology.js";
import {
    cellCenter,
    geometryCacheForState,
    previewCellFromTopologyCell,
    renderCellSize,
    resolveSampledCell,
    resolveTopologyCell,
} from "./editor-operation-resolvers.js";
import type {
    IndexedTopologyPaintableCell,
    PaintableCell,
    PreviewPaintCell,
} from "./types/editor.js";
import type { AppState } from "./types/state.js";

function expandBrushStamp(
    state: AppState,
    originCell: PaintableCell,
    brushSize: number,
    paintState: number,
): PreviewPaintCell[] {
    const start = resolveTopologyCell(state, originCell);
    if (!start) {
        return [];
    }

    const maxDepth = brushRadiusForSize(brushSize);
    const queue: Array<{ cell: IndexedTopologyPaintableCell; depth: number }> = [
        { cell: start, depth: 0 },
    ];
    const visited = new Map<string, PreviewPaintCell>([
        [start.id, previewCellFromTopologyCell(start, paintState)],
    ]);

    while (queue.length > 0) {
        const current = queue.shift();
        if (!current || current.depth >= maxDepth) {
            continue;
        }

        (current.cell.neighbors || []).forEach((neighborId) => {
            if (!neighborId || visited.has(neighborId)) {
                return;
            }
            const neighbor = findTopologyCellById(state.topologyIndex, neighborId);
            if (!neighbor) {
                return;
            }
            visited.set(neighbor.id, previewCellFromTopologyCell(neighbor, paintState));
            queue.push({ cell: neighbor, depth: current.depth + 1 });
        });
    }

    return Array.from(visited.values());
}

export function mergePreviewCells(
    targetMap: Map<string, PreviewPaintCell>,
    cells: PreviewPaintCell[],
): Map<string, PreviewPaintCell> {
    cells.forEach((cell) => {
        targetMap.set(cell.id, cell);
    });
    return targetMap;
}

export function buildBrushCells(
    state: AppState,
    originCell: PaintableCell,
    paintState: number,
    brushSize: number,
): PreviewPaintCell[] {
    return expandBrushStamp(state, originCell, brushSize, paintState);
}

export function buildLineCells(
    state: AppState,
    startCell: PaintableCell,
    endCell: PaintableCell,
    paintState: number,
    brushSize: number,
): PreviewPaintCell[] {
    const start = resolveTopologyCell(state, startCell);
    const end = resolveTopologyCell(state, endCell);
    if (!start || !end) {
        return [];
    }

    const startCenter = cellCenter(state, start);
    const endCenter = cellCenter(state, end);
    const distance = Math.hypot(endCenter.x - startCenter.x, endCenter.y - startCenter.y);
    const stepLength = Math.max(1, renderCellSize(state) / 3);
    const steps = Math.max(1, Math.ceil(distance / stepLength));
    const geometryCache = geometryCacheForState(state);
    const stamped = new Map<string, PreviewPaintCell>();

    for (let step = 0; step <= steps; step += 1) {
        const progress = steps === 0 ? 1 : step / steps;
        const offsetX = startCenter.x + (endCenter.x - startCenter.x) * progress;
        const offsetY = startCenter.y + (endCenter.y - startCenter.y) * progress;
        const resolved = resolveSampledCell(state, offsetX, offsetY, geometryCache);
        if (!resolved) {
            continue;
        }
        mergePreviewCells(stamped, expandBrushStamp(state, resolved, brushSize, paintState));
    }

    return Array.from(stamped.values());
}

export function buildRectangleCells(
    state: AppState,
    startCell: PaintableCell,
    endCell: PaintableCell,
    paintState: number,
    brushSize: number,
): PreviewPaintCell[] {
    const start = resolveTopologyCell(state, startCell);
    const end = resolveTopologyCell(state, endCell);
    if (!start || !end || !state.topology?.cells) {
        return [];
    }

    const startCenter = cellCenter(state, start);
    const endCenter = cellCenter(state, end);
    const left = Math.min(startCenter.x, endCenter.x);
    const right = Math.max(startCenter.x, endCenter.x);
    const top = Math.min(startCenter.y, endCenter.y);
    const bottom = Math.max(startCenter.y, endCenter.y);
    const borderBand = Math.max(1, renderCellSize(state) / 2);
    const outlineAnchors = new Map<string, IndexedTopologyPaintableCell>();

    state.topology.cells.forEach((cell) => {
        const resolvedCell = findTopologyCellById(state.topologyIndex, cell.id);
        if (!resolvedCell) {
            return;
        }
        const center = cellCenter(state, resolvedCell);
        const insideHorizontal = center.x >= left - borderBand && center.x <= right + borderBand;
        const insideVertical = center.y >= top - borderBand && center.y <= bottom + borderBand;
        if (!insideHorizontal || !insideVertical) {
            return;
        }

        const nearVerticalBorder =
            Math.abs(center.x - left) <= borderBand || Math.abs(center.x - right) <= borderBand;
        const nearHorizontalBorder =
            Math.abs(center.y - top) <= borderBand || Math.abs(center.y - bottom) <= borderBand;
        if (!nearVerticalBorder && !nearHorizontalBorder) {
            return;
        }

        outlineAnchors.set(resolvedCell.id, resolvedCell);
    });

    const stamped = new Map<string, PreviewPaintCell>();
    outlineAnchors.forEach((cell) => {
        mergePreviewCells(stamped, expandBrushStamp(state, cell, brushSize, paintState));
    });
    return Array.from(stamped.values());
}

export function buildFillCells(
    state: AppState,
    originCell: PaintableCell,
    paintState: number,
): PreviewPaintCell[] {
    const start = resolveTopologyCell(state, originCell);
    if (!start) {
        return [];
    }

    const startState = Number(state.cellStates?.[start.index] ?? 0);
    if (startState === paintState) {
        return [];
    }

    const queue: IndexedTopologyPaintableCell[] = [start];
    const visited = new Set([start.id]);
    const filled = new Map<string, PreviewPaintCell>();

    while (queue.length > 0) {
        const current = queue.shift();
        if (!current) {
            continue;
        }

        const currentState = Number(state.cellStates?.[current.index] ?? 0);
        if (currentState !== startState) {
            continue;
        }

        filled.set(current.id, previewCellFromTopologyCell(current, paintState));
        (current.neighbors || []).forEach((neighborId) => {
            if (!neighborId || visited.has(neighborId)) {
                return;
            }
            visited.add(neighborId);
            const neighbor = findTopologyCellById(state.topologyIndex, neighborId);
            if (neighbor) {
                queue.push(neighbor);
            }
        });
    }

    return Array.from(filled.values());
}

export function buildEditorToolCells(
    state: AppState,
    tool: string,
    startCell: PaintableCell,
    endCell: PaintableCell | null | undefined,
    paintState: number,
    brushSize: number,
): PreviewPaintCell[] {
    if (tool === EDITOR_TOOL_FILL) {
        return buildFillCells(state, startCell, paintState);
    }
    if (tool === EDITOR_TOOL_LINE) {
        return buildLineCells(state, startCell, endCell ?? startCell, paintState, brushSize);
    }
    if (tool === EDITOR_TOOL_RECTANGLE) {
        return buildRectangleCells(state, startCell, endCell ?? startCell, paintState, brushSize);
    }
    return buildBrushCells(state, startCell, paintState, brushSize);
}
