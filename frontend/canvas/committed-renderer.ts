import { DEFAULT_GEOMETRY, gridMetrics, normalizeGeometry } from "../layout.js";
import { resolveCellFromCanvasOffset as resolveGeometryCellFromOffset } from "../geometry-adapters.js";
import { getGeometryAdapter } from "../geometry/registry.js";
import {
    topologyHeight,
    topologyWidth,
} from "../topology.js";
import { topologyUsesBackendViewportSync } from "../topology-catalog.js";
import { resolveGeometryCache } from "./cache.js";
import { drawCommittedLayer } from "./render-layers.js";
import {
    buildStateColorLookup,
    DEFAULT_COLORS,
    readCanvasColors,
    resolveCanvasRenderStyle,
    resolveRenderedCellColor,
} from "./render-style.js";
import {
    resolveRenderDiagnosticsSnapshot,
    resolveRenderedCellCenter,
    sampleRenderDiagnostics,
} from "./render-diagnostics.js";
import { createCanvasSurface, type CanvasSurfaceMetrics } from "./surface.js";
import type { CellStateDefinition, TopologyCell, TopologyPayload } from "../types/domain.js";
import type { PaintableCell } from "../types/editor.js";
import type {
    CanvasColors,
    CanvasRenderPayload,
    CanvasRenderStyle,
    GeometryCache,
    RenderDiagnosticsSnapshot,
} from "../types/rendering.js";

interface CreateCanvasCommittedRendererOptions {
    canvas: HTMLCanvasElement;
    getDevicePixelRatio?: () => number;
    getComputedStyleFn?: (node: Element) => CSSStyleDeclaration;
}

export interface CanvasCommittedRenderSnapshot {
    context: CanvasRenderingContext2D;
    geometry: string;
    topology: TopologyPayload | null;
    metrics: CanvasSurfaceMetrics;
    geometryCache: GeometryCache | null;
    canvasColors: CanvasColors;
    renderStyle: CanvasRenderStyle;
    colorLookup: Map<number, string>;
    cellStates: number[];
    resolveRenderedCellColor: (
        stateValue: number,
        colorLookup: Map<number, string>,
        colors: CanvasColors,
        options?: {
            geometry?: string;
            x?: number | null;
            y?: number | null;
            cell?: TopologyCell | PaintableCell | null;
            tileColorsEnabled?: boolean;
        },
    ) => string;
}

export interface CanvasCommittedRenderer {
    render(
        nextState: CanvasRenderPayload,
        nextCellSize?: number,
        nextStateDefinitions?: CellStateDefinition[],
        nextGeometry?: string,
    ): void;
    restoreCommittedSurface(): void;
    snapshot(): CanvasCommittedRenderSnapshot;
    getCellFromPointerEvent(event: MouseEvent | PointerEvent): PaintableCell | null;
    getMetrics(): CanvasSurfaceMetrics;
    getRenderDiagnostics(): RenderDiagnosticsSnapshot | null;
    getRenderedCellCenter(cellId: string): { x: number; y: number } | null;
}

function canvasBorderRadius(gap: number): string {
    return gap === 0 ? "0px" : "18px";
}

export function createCanvasCommittedRenderer({
    canvas,
    getDevicePixelRatio = () => window.devicePixelRatio || 1,
    getComputedStyleFn = (node) => window.getComputedStyle(node),
}: CreateCanvasCommittedRendererOptions): CanvasCommittedRenderer {
    const surface = createCanvasSurface(canvas);
    let topology: TopologyPayload | null = null;
    let cellStates: number[] = [];
    let cellSize = 12;
    let geometry = DEFAULT_GEOMETRY;
    let stateDefinitions: CellStateDefinition[] = [];
    let geometryCacheKey = "";
    let geometryCache: GeometryCache | null = null;
    let canvasColors: CanvasColors = { ...DEFAULT_COLORS };
    let colorLookup = buildStateColorLookup([], canvasColors);
    let currentRenderStyle = resolveCanvasRenderStyle(cellSize, geometry, canvasColors);
    let tileColorsEnabled = true;
    let renderDiagnostics: RenderDiagnosticsSnapshot | null = null;
    let resolvedRenderDiagnostics: RenderDiagnosticsSnapshot | null = null;
    let metrics: CanvasSurfaceMetrics = {
        ...gridMetrics(0, 0, cellSize, geometry),
        pixelWidth: canvas.width,
        pixelHeight: canvas.height,
        dpr: 1,
    };

    function syncCanvasViewportAlignment(nextMetrics: CanvasSurfaceMetrics): void {
        const viewport = canvas.parentElement;
        if (!(viewport instanceof HTMLElement)) {
            return;
        }
        if (topologyUsesBackendViewportSync(topology?.topology_spec)) {
            canvas.style.margin = "0";
            return;
        }

        const horizontalInset = Math.max(0, (viewport.clientWidth - nextMetrics.cssWidth) / 2);
        const verticalInset = Math.max(0, (viewport.clientHeight - nextMetrics.cssHeight) / 2);
        canvas.style.margin = `${verticalInset}px ${horizontalInset}px`;
    }

    function drawCommittedGrid(): void {
        canvasColors = readCanvasColors(canvas, getComputedStyleFn);
        colorLookup = buildStateColorLookup(stateDefinitions, canvasColors);
        currentRenderStyle = resolveCanvasRenderStyle(cellSize, geometry, canvasColors);
        const resolveCellColor = (
            stateValue: number,
            nextColorLookup: Map<number, string>,
            colors: CanvasColors,
            options: {
                geometry?: string;
                x?: number | null;
                y?: number | null;
                cell?: TopologyCell | PaintableCell | null;
                tileColorsEnabled?: boolean;
            } = {},
        ): string => resolveRenderedCellColor(stateValue, nextColorLookup, colors, {
            ...options,
            tileColorsEnabled,
        });
        drawCommittedLayer({
            targetContext: surface.committedContext,
            geometry,
            topology,
            metrics,
            geometryCache,
            canvasColors,
            renderStyle: currentRenderStyle,
            colorLookup,
            resolveRenderedCellColor: resolveCellColor,
            cellStates,
            cellSize,
        });
    }

    function render(
        nextState: CanvasRenderPayload,
        nextCellSize = cellSize,
        nextStateDefinitions = stateDefinitions,
        nextGeometry = geometry,
    ): void {
        topology = nextState.topology;
        cellStates = nextState.cellStates;
        tileColorsEnabled = nextState.tileColorsEnabled !== false;
        cellSize = nextCellSize;
        stateDefinitions = nextStateDefinitions || [];
        geometry = normalizeGeometry(nextGeometry);

        const adapter = getGeometryAdapter(geometry);
        const width = topologyWidth(topology);
        const height = topologyHeight(topology);
        const nextMetrics = adapter.buildMetrics({ width, height, cellSize, topology });
        const dpr = Math.max(1, getDevicePixelRatio());
        canvas.dataset.renderCellSize = String(cellSize);
        metrics = surface.resize(nextMetrics, dpr, canvasBorderRadius(nextMetrics.gap));
        syncCanvasViewportAlignment(metrics);
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
        renderDiagnostics = sampleRenderDiagnostics(
            topology,
            geometryCache,
            {
                geometry,
                adapterFamily: adapter.family,
                metrics,
                cellSize,
            },
        );
        resolvedRenderDiagnostics = null;

        drawCommittedGrid();
    }

    function restoreCommittedSurface(): void {
        surface.restoreCommittedSurface(metrics);
    }

    function snapshot(): CanvasCommittedRenderSnapshot {
        return {
            context: surface.context,
            geometry,
            topology,
            metrics,
            geometryCache,
            canvasColors,
            renderStyle: currentRenderStyle,
            colorLookup,
            cellStates,
            resolveRenderedCellColor: (
                stateValue,
                nextColorLookup,
                colors,
                options = {},
            ) => resolveRenderedCellColor(stateValue, nextColorLookup, colors, {
                ...options,
                tileColorsEnabled,
            }),
        };
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

    function getRenderDiagnostics(): RenderDiagnosticsSnapshot | null {
        if (renderDiagnostics === null) {
            return null;
        }
        if (resolvedRenderDiagnostics === null) {
            resolvedRenderDiagnostics = resolveRenderDiagnosticsSnapshot(renderDiagnostics, geometryCache);
        }
        return resolvedRenderDiagnostics ? structuredClone(resolvedRenderDiagnostics) : null;
    }

    function getRenderedCellCenter(cellId: string): { x: number; y: number } | null {
        return resolveRenderedCellCenter(geometryCache, cellId);
    }

    return {
        render,
        restoreCommittedSurface,
        snapshot,
        getCellFromPointerEvent,
        getMetrics,
        getRenderDiagnostics,
        getRenderedCellCenter,
    };
}
