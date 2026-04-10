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
import { createCanvasSurface, type CanvasSurfaceMetrics } from "./canvas/surface.js";
import { createTransientOverlayController, type TransientOverlaySnapshot } from "./canvas/transient-overlays.js";
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
    let stateDefinitions: CellStateDefinition[] = [];
    let geometryCacheKey = "";
    let geometryCache: GeometryCache | null = null;
    let canvasColors: CanvasColors = { ...DEFAULT_COLORS };
    let colorLookup = buildStateColorLookup([], canvasColors);
    let currentRenderStyle = resolveCanvasRenderStyle(cellSize, geometry, canvasColors);
    let metrics: CanvasSurfaceMetrics = {
        ...gridMetrics(0, 0, cellSize, geometry),
        pixelWidth: canvas.width,
        pixelHeight: canvas.height,
        dpr: 1,
    };
    const transientOverlays = createTransientOverlayController({
        onChange: redrawTransientLayers,
        setTimeoutFn,
        clearTimeoutFn,
    });

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

    function drawPreviewOverlay(snapshot: TransientOverlaySnapshot): void {
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
            previewCells: snapshot.previewCells,
        });
    }

    function drawHoverOverlay(snapshot: TransientOverlaySnapshot): void {
        if (!snapshot.hoveredCell) {
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
            hoveredCell: snapshot.hoveredCell,
            cellStates,
        });
    }

    function drawSelectionOverlay(snapshot: TransientOverlaySnapshot): void {
        if (snapshot.selectedCells.length === 0) {
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
            selectedCells: snapshot.selectedCells,
            cellStates,
        });
    }

    function drawGestureOutlineOverlay(snapshot: TransientOverlaySnapshot): void {
        if (snapshot.gestureOutlineTone === null || snapshot.gestureOutlineCells.length === 0) {
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
            outlinedCells: snapshot.gestureOutlineCells,
            tone: snapshot.gestureOutlineTone,
            cellStates,
        });
    }

    function redrawTransientLayers(): void {
        surface.restoreCommittedSurface(metrics);
        const overlaySnapshot = transientOverlays.snapshot();
        drawHoverOverlay(overlaySnapshot);
        drawSelectionOverlay(overlaySnapshot);
        drawPreviewOverlay(overlaySnapshot);
        drawGestureOutlineOverlay(overlaySnapshot);
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
        transientOverlays.reconcileForRender(nextTopology);
        topology = nextTopology;
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
        transientOverlays.setPreviewCells(cells);
    }

    function clearPreview(): void {
        transientOverlays.clearPreview();
    }

    function setHoveredCell(cell: PaintableCell | null): void {
        transientOverlays.setHoveredCell(cell);
    }

    function setSelectedCells(cells: PaintableCell[]): void {
        transientOverlays.setSelectedCells(cells);
    }

    function getSelectedCells(): PaintableCell[] {
        return transientOverlays.getSelectedCells();
    }

    function setGestureOutline(cells: PaintableCell[], tone: GestureOutlineTone): void {
        transientOverlays.setGestureOutline(cells, tone);
    }

    function flashGestureOutline(
        cells: PaintableCell[],
        tone: GestureOutlineTone,
        durationMs?: number,
    ): void {
        transientOverlays.flashGestureOutline(cells, tone, durationMs);
    }

    function clearGestureOutline(): void {
        transientOverlays.clearGestureOutline();
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
        setSelectedCells,
        getSelectedCells,
        setGestureOutline,
        flashGestureOutline,
        clearGestureOutline,
        getCellFromPointerEvent,
        getMetrics,
    };
}
