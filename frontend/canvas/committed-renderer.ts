import { DEFAULT_GEOMETRY, gridMetrics, normalizeGeometry } from "../layout.js";
import { resolveCellFromCanvasOffset as resolveGeometryCellFromOffset } from "../geometry-adapters.js";
import { getGeometryAdapter } from "../geometry/registry.js";
import { indexTopology } from "../topology-index.js";
import { topologyHeight, topologyWidth } from "../topology.js";
import { resolveGeometryCache } from "./cache.js";
import { drawCommittedCells, drawCommittedLayer } from "./render-layers.js";
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
import type {
    CellStateDefinition,
    TopologyCell,
    TopologyIndex,
    TopologyPayload,
} from "../types/domain.js";
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
    topologyIndex: TopologyIndex;
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

interface RenderDiagnosticsContext {
    topology: TopologyPayload | null;
    geometryCache: GeometryCache | null;
    geometry: string;
    adapterFamily: "regular" | "mixed" | "aperiodic";
    metrics: CanvasSurfaceMetrics;
    cellSize: number;
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
    let topologyIndex = indexTopology(null);
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
    let renderDiagnosticsContext: RenderDiagnosticsContext | null = null;
    let renderDiagnosticsSampled = false;
    let previousCommittedKey = "";
    let previousCellStates: number[] = [];
    let metrics: CanvasSurfaceMetrics = {
        ...gridMetrics(0, 0, cellSize, geometry),
        pixelWidth: canvas.width,
        pixelHeight: canvas.height,
        dpr: 1,
    };

    function syncCanvasViewportAlignment(): void {
        // `.grid-viewport` is a CSS grid with `place-items: center`. Applying
        // renderer-computed margins as well double-counts the inset for
        // presentation-only (especially aperiodic) boards.
        canvas.style.margin = "0";
    }

    function prepareCommittedStyle(): void {
        canvasColors = readCanvasColors(canvas, getComputedStyleFn);
        colorLookup = buildStateColorLookup(stateDefinitions, canvasColors);
        currentRenderStyle = resolveCanvasRenderStyle(cellSize, geometry, canvasColors);
    }

    function committedLayerInputs() {
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
        ): string =>
            resolveRenderedCellColor(stateValue, nextColorLookup, colors, {
                ...options,
                tileColorsEnabled,
            });
        return {
            targetContext: surface.committedContext,
            geometry,
            topology,
            topologyIndex,
            metrics,
            geometryCache,
            canvasColors,
            renderStyle: currentRenderStyle,
            colorLookup,
            resolveRenderedCellColor: resolveCellColor,
            cellStates,
            cellSize,
        };
    }

    function drawCommittedGrid(): void {
        drawCommittedLayer({
            ...committedLayerInputs(),
        });
    }

    function render(
        nextState: CanvasRenderPayload,
        nextCellSize = cellSize,
        nextStateDefinitions = stateDefinitions,
        nextGeometry = geometry,
    ): void {
        topology = nextState.topology;
        topologyIndex = indexTopology(topology);
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
        syncCanvasViewportAlignment();
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
        renderDiagnostics = null;
        resolvedRenderDiagnostics = null;
        renderDiagnosticsSampled = false;
        renderDiagnosticsContext = {
            topology,
            geometryCache,
            geometry,
            adapterFamily: adapter.family,
            metrics,
            cellSize,
        };

        prepareCommittedStyle();
        const committedKey = JSON.stringify({
            revision: topology?.topology_revision ?? "",
            geometry,
            cellSize,
            pixelWidth: metrics.pixelWidth,
            pixelHeight: metrics.pixelHeight,
            dpr: metrics.dpr,
            canvasColors,
            currentRenderStyle,
            stateDefinitions,
            tileColorsEnabled,
        });
        const changedCellIndexes: number[] = [];
        if (
            adapter.family === "regular" &&
            committedKey === previousCommittedKey &&
            previousCellStates.length === cellStates.length
        ) {
            for (let index = 0; index < cellStates.length; index += 1) {
                if (cellStates[index] !== previousCellStates[index]) {
                    changedCellIndexes.push(index);
                }
            }
        }
        const incrementalLimit = Math.floor(cellStates.length * 0.25);
        if (
            changedCellIndexes.length > 0 &&
            changedCellIndexes.length <= incrementalLimit &&
            committedKey === previousCommittedKey
        ) {
            drawCommittedCells({
                ...committedLayerInputs(),
                cellIndexes: changedCellIndexes,
            });
        } else if (changedCellIndexes.length > 0 || committedKey !== previousCommittedKey) {
            drawCommittedGrid();
        }
        previousCommittedKey = committedKey;
        previousCellStates = cellStates.slice();
    }

    function restoreCommittedSurface(): void {
        surface.restoreCommittedSurface(metrics);
    }

    function snapshot(): CanvasCommittedRenderSnapshot {
        return {
            context: surface.context,
            geometry,
            topology,
            topologyIndex,
            metrics,
            geometryCache,
            canvasColors,
            renderStyle: currentRenderStyle,
            colorLookup,
            cellStates,
            resolveRenderedCellColor: (stateValue, nextColorLookup, colors, options = {}) =>
                resolveRenderedCellColor(stateValue, nextColorLookup, colors, {
                    ...options,
                    tileColorsEnabled,
                }),
        };
    }

    function getCellFromPointerEvent(event: MouseEvent | PointerEvent): PaintableCell | null {
        const rect = canvas.getBoundingClientRect();
        const scaleX = rect.width > 0 ? metrics.cssWidth / rect.width : 1;
        const scaleY = rect.height > 0 ? metrics.cssHeight / rect.height : 1;
        return resolveGeometryCellFromOffset(
            (event.clientX - rect.left) * scaleX,
            (event.clientY - rect.top) * scaleY,
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
        if (!renderDiagnosticsSampled && renderDiagnosticsContext !== null) {
            renderDiagnostics = sampleRenderDiagnostics(
                renderDiagnosticsContext.topology,
                renderDiagnosticsContext.geometryCache,
                {
                    geometry: renderDiagnosticsContext.geometry,
                    adapterFamily: renderDiagnosticsContext.adapterFamily,
                    metrics: renderDiagnosticsContext.metrics,
                    cellSize: renderDiagnosticsContext.cellSize,
                },
            );
            renderDiagnosticsSampled = true;
        }
        if (renderDiagnostics === null) {
            return null;
        }
        if (resolvedRenderDiagnostics === null) {
            resolvedRenderDiagnostics = resolveRenderDiagnosticsSnapshot(
                renderDiagnostics,
                renderDiagnosticsContext?.geometryCache ?? geometryCache,
            );
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
