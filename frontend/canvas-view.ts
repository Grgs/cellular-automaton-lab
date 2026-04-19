import { DEFAULT_GEOMETRY, gridMetrics, normalizeGeometry } from "./layout.js";
import {
    cellCenterOffset as resolveCellCenterOffset,
    resolveCellFromCanvasOffset as resolveGeometryCellFromOffset,
    topologyCellCenter as resolveTopologyCellCenter,
} from "./geometry-adapters.js";
import { getGeometryAdapter } from "./geometry/registry.js";
import { summarizePositiveAreaPolygonOverlaps } from "./geometry/polygon-overlap.js";
import {
    topologyCellStatesById,
    topologyHeight,
    topologyWidth,
} from "./topology.js";
import { resolveGeometryCache } from "./canvas/cache.js";
import { drawCommittedLayer, drawGestureOutlineLayer, drawHoverLayer, drawPreviewLayer, drawSelectionLayer } from "./canvas/render-layers.js";
import { topologyUsesBackendViewportSync } from "./topology-catalog.js";
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
    GeometryBounds,
    GridMetrics,
    PolygonGeometryCache,
    RenderDiagnosticsSampleCell,
    RenderDiagnosticsSnapshot,
    RenderableTopologyCell,
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
    getRenderDiagnostics(): RenderDiagnosticsSnapshot | null;
    getRenderedCellCenter(cellId: string): { x: number; y: number } | null;
};

type SampleRole = "lexicographicFirst" | "centerNearest" | "boundaryFurthest";

function canvasBorderRadius(gap: number): string {
    return gap === 0 ? "0px" : "18px";
}

function isFinitePoint(
    value: { x?: number | null; y?: number | null } | null | undefined,
): value is { x: number; y: number } {
    return Number.isFinite(Number(value?.x)) && Number.isFinite(Number(value?.y));
}

function boundsFromVertices(vertices: Array<{ x: number; y: number }>): GeometryBounds | null {
    if (vertices.length === 0) {
        return null;
    }
    const xValues = vertices.map((vertex) => Number(vertex.x));
    const yValues = vertices.map((vertex) => Number(vertex.y));
    const minX = Math.min(...xValues);
    const maxX = Math.max(...xValues);
    const minY = Math.min(...yValues);
    const maxY = Math.max(...yValues);
    return {
        minX,
        maxX,
        minY,
        maxY,
        width: maxX - minX,
        height: maxY - minY,
    };
}

function boundsCenter(bounds: GeometryBounds): { x: number; y: number } {
    return {
        x: bounds.minX + (bounds.width / 2),
        y: bounds.minY + (bounds.height / 2),
    };
}

function rawGeometryForCell(cell: RenderableTopologyCell): {
    center: { x: number; y: number };
    bounds: GeometryBounds;
} | null {
    if (!Array.isArray(cell.vertices) || cell.vertices.length === 0) {
        return null;
    }
    const bounds = boundsFromVertices(cell.vertices);
    if (bounds === null) {
        return null;
    }
    return {
        center: isFinitePoint(cell.center)
            ? { x: Number(cell.center.x), y: Number(cell.center.y) }
            : boundsCenter(bounds),
        bounds,
    };
}

function renderedBoundsForCell(geometryCell: {
    minX: number;
    maxX: number;
    minY: number;
    maxY: number;
}): GeometryBounds {
    return {
        minX: geometryCell.minX,
        maxX: geometryCell.maxX,
        minY: geometryCell.minY,
        maxY: geometryCell.maxY,
        width: geometryCell.maxX - geometryCell.minX,
        height: geometryCell.maxY - geometryCell.minY,
    };
}

function centerDistanceSquared(
    center: { x: number; y: number },
    target: { x: number; y: number },
): number {
    const dx = center.x - target.x;
    const dy = center.y - target.y;
    return (dx * dx) + (dy * dy);
}

function aggregateBounds(
    boundsList: GeometryBounds[],
): GeometryBounds | null {
    if (boundsList.length === 0) {
        return null;
    }
    return boundsList.reduce((combined, bounds) => ({
        minX: Math.min(combined.minX, bounds.minX),
        maxX: Math.max(combined.maxX, bounds.maxX),
        minY: Math.min(combined.minY, bounds.minY),
        maxY: Math.max(combined.maxY, bounds.maxY),
        width: Math.max(combined.maxX, bounds.maxX) - Math.min(combined.minX, bounds.minX),
        height: Math.max(combined.maxY, bounds.maxY) - Math.min(combined.minY, bounds.minY),
    }));
}

function orientationTokenCounts(
    cells: RenderableTopologyCell[],
): Record<string, number> | null {
    const counts = new Map<string, number>();
    for (const cell of cells) {
        if (typeof cell.orientation_token !== "string" || cell.orientation_token.length === 0) {
            continue;
        }
        counts.set(cell.orientation_token, (counts.get(cell.orientation_token) ?? 0) + 1);
    }
    if (counts.size === 0) {
        return null;
    }
    return Object.fromEntries(
        Array.from(counts.entries()).sort((left, right) => left[0].localeCompare(right[0])),
    );
}

function angularSectorCounts(
    centers: Array<{ x: number; y: number }>,
    origin: { x: number; y: number },
    sectorCount: number = 12,
): number[] | null {
    if (centers.length === 0 || sectorCount <= 0) {
        return null;
    }
    const counts = Array.from({ length: sectorCount }, () => 0);
    const sectorAngle = (Math.PI * 2) / sectorCount;
    for (const center of centers) {
        const dx = center.x - origin.x;
        const dy = center.y - origin.y;
        const angle = Math.atan2(dy, dx);
        const normalizedAngle = angle >= 0 ? angle : angle + (Math.PI * 2);
        const index = Math.min(
            sectorCount - 1,
            Math.floor(normalizedAngle / sectorAngle),
        );
        counts[index] = (counts[index] ?? 0) + 1;
    }
    return counts;
}

function asPolygonGeometryCache(cache: GeometryCache | null): PolygonGeometryCache | null {
    if (!cache || !("cellsById" in cache)) {
        return null;
    }
    return cache;
}

function sampleRenderDiagnostics(
    topology: TopologyPayload | null,
    geometryCache: GeometryCache | null,
    {
        geometry,
        adapterFamily,
        metrics,
        cellSize,
    }: {
        geometry: string;
        adapterFamily: "regular" | "mixed" | "aperiodic";
        metrics: CanvasSurfaceMetrics;
        cellSize: number;
    },
): RenderDiagnosticsSnapshot | null {
    if (!topology?.cells?.length) {
        return null;
    }
    const polygonCache = asPolygonGeometryCache(geometryCache);
    if (polygonCache === null) {
        return null;
    }
    const topologyCells = topology.cells
        .map((cell) => {
            const typedCell = cell as RenderableTopologyCell;
            const rawGeometry = rawGeometryForCell(typedCell);
            const renderedGeometry = typedCell.id ? polygonCache.cellsById.get(typedCell.id) ?? null : null;
            if (rawGeometry === null || renderedGeometry === null) {
                return null;
            }
            return {
                cell: typedCell,
                rawCenter: rawGeometry.center,
                rawBounds: rawGeometry.bounds,
                renderedCenter: { x: renderedGeometry.centerX, y: renderedGeometry.centerY },
                renderedBounds: renderedBoundsForCell(renderedGeometry),
            };
        })
        .filter((entry): entry is NonNullable<typeof entry> => entry !== null)
        .sort((left, right) => left.cell.id.localeCompare(right.cell.id));
    if (topologyCells.length === 0) {
        return null;
    }
    const topologyBounds = boundsFromVertices(
        topologyCells.flatMap((entry) => entry.cell.vertices ?? []),
    );
    if (topologyBounds === null) {
        return null;
    }
    const topologyCenter = boundsCenter(topologyBounds);
    const renderedBounds = aggregateBounds(topologyCells.map((entry) => entry.renderedBounds));
    const renderedTopologyCenter = renderedBounds ? boundsCenter(renderedBounds) : null;
    const usedIds = new Set<string>();
    const roles: SampleRole[] = [
        "lexicographicFirst",
        "centerNearest",
        "boundaryFurthest",
    ];
    const sampleCells = {
        lexicographicFirst: null,
        centerNearest: null,
        boundaryFurthest: null,
    } as RenderDiagnosticsSnapshot["sampleCells"];

    const resolveRole = (role: SampleRole): typeof topologyCells[number] | null => {
        const candidates = topologyCells.filter((entry) => !usedIds.has(entry.cell.id));
        if (candidates.length === 0) {
            return null;
        }
        if (role === "lexicographicFirst") {
            return candidates[0] ?? null;
        }
        if (role === "centerNearest") {
            return [...candidates].sort((left, right) => {
                const distanceDelta = centerDistanceSquared(left.rawCenter, topologyCenter)
                    - centerDistanceSquared(right.rawCenter, topologyCenter);
                return distanceDelta !== 0
                    ? distanceDelta
                    : left.cell.id.localeCompare(right.cell.id);
            })[0] ?? null;
        }
        return [...candidates].sort((left, right) => {
            const distanceDelta = centerDistanceSquared(right.rawCenter, topologyCenter)
                - centerDistanceSquared(left.rawCenter, topologyCenter);
            return distanceDelta !== 0
                ? distanceDelta
                : left.cell.id.localeCompare(right.cell.id);
        })[0] ?? null;
    };

    for (const role of roles) {
        const selected = resolveRole(role);
        if (!selected) {
            continue;
        }
        usedIds.add(selected.cell.id);
        sampleCells[role] = {
            role,
            cellId: selected.cell.id,
            kind: typeof selected.cell.kind === "string" ? selected.cell.kind : null,
            rawCenter: selected.rawCenter,
            rawBounds: selected.rawBounds,
            renderedCenter: selected.renderedCenter,
            renderedBounds: selected.renderedBounds,
        } satisfies RenderDiagnosticsSampleCell;
    }

    return {
        geometry,
        adapterGeometry: geometry,
        adapterFamily,
        topologyBounds,
        renderMetrics: {
            cellSize,
            renderCellSize: cellSize,
            scale: typeof metrics.scale === "number" ? metrics.scale : null,
            coordinateScale: typeof metrics.coordinateScale === "number" ? metrics.coordinateScale : 1,
            xInset: metrics.xInset,
            yInset: metrics.yInset,
            cssWidth: metrics.cssWidth,
            cssHeight: metrics.cssHeight,
            canvasWidth: metrics.pixelWidth,
            canvasHeight: metrics.pixelHeight,
        },
        sampleCells,
        metricInputs: {
            renderedTopologyCenter,
            renderedCellCount: topologyCells.length,
            orientationTokenCounts: orientationTokenCounts(topologyCells.map((entry) => entry.cell)),
            angularSectorCounts: renderedTopologyCenter
                ? angularSectorCounts(
                    topologyCells.map((entry) => entry.renderedCenter),
                    renderedTopologyCenter,
                )
                : null,
        },
        overlapHotspots: null,
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
    let renderDiagnostics: RenderDiagnosticsSnapshot | null = null;
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

    function syncCanvasViewportAlignment(nextMetrics: GridMetrics): void {
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

    function drawGrid(): void {
        const adapter = getGeometryAdapter(geometry);
        const width = topologyWidth(topology);
        const height = topologyHeight(topology);
        const nextMetrics = adapter.buildMetrics({ width, height, cellSize, topology });
        const dpr = Math.max(1, getDevicePixelRatio());
        canvas.dataset.renderCellSize = String(cellSize);
        metrics = surface.resize(nextMetrics, dpr, canvasBorderRadius(nextMetrics.gap));
        syncCanvasViewportAlignment(nextMetrics);
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

    function getRenderDiagnostics(): RenderDiagnosticsSnapshot | null {
        if (!renderDiagnostics) {
            return null;
        }
        if (renderDiagnostics.overlapHotspots === null) {
            const polygonCache = asPolygonGeometryCache(geometryCache);
            const transformSampleIds = Object.values(renderDiagnostics.sampleCells)
                .map((sample) => sample?.cellId ?? null)
                .filter((cellId): cellId is string => typeof cellId === "string");
            renderDiagnostics = {
                ...renderDiagnostics,
                overlapHotspots: polygonCache
                    ? summarizePositiveAreaPolygonOverlaps(
                        polygonCache.cells,
                        { maxStoredPairs: 50, transformSampleIds },
                    )
                    : null,
            };
        }
        return structuredClone(renderDiagnostics);
    }

    function getRenderedCellCenter(cellId: string): { x: number; y: number } | null {
        const polygonCache = asPolygonGeometryCache(geometryCache);
        const renderedGeometry = polygonCache?.cellsById.get(cellId) ?? null;
        if (!renderedGeometry) {
            return null;
        }
        return {
            x: renderedGeometry.centerX,
            y: renderedGeometry.centerY,
        };
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
        getRenderDiagnostics,
        getRenderedCellCenter,
    };
}
