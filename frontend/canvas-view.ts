import { DEFAULT_GEOMETRY, gridMetrics, normalizeGeometry } from "./layout.js";
import {
    cellCenterOffset as resolveCellCenterOffset,
    resolveCellFromCanvasOffset as resolveGeometryCellFromOffset,
    topologyCellCenter as resolveTopologyCellCenter,
} from "./geometry-adapters.js";
import { getGeometryAdapter } from "./geometry/registry.js";
import {
    topologyCellStatesById,
    topologyHeight,
    topologyWidth,
} from "./topology.js";
import { resolveGeometryCache } from "./canvas/cache.js";
import { drawCommittedLayer, drawGestureOutlineLayer, drawHoverLayer, drawPreviewLayer, drawSelectionLayer } from "./canvas/render-layers.js";
import {
    buildStateColorLookup,
    DEFAULT_COLORS,
    readCanvasColors,
    resolveCanvasRenderStyle,
    resolveDeadCellColor,
    resolveRenderedCellColor,
    resolveRenderDetailLevel,
    resolveRenderStyle,
    resolveStateColor,
} from "./canvas/render-style.js";
import { DRAG_GESTURE_FLASH_DURATION_MS } from "./interactions/constants.js";
import { createCanvasSurface, type CanvasSurfaceMetrics } from "./canvas/surface.js";
import type { CellStateDefinition, TopologyPayload } from "./types/domain.js";
import type { GestureOutlineTone, PaintableCell, PreviewPaintCell } from "./types/editor.js";
import type {
    CanvasColors,
    CanvasGridView,
    CanvasRenderPayload,
    GeometryCache,
    GridMetrics,
} from "./types/rendering.js";

interface CreateCanvasGridViewOptions {
    canvas: HTMLCanvasElement;
    getDevicePixelRatio?: () => number;
    getComputedStyleFn?: (node: Element) => CSSStyleDeclaration;
    setTimeoutFn?: (callback: () => void, delay: number) => number;
    clearTimeoutFn?: (timerId: number) => void;
}

type RuntimeCanvasGridView = CanvasGridView & {
    supportsTopology: true;
    getMetrics(): CanvasSurfaceMetrics;
};

function previewKey(cell: PreviewPaintCell | null | undefined): string | null {
    return cell?.id || null;
}

function paintableCellKey(cell: PaintableCell | null | undefined): string | null {
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

function canvasBorderRadius(gap: number): string {
    return gap === 0 ? "0px" : "18px";
}

export {
    buildStateColorLookup,
    resolveDeadCellColor,
    resolveRenderDetailLevel,
    resolveRenderStyle,
    resolveStateColor,
};

export function canvasPixelDimensions(
    width: number,
    height: number,
    cellSize: number,
    geometry = DEFAULT_GEOMETRY,
    topology: TopologyPayload | null = null,
): GridMetrics & { width: number; height: number; pitch: number } {
    const metrics = gridMetrics(width, height, cellSize, geometry, topology);
    return {
        ...metrics,
        width: metrics.cssWidth,
        height: metrics.cssHeight,
        pitch: Number(metrics.pitch ?? metrics.horizontalPitch ?? 0),
    };
}

export function cellFromCanvasOffset(
    offsetX: number,
    offsetY: number,
    width: number,
    height: number,
    cellSize: number,
    geometry = DEFAULT_GEOMETRY,
): PaintableCell | null {
    return resolveGeometryCellFromOffset(offsetX, offsetY, width, height, cellSize, geometry);
}

export function cellCenterOffset(
    x: number,
    y: number,
    cellSize: number,
    geometry = DEFAULT_GEOMETRY,
): { x: number; y: number } {
    return resolveCellCenterOffset(x, y, cellSize, geometry);
}

export function topologyCellCenter(
    cell: PaintableCell,
    cellSize: number,
    geometry = DEFAULT_GEOMETRY,
    width = 0,
    height = 0,
    metrics: GridMetrics | null = null,
    geometryCache: GeometryCache | null = null,
    topology: TopologyPayload | null = null,
): { x: number; y: number } {
    return resolveTopologyCellCenter(cell, cellSize, geometry, width, height, metrics, geometryCache, topology);
}

export function createCanvasGridView({
    canvas,
    getDevicePixelRatio = () => window.devicePixelRatio || 1,
    getComputedStyleFn = (node) => window.getComputedStyle(node),
    setTimeoutFn = (callback: () => void, delay: number) => window.setTimeout(callback, delay),
    clearTimeoutFn = (timerId: number) => window.clearTimeout(timerId),
}: CreateCanvasGridViewOptions): RuntimeCanvasGridView {
    const surface = createCanvasSurface(canvas);
    let topology: TopologyPayload | null = null;
    let cellStates: number[] = [];
    let previewCellStatesById: Record<string, number> | null = null;
    let cellSize = 12;
    let geometry = DEFAULT_GEOMETRY;
    let previewCells = new Map<string, PreviewPaintCell>();
    let stateDefinitions: CellStateDefinition[] = [];
    let geometryCacheKey = "";
    let geometryCache: GeometryCache | null = null;
    let canvasColors: CanvasColors = { ...DEFAULT_COLORS };
    let colorLookup = buildStateColorLookup([], canvasColors);
    let currentRenderStyle = resolveCanvasRenderStyle(cellSize, geometry, canvasColors);
    let hoveredCell: PaintableCell | null = null;
    let selectedCell: PaintableCell | null = null;
    let gestureOutlineCells = new Map<string, PaintableCell>();
    let gestureOutlineTone: GestureOutlineTone | null = null;
    let gestureOutlineTimerId: number | null = null;
    let lastTopologyRevision: string | null = null;
    let metrics: CanvasSurfaceMetrics = {
        ...gridMetrics(0, 0, cellSize, geometry),
        pixelWidth: canvas.width,
        pixelHeight: canvas.height,
        dpr: 1,
    };

    function drawCommittedGrid(): void {
        canvasColors = readCanvasColors(canvas, getComputedStyleFn);
        colorLookup = buildStateColorLookup(stateDefinitions, canvasColors);
        currentRenderStyle = resolveCanvasRenderStyle(cellSize, geometry, canvasColors);
        drawCommittedLayer({
            targetContext: surface.committedContext,
            geometry,
            topology,
            metrics,
            geometryCache,
            canvasColors,
            renderStyle: currentRenderStyle,
            colorLookup,
            resolveRenderedCellColor,
            cellStates,
            cellSize,
        });
    }

    function drawPreviewOverlay(): void {
        drawPreviewLayer({
            context: surface.context,
            geometry,
            topology,
            metrics,
            geometryCache,
            canvasColors,
            renderStyle: currentRenderStyle,
            colorLookup,
            resolveRenderedCellColor,
            previewCells,
        });
    }

    function drawHoverOverlay(): void {
        if (!hoveredCell || paintableCellKey(hoveredCell) === paintableCellKey(selectedCell)) {
            return;
        }
        drawHoverLayer({
            context: surface.context,
            geometry,
            topology,
            metrics,
            geometryCache,
            canvasColors,
            renderStyle: currentRenderStyle,
            colorLookup,
            resolveRenderedCellColor,
            hoveredCell,
            cellStates,
        });
    }

    function drawSelectionOverlay(): void {
        if (!selectedCell) {
            return;
        }
        drawSelectionLayer({
            context: surface.context,
            geometry,
            topology,
            metrics,
            geometryCache,
            canvasColors,
            renderStyle: currentRenderStyle,
            colorLookup,
            resolveRenderedCellColor,
            selectedCell,
            cellStates,
        });
    }

    function drawGestureOutlineOverlay(): void {
        if (gestureOutlineTone === null || gestureOutlineCells.size === 0) {
            return;
        }
        drawGestureOutlineLayer({
            context: surface.context,
            geometry,
            topology,
            metrics,
            geometryCache,
            canvasColors,
            renderStyle: currentRenderStyle,
            colorLookup,
            resolveRenderedCellColor,
            outlinedCells: Array.from(gestureOutlineCells.values()),
            tone: gestureOutlineTone,
            cellStates,
        });
    }

    function redrawTransientLayers(): void {
        surface.restoreCommittedSurface(metrics);
        drawHoverOverlay();
        drawSelectionOverlay();
        drawPreviewOverlay();
        drawGestureOutlineOverlay();
    }

    function normalizeGestureOutlineCells(cells: PaintableCell[]): Map<string, PaintableCell> {
        return new Map(
            cells
                .map((cell) => [paintableCellKey(cell), { ...cell }])
                .filter((entry): entry is [string, PaintableCell] => typeof entry[0] === "string" && entry[0].length > 0),
        );
    }

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

    function shouldClearGestureOutlineForTopology(nextTopology: TopologyPayload | null): boolean {
        if (gestureOutlineCells.size === 0) {
            return false;
        }
        if (!Array.isArray(nextTopology?.cells)) {
            return true;
        }
        const nextIds = new Set(nextTopology.cells.map((cell) => cell.id));
        return Array.from(gestureOutlineCells.keys()).some((cellId) => !nextIds.has(cellId));
    }

    function drawGrid(): void {
        const adapter = getGeometryAdapter(geometry);
        const width = topologyWidth(topology);
        const height = topologyHeight(topology);
        const nextMetrics = adapter.buildMetrics({ width, height, cellSize, topology });
        const dpr = Math.max(1, getDevicePixelRatio());
        canvas.dataset.renderCellSize = String(cellSize);
        metrics = surface.resize(nextMetrics, dpr, canvasBorderRadius(nextMetrics.gap));
        metrics = {
            ...metrics,
            width,
            height,
            pitch: Number(nextMetrics.pitch ?? nextMetrics.horizontalPitch ?? 0),
        };
        const nextCache = resolveGeometryCache({
            existingKey: geometryCacheKey,
            existingCache: geometryCache,
            width,
            height,
            cellSize,
            geometry,
            metrics,
            topology,
        });
        geometryCacheKey = nextCache.cacheKey;
        geometryCache = nextCache.geometryCache;

        drawCommittedGrid();
        redrawTransientLayers();
    }

    function render(
        nextState: CanvasRenderPayload,
        nextCellSize = cellSize,
        nextStateDefinitions = stateDefinitions,
        nextGeometry = geometry,
    ): void {
        const nextTopology = nextState.topology;
        const nextTopologyRevision = nextTopology?.topology_revision ?? null;
        const topologyRevisionChanged = lastTopologyRevision !== null && nextTopologyRevision !== lastTopologyRevision;
        if (topologyRevisionChanged) {
            selectedCell = null;
            clearGestureOutlineState();
        }
        if (
            selectedCell
            && (!Array.isArray(nextTopology?.cells) || !nextTopology.cells.some((cell) => cell.id === selectedCell?.id))
        ) {
            selectedCell = null;
        }
        if (!topologyRevisionChanged && shouldClearGestureOutlineForTopology(nextTopology)) {
            clearGestureOutlineState();
        }
        topology = nextTopology;
        lastTopologyRevision = nextTopologyRevision;
        cellStates = nextState.cellStates;
        previewCellStatesById = nextState.previewCellStatesById;
        cellSize = nextCellSize;
        stateDefinitions = nextStateDefinitions || [];
        geometry = normalizeGeometry(nextGeometry);
        if (previewCellStatesById && topology?.cells) {
            const previewStates = topologyCellStatesById(topology, cellStates);
            previewCellStatesById = { ...previewStates, ...previewCellStatesById };
        }
        drawGrid();
    }

    function setPreviewCells(cells: PreviewPaintCell[]): void {
        previewCells = new Map(
            cells
                .map((cell) => [previewKey(cell), cell])
                .filter((entry): entry is [string, PreviewPaintCell] => typeof entry[0] === "string" && entry[0].length > 0),
        );
        redrawTransientLayers();
    }

    function clearPreview(): void {
        if (previewCells.size === 0) {
            return;
        }
        previewCells = new Map();
        redrawTransientLayers();
    }

    function setHoveredCell(cell: PaintableCell | null): void {
        if (paintableCellKey(hoveredCell) === paintableCellKey(cell)) {
            return;
        }
        hoveredCell = cell ? { ...cell } : null;
        redrawTransientLayers();
    }

    function setSelectedCell(cell: PaintableCell | null): void {
        if (paintableCellKey(selectedCell) === paintableCellKey(cell)) {
            return;
        }
        selectedCell = cell ? { ...cell } : null;
        redrawTransientLayers();
    }

    function getSelectedCell(): PaintableCell | null {
        return selectedCell ? { ...selectedCell } : null;
    }

    function setGestureOutline(cells: PaintableCell[], tone: GestureOutlineTone): void {
        clearGestureOutlineTimer();
        const nextCells = normalizeGestureOutlineCells(cells);
        const sameTone = gestureOutlineTone === tone;
        const sameCells = gestureOutlineCells.size === nextCells.size
            && Array.from(nextCells.keys()).every((key) => gestureOutlineCells.has(key));
        if (sameTone && sameCells) {
            return;
        }
        gestureOutlineCells = nextCells;
        gestureOutlineTone = nextCells.size > 0 ? tone : null;
        redrawTransientLayers();
    }

    function flashGestureOutline(
        cells: PaintableCell[],
        tone: GestureOutlineTone,
        durationMs = DRAG_GESTURE_FLASH_DURATION_MS,
    ): void {
        const nextCells = normalizeGestureOutlineCells(cells);
        clearGestureOutlineTimer();
        gestureOutlineCells = nextCells;
        gestureOutlineTone = nextCells.size > 0 ? tone : null;
        redrawTransientLayers();
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
            redrawTransientLayers();
        }, durationMs);
    }

    function clearGestureOutline(): void {
        if (gestureOutlineCells.size === 0 && gestureOutlineTone === null && gestureOutlineTimerId === null) {
            return;
        }
        clearGestureOutlineState();
        redrawTransientLayers();
    }

    function getCellFromPointerEvent(event: MouseEvent | PointerEvent): PaintableCell | null {
        const rect = canvas.getBoundingClientRect();
        return resolveGeometryCellFromOffset(
            event.clientX - rect.left,
            event.clientY - rect.top,
            metrics.width,
            metrics.height,
            cellSize,
            geometry,
            metrics,
            geometryCache,
        );
    }

    function getMetrics(): CanvasSurfaceMetrics {
        return { ...metrics };
    }

    return {
        supportsTopology: true,
        render,
        setPreviewCells,
        clearPreview,
        setHoveredCell,
        setSelectedCell,
        getSelectedCell,
        setGestureOutline,
        flashGestureOutline,
        clearGestureOutline,
        getCellFromPointerEvent,
        getMetrics,
    };
}
