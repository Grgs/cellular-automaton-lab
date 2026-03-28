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
import type { CellStateDefinition, TopologyPayload } from "./types/domain.js";
import type { PaintableCell, PreviewPaintCell } from "./types/editor.js";
import type {
    CanvasColors,
    CanvasGridView,
    CanvasRenderPayload,
    CanvasRenderStyle,
    GeometryAdapter,
    GeometryCache,
    GridMetrics,
    PolygonGeometryCell,
    RenderableTopologyCell,
} from "./types/rendering.js";

interface CanvasMetrics extends GridMetrics {
    pixelWidth: number;
    pixelHeight: number;
    dpr: number;
}

interface CreateCanvasGridViewOptions {
    canvas: HTMLCanvasElement;
    getDevicePixelRatio?: () => number;
    getComputedStyleFn?: (node: Element) => CSSStyleDeclaration;
}

type RuntimeCanvasGridView = CanvasGridView & {
    supportsTopology: true;
    getMetrics(): CanvasMetrics;
};

function previewKey(cell: PreviewPaintCell | null | undefined): string | null {
    return cell?.id || null;
}

function canvasBorderRadius(gap: number): string {
    return gap === 0 ? "0px" : "18px";
}

function extractRenderState(input: unknown): CanvasRenderPayload {
    const payload = (input && typeof input === "object") ? input as Partial<CanvasRenderPayload> : {};
    return {
        topology: payload.topology ?? null,
        cellStates: Array.isArray(payload.cellStates) ? payload.cellStates : [],
        previewCellStatesById: payload.previewCellStatesById && typeof payload.previewCellStatesById === "object"
            ? payload.previewCellStatesById
            : null,
    };
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
}: CreateCanvasGridViewOptions): RuntimeCanvasGridView {
    const contextCandidate = canvas.getContext("2d");
    const committedCanvas = document.createElement("canvas");
    const committedContextCandidate = committedCanvas.getContext("2d");
    if (!contextCandidate || !committedContextCandidate) {
        throw new Error("Canvas 2D rendering context is unavailable.");
    }
    const context = contextCandidate;
    const committedContext = committedContextCandidate;
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
    let metrics: CanvasMetrics = {
        ...gridMetrics(0, 0, cellSize, geometry),
        pixelWidth: canvas.width,
        pixelHeight: canvas.height,
        dpr: 1,
    };

    function restoreCommittedSurface(): void {
        context.setTransform(1, 0, 0, 1, 0, 0);
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.drawImage(committedCanvas, 0, 0);
        context.setTransform(metrics.dpr, 0, 0, metrics.dpr, 0, 0);
    }

    function resolvePreviewTopologyCell(cell: PreviewPaintCell): RenderableTopologyCell | null {
        return geometryCache?.cellsById?.get(cell.id)?.cell
            || (topology?.cells?.find((candidate) => candidate.id === cell.id) as RenderableTopologyCell | undefined)
            || null;
    }

    function drawCommittedCells(targetContext: CanvasRenderingContext2D, adapter: GeometryAdapter): void {
        if (!topology?.cells) {
            return;
        }
        topology.cells.forEach((cell, index) => {
            adapter.drawCell({
                context: targetContext,
                cell: cell as RenderableTopologyCell,
                stateValue: cellStates[index] ?? 0,
                metrics,
                cache: geometryCache,
                colors: canvasColors,
                colorLookup,
                resolveRenderedCellColor,
                renderStyle: currentRenderStyle,
                renderLayer: "committed",
            });
        });
    }

    function drawCommittedGrid(): void {
        const adapter = getGeometryAdapter(geometry);
        committedContext.setTransform(metrics.dpr, 0, 0, metrics.dpr, 0, 0);
        committedContext.clearRect(0, 0, Math.max(metrics.cssWidth, 1), Math.max(metrics.cssHeight, 1));

        canvasColors = readCanvasColors(canvas, getComputedStyleFn);
        colorLookup = buildStateColorLookup(stateDefinitions, canvasColors);
        currentRenderStyle = resolveCanvasRenderStyle(cellSize, geometry, canvasColors);
        committedContext.fillStyle = currentRenderStyle.lineColor;
        committedContext.fillRect(0, 0, metrics.cssWidth, metrics.cssHeight);

        drawCommittedCells(committedContext, adapter);
        if (typeof adapter.drawOverlay === "function") {
            adapter.drawOverlay({
                context: committedContext,
                width: metrics.width,
                height: metrics.height,
                metrics,
                cache: geometryCache,
                renderStyle: currentRenderStyle,
                cellSize,
            });
        }
    }

    function drawPreviewOverlay(): void {
        if (previewCells.size === 0) {
            return;
        }

        const adapter = getGeometryAdapter(geometry);
        previewCells.forEach((cell) => {
            if (adapter.family === "mixed") {
                const topologyCell = resolvePreviewTopologyCell(cell);
                if (!topologyCell) {
                    return;
                }
                adapter.drawCell({
                    context,
                    cell: topologyCell,
                    stateValue: cell.state,
                    metrics,
                    cache: geometryCache,
                    colors: canvasColors,
                    colorLookup,
                    resolveRenderedCellColor,
                    renderStyle: currentRenderStyle,
                    renderLayer: "preview",
                });
                return;
            }

            if (typeof cell?.id !== "string" || cell.id.length === 0) {
                return;
            }
            adapter.drawCell({
                context,
                cell,
                stateValue: cell.state,
                metrics,
                cache: geometryCache,
                colors: canvasColors,
                colorLookup,
                resolveRenderedCellColor,
                renderStyle: currentRenderStyle,
                renderLayer: "preview",
            });
        });
    }

    function drawGrid(): void {
        const adapter = getGeometryAdapter(geometry);
        const width = topologyWidth(topology);
        const height = topologyHeight(topology);
        const nextMetrics = adapter.buildMetrics({ width, height, cellSize, topology });
        const dpr = Math.max(1, getDevicePixelRatio());
        const pixelWidth = Math.max(1, Math.round(nextMetrics.cssWidth * dpr));
        const pixelHeight = Math.max(1, Math.round(nextMetrics.cssHeight * dpr));

        canvas.style.width = `${nextMetrics.cssWidth}px`;
        canvas.style.height = `${nextMetrics.cssHeight}px`;
        canvas.style.borderRadius = canvasBorderRadius(nextMetrics.gap);
        canvas.dataset.renderCellSize = String(cellSize);
        if (canvas.width !== pixelWidth) {
            canvas.width = pixelWidth;
        }
        if (canvas.height !== pixelHeight) {
            canvas.height = pixelHeight;
        }
        if (committedCanvas.width !== pixelWidth) {
            committedCanvas.width = pixelWidth;
        }
        if (committedCanvas.height !== pixelHeight) {
            committedCanvas.height = pixelHeight;
        }

        metrics = {
            ...nextMetrics,
            width,
            height,
            pixelWidth: canvas.width,
            pixelHeight: canvas.height,
            dpr,
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
        restoreCommittedSurface();
        drawPreviewOverlay();
    }

    function render(
        nextGridOrState: unknown,
        nextCellSize = cellSize,
        nextStateDefinitions = stateDefinitions,
        nextGeometry = geometry,
    ): void {
        const nextState = extractRenderState(nextGridOrState);
        topology = nextState.topology;
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
        restoreCommittedSurface();
        drawPreviewOverlay();
    }

    function clearPreview(): void {
        if (previewCells.size === 0) {
            return;
        }
        previewCells = new Map();
        restoreCommittedSurface();
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

    function getMetrics(): CanvasMetrics {
        return { ...metrics };
    }

    return {
        supportsTopology: true,
        render,
        setPreviewCells,
        clearPreview,
        getCellFromPointerEvent,
        getMetrics,
    };
}
