import { drawPolygonCellWithTransientOverlay, drawPolygonGrid } from "../canvas/draw.js";
import {
    buildMixedTopologyGeometryCache,
    resolveMixedCellFromOffset,
} from "../canvas/geometry-mixed.js";
import type { TopologyPayload } from "../types/domain.js";
import type {
    GeometryBuildMetricsArgs,
    GeometryDrawOverlayArgs,
    GeometryResolveCellCenterArgs,
    GeometryResolveCellFromOffsetArgs,
    GridMetrics,
    Point2D,
    PolygonGeometryCache,
    PolygonGeometryCell,
    RenderedCellArgs,
    RenderableTopologyCell,
} from "../types/rendering.js";
import { asPolygonGeometryCache } from "./cache-guards.js";

interface PolygonBounds {
    minX: number;
    maxX: number;
    minY: number;
    maxY: number;
}

function normalizePoint(point: Point2D | null | undefined): Point2D | null {
    if (!point) {
        return null;
    }
    const x = Number(point.x);
    const y = Number(point.y);
    if (!Number.isFinite(x) || !Number.isFinite(y)) {
        return null;
    }
    return { x, y };
}

export function measurePolygonBounds(
    points: readonly Point2D[],
    fallbackCenter: Point2D | null = null,
): PolygonBounds | null {
    const normalizedPoints = points
        .map((point) => normalizePoint(point))
        .filter((point): point is Point2D => point !== null);
    const resolvedFallback = normalizePoint(fallbackCenter);
    const source =
        normalizedPoints.length > 0 ? normalizedPoints : resolvedFallback ? [resolvedFallback] : [];
    if (source.length === 0) {
        return null;
    }

    const xs = source.map((point) => point.x);
    const ys = source.map((point) => point.y);
    return {
        minX: Math.min(...xs),
        maxX: Math.max(...xs),
        minY: Math.min(...ys),
        maxY: Math.max(...ys),
    };
}

export function measureTopologyVertexBounds(
    topology: TopologyPayload | null,
    transformVertex: (vertex: Point2D, cell: RenderableTopologyCell) => Point2D = (vertex) =>
        vertex,
): PolygonBounds | null {
    const transformedVertices: Point2D[] = [];
    for (const rawCell of topology?.cells ?? []) {
        const cell = rawCell as RenderableTopologyCell;
        for (const rawVertex of cell.vertices ?? []) {
            const vertex = normalizePoint(transformVertex(rawVertex, cell));
            if (vertex) {
                transformedVertices.push(vertex);
            }
        }
    }
    return measurePolygonBounds(transformedVertices);
}

export function buildTransformedPolygonGeometryCell(
    cell: RenderableTopologyCell,
    transformVertex: (vertex: Point2D, cell: RenderableTopologyCell) => Point2D,
    transformCenter?: (
        center: Point2D | null | undefined,
        cell: RenderableTopologyCell,
    ) => Point2D | null,
): PolygonGeometryCell | null {
    const vertices = (cell.vertices ?? [])
        .map((vertex) => normalizePoint(transformVertex(vertex, cell)))
        .filter((vertex): vertex is Point2D => vertex !== null);
    const center =
        typeof transformCenter === "function"
            ? normalizePoint(transformCenter(cell.center, cell))
            : null;
    const bounds = measurePolygonBounds(vertices, center);
    if (!bounds) {
        return null;
    }

    return {
        cell,
        vertices,
        centerX: center?.x ?? (bounds.minX + bounds.maxX) / 2,
        centerY: center?.y ?? (bounds.minY + bounds.maxY) / 2,
        minX: bounds.minX,
        maxX: bounds.maxX,
        minY: bounds.minY,
        maxY: bounds.maxY,
    };
}

export function resolvePolygonGeometryCell(
    cell: RenderableTopologyCell,
    cache: PolygonGeometryCache | null,
    buildCellGeometry: (cell: RenderableTopologyCell) => PolygonGeometryCell | null,
): PolygonGeometryCell | null {
    if (cell?.id && cache?.cellsById?.has(cell.id)) {
        return cache.cellsById.get(cell.id) ?? null;
    }
    return buildCellGeometry(cell);
}

export function buildPolygonGeometryCache(
    topology: TopologyPayload | null,
    buildCellGeometry: (cell: RenderableTopologyCell) => PolygonGeometryCell | null,
): PolygonGeometryCache {
    return buildMixedTopologyGeometryCache(topology, buildCellGeometry);
}

export function resolvePolygonCellFromOffset({
    offsetX,
    offsetY,
    cache,
}: {
    offsetX: number;
    offsetY: number;
    cache?: GeometryResolveCellFromOffsetArgs["cache"] | undefined;
}) {
    return resolveMixedCellFromOffset(offsetX, offsetY, asPolygonGeometryCache(cache));
}

export function resolvePolygonCellCenter<TMetrics extends GridMetrics>({
    cell,
    width = 0,
    height = 0,
    cellSize,
    topology = null,
    metrics,
    cache,
    buildMetrics,
    buildCellGeometry,
}: {
    cell: GeometryResolveCellCenterArgs["cell"];
    width?: number;
    height?: number;
    cellSize: number;
    topology?: TopologyPayload | null | undefined;
    metrics?: TMetrics | null | undefined;
    cache?: GeometryResolveCellCenterArgs["cache"] | undefined;
    buildMetrics: (args: GeometryBuildMetricsArgs) => TMetrics;
    buildCellGeometry: (
        cell: RenderableTopologyCell,
        metrics: TMetrics,
        cache: PolygonGeometryCache | null,
    ) => PolygonGeometryCell | null;
}): Point2D {
    const polygonCache = asPolygonGeometryCache(cache);
    const renderableCell = cell as RenderableTopologyCell;
    if (renderableCell?.id && polygonCache?.cellsById?.has(renderableCell.id)) {
        const cachedCell = polygonCache.cellsById.get(renderableCell.id) ?? null;
        if (cachedCell) {
            return { x: cachedCell.centerX, y: cachedCell.centerY };
        }
    }

    const resolvedMetrics = (metrics ??
        buildMetrics({
            width,
            height,
            cellSize,
            topology,
        })) as TMetrics;
    const geometryCell = buildCellGeometry(renderableCell, resolvedMetrics, polygonCache);
    return geometryCell ? { x: geometryCell.centerX, y: geometryCell.centerY } : { x: 0, y: 0 };
}

export function drawResolvedPolygonCell({
    geometry,
    geometryCell,
    cell,
    stateValue,
    context,
    colors,
    colorLookup,
    resolveRenderedCellColor,
    renderLayer,
    renderStyle,
    resolvedFillColor = null,
    drawPreviewStroke = false,
    committedStrokeColor = null,
    fillBridgeColor = null,
    fillBridgeStrokeWidth = 0,
}: {
    geometry: string;
    geometryCell: PolygonGeometryCell | null;
    cell: RenderedCellArgs["cell"];
    stateValue: number;
    context: RenderedCellArgs["context"];
    colors: RenderedCellArgs["colors"];
    colorLookup: RenderedCellArgs["colorLookup"];
    resolveRenderedCellColor: RenderedCellArgs["resolveRenderedCellColor"];
    renderLayer?: RenderedCellArgs["renderLayer"] | undefined;
    renderStyle?: RenderedCellArgs["renderStyle"] | undefined;
    resolvedFillColor?: string | null;
    drawPreviewStroke?: boolean;
    committedStrokeColor?: string | null;
    fillBridgeColor?: string | null;
    fillBridgeStrokeWidth?: number;
}): void {
    if (!geometryCell) {
        return;
    }

    const color =
        resolvedFillColor ??
        resolveRenderedCellColor(stateValue, colorLookup, colors, {
            geometry,
            cell: geometryCell.cell || cell,
        });
    drawPolygonCellWithTransientOverlay({
        context,
        vertices: geometryCell.vertices,
        fillColor: color,
        renderLayer,
        renderStyle,
        committedStrokeColor,
        drawPreviewStroke,
        fillBridgeColor,
        fillBridgeStrokeWidth,
    });
}

export function drawPolygonCacheOverlay({
    context,
    cache,
    renderStyle,
}: Pick<GeometryDrawOverlayArgs, "context" | "cache" | "renderStyle">): void {
    drawPolygonGrid(context, renderStyle, asPolygonGeometryCache(cache));
}
