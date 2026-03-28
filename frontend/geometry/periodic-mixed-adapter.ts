import { tracePolygonPath } from "../canvas/draw.js";
import {
    buildMixedTopologyGeometryCache,
    resolveMixedCellFromOffset,
} from "../canvas/geometry-mixed.js";
import { asPolygonGeometryCache } from "./cache-guards.js";
import {
    applyMixedViewportPreview,
    constrainMixedViewportDimensions,
    fitGridDimension,
    fitRenderCellSizeWithMetrics,
} from "./shared.js";
import { getPeriodicFaceTilingDescriptor } from "./periodic-face-tilings.js";
import type { PaintableCell } from "../types/editor.js";
import type {
    GeometryAdapter,
    GeometryBuildCacheArgs,
    GeometryBuildMetricsArgs,
    GeometryResolveCellCenterArgs,
    GeometryResolveCellFromOffsetArgs,
    GeometryResolveCoordinateCenterArgs,
    GeometryViewportPreviewArgs,
    GridMetrics,
    PeriodicFaceTilingDescriptor,
    Point2D,
    PolygonGeometryCache,
    PolygonGeometryCell,
    RenderedCellArgs,
    RenderableTopologyCell,
} from "../types/rendering.js";
import type { TopologyPayload } from "../types/domain.js";

interface PatternMetrics extends GridMetrics {
    scale: number;
    baseMinX: number;
    baseMinY: number;
    unitWidth: number;
    unitHeight: number;
    rowOffsetX: number;
}

function descriptorScale(descriptor: PeriodicFaceTilingDescriptor | null, cellSize: number): number {
    return cellSize / (descriptor?.base_edge || 52);
}

function patternBounds(
    descriptor: PeriodicFaceTilingDescriptor,
    width: number,
    height: number,
): { minX: number; minY: number; maxX: number; maxY: number } {
    const unitWidth = descriptor?.unit_width || 0;
    const unitHeight = descriptor?.unit_height || 0;
    const rowOffsetX = descriptor?.row_offset_x || 0;
    const hasShiftedRows = Math.max(height, 1) > 1;
    const minX = Math.min(
        descriptor?.min_x || 0,
        (descriptor?.min_x || 0) + (hasShiftedRows && rowOffsetX < 0 ? rowOffsetX : 0),
    );
    const minY = descriptor?.min_y || 0;
    const maxX = (descriptor?.max_x || 0)
        + (Math.max(width, 1) - 1) * unitWidth
        + (hasShiftedRows && rowOffsetX > 0 ? rowOffsetX : 0);
    const maxY = (descriptor?.max_y || 0) + (Math.max(height, 1) - 1) * unitHeight;
    return {
        minX,
        minY,
        maxX,
        maxY,
    };
}

function topologyBounds(
    topology: TopologyPayload | null,
    descriptor: PeriodicFaceTilingDescriptor,
    width: number,
    height: number,
): { minX: number; minY: number; maxX: number; maxY: number } {
    const vertices = (topology?.cells || [])
        .flatMap((cell) => Array.isArray((cell as RenderableTopologyCell).vertices) ? (cell as RenderableTopologyCell).vertices || [] : []);
    if (vertices.length === 0) {
        return patternBounds(descriptor, width, height);
    }

    const xs = vertices.map((vertex) => Number(vertex.x));
    const ys = vertices.map((vertex) => Number(vertex.y));
    return {
        minX: Math.min(...xs),
        minY: Math.min(...ys),
        maxX: Math.max(...xs),
        maxY: Math.max(...ys),
    };
}

function buildPatternMetrics({
    descriptor,
    width,
    height,
    cellSize,
    topology = null,
}: {
    descriptor: PeriodicFaceTilingDescriptor;
    width: number;
    height: number;
    cellSize: number;
    topology?: TopologyPayload | null;
}): PatternMetrics {
    if (width === 0 || height === 0) {
        return {
            geometry: descriptor.geometry,
            width,
            height,
            cellSize,
            gap: 0,
            xInset: 1,
            yInset: 1,
            cssWidth: 0,
            cssHeight: 0,
            scale: descriptorScale(descriptor, cellSize),
            baseMinX: descriptor.min_x,
            baseMinY: descriptor.min_y,
            unitWidth: descriptor.unit_width,
            unitHeight: descriptor.unit_height,
            rowOffsetX: descriptor.row_offset_x || 0,
        };
    }

    const scale = descriptorScale(descriptor, cellSize);
    const bounds = topologyBounds(topology, descriptor, width, height);
    const cssWidth = 2 + ((bounds.maxX - bounds.minX) * scale);
    const cssHeight = 2 + ((bounds.maxY - bounds.minY) * scale);
    return {
        geometry: descriptor.geometry,
        width,
        height,
        cellSize,
        gap: 0,
        xInset: 1 - (bounds.minX * scale),
        yInset: 1 - (bounds.minY * scale),
        cssWidth,
        cssHeight,
        scale,
        baseMinX: bounds.minX,
        baseMinY: bounds.minY,
        unitWidth: descriptor.unit_width,
        unitHeight: descriptor.unit_height,
        rowOffsetX: descriptor.row_offset_x || 0,
    };
}

function estimatePatternDimension(
    viewportPixels: number,
    descriptor: PeriodicFaceTilingDescriptor,
    cellSize: number,
    axis: "width" | "height",
): number {
    const scale = descriptorScale(descriptor, cellSize);
    if (viewportPixels <= 0 || scale <= 0) {
        return descriptor.min_dimension;
    }

    const span = axis === "width"
        ? descriptor.max_x - descriptor.min_x
        : descriptor.max_y - descriptor.min_y;
    const unit = axis === "width" ? descriptor.unit_width : descriptor.unit_height;
    const availableBase = (viewportPixels - 2) / scale;
    if (availableBase <= 0) {
        return descriptor.min_dimension;
    }

    return Math.max(
        descriptor.min_dimension,
        Math.floor(Math.max(availableBase - span, 0) / unit) + 1,
    );
}

function patternViewportDimensions(
    descriptor: PeriodicFaceTilingDescriptor,
    viewportWidth: number,
    viewportHeight: number,
    cellSize: number,
) {
    const estimatedHeight = estimatePatternDimension(viewportHeight, descriptor, cellSize, "height");
    const height = fitGridDimension(
        estimatedHeight,
        (candidateHeight) => buildPatternMetrics({
            descriptor,
            width: 1,
            height: candidateHeight,
            cellSize,
        }).cssHeight <= viewportHeight,
        descriptor.min_dimension,
    );
    const estimatedWidth = estimatePatternDimension(viewportWidth, descriptor, cellSize, "width");
    const width = fitGridDimension(
        estimatedWidth,
        (candidateWidth) => buildPatternMetrics({
            descriptor,
            width: candidateWidth,
            height,
            cellSize,
        }).cssWidth <= viewportWidth,
        descriptor.min_dimension,
    );

    return constrainMixedViewportDimensions(
        { width, height },
        cellSize,
        (nextWidth, nextHeight) => descriptor.cell_count_per_unit * nextWidth * nextHeight,
        undefined,
        descriptor.min_dimension,
    );
}

function scaleVertices(vertices: Point2D[], metrics: PatternMetrics): Point2D[] {
    return vertices.map((vertex) => ({
        x: 1 + ((Number(vertex.x) - metrics.baseMinX) * metrics.scale),
        y: 1 + ((Number(vertex.y) - metrics.baseMinY) * metrics.scale),
    }));
}

function buildGeometryCellFromTopology(
    cell: RenderableTopologyCell,
    metrics: PatternMetrics,
): PolygonGeometryCell | null {
    if (!Array.isArray(cell?.vertices) || cell.vertices.length === 0) {
        return null;
    }

    const vertices = scaleVertices(cell.vertices, metrics);
    const minX = Math.min(...vertices.map((vertex) => vertex.x));
    const maxX = Math.max(...vertices.map((vertex) => vertex.x));
    const minY = Math.min(...vertices.map((vertex) => vertex.y));
    const maxY = Math.max(...vertices.map((vertex) => vertex.y));
    return {
        cell,
        vertices,
        centerX: 1 + ((Number(cell.center?.x ?? ((minX + maxX) / 2)) - metrics.baseMinX) * metrics.scale),
        centerY: 1 + ((Number(cell.center?.y ?? ((minY + maxY) / 2)) - metrics.baseMinY) * metrics.scale),
        minX,
        maxX,
        minY,
        maxY,
    };
}

function resolveGeometryCell(
    geometry: string,
    cell: RenderableTopologyCell,
    metrics: PatternMetrics,
    cache: PolygonGeometryCache | null,
): PolygonGeometryCell | null {
    if (cell?.id && cache?.cellsById?.has(cell.id)) {
        return cache.cellsById.get(cell.id) ?? null;
    }
    return buildGeometryCellFromTopology(cell, metrics);
}

function createPatternViewportFit(descriptor: PeriodicFaceTilingDescriptor) {
    return ({ viewportWidth, viewportHeight, cellSize }: { viewportWidth: number; viewportHeight: number; cellSize: number }) => patternViewportDimensions(
        descriptor,
        viewportWidth,
        viewportHeight,
        cellSize,
    );
}

function createMetricsBuilder(descriptor: PeriodicFaceTilingDescriptor) {
    return ({
        width,
        height,
        cellSize,
        topology,
    }: {
        width: number;
        height: number;
        cellSize: number;
        topology: TopologyPayload | null;
    }) => buildPatternMetrics({
        descriptor,
        width,
        height,
        cellSize,
        topology,
    });
}

export function createPeriodicMixedGeometryAdapter(geometry: string): GeometryAdapter {
    const descriptor = getPeriodicFaceTilingDescriptor(geometry);
    if (!descriptor) {
        throw new Error(`Missing periodic face tiling descriptor for geometry: ${geometry}`);
    }
    const buildMetrics = createMetricsBuilder(descriptor);
    const fitViewport = createPatternViewportFit(descriptor);

    return {
        geometry,
        family: "mixed",

        buildMetrics,

        fitViewport,

        fitRenderCellSize({ viewportWidth, viewportHeight, width, height, topology = null, fallbackCellSize }) {
            return fitRenderCellSizeWithMetrics({
                viewportWidth,
                viewportHeight,
                width,
                height,
                topology,
                fallbackCellSize,
                buildMetrics: ({ width: nextWidth, height: nextHeight, topology: nextTopology, cellSize }) => (
                    buildMetrics({
                        width: nextWidth,
                        height: nextHeight,
                        topology: nextTopology,
                        cellSize,
                    })
                ),
            });
        },

        buildCache({ topology, metrics }: GeometryBuildCacheArgs) {
            return buildMixedTopologyGeometryCache(topology, (cell) => (
                resolveGeometryCell(geometry, cell, metrics as PatternMetrics, null)
            ));
        },

        buildCellGeometry({ cell, metrics, cache }) {
            return resolveGeometryCell(
                geometry,
                cell as RenderableTopologyCell,
                metrics as PatternMetrics,
                asPolygonGeometryCache(cache),
            );
        },

        resolveCellFromOffset({ offsetX, offsetY, cache }: GeometryResolveCellFromOffsetArgs) {
            return resolveMixedCellFromOffset(
                offsetX,
                offsetY,
                cache && "cellsById" in cache ? cache : null,
            );
        },

        resolveCellCenter({ cell, width = 0, height = 0, cellSize, metrics, cache, topology = null }: GeometryResolveCellCenterArgs) {
            const resolvedMetrics = (metrics || buildMetrics({ width, height, cellSize, topology })) as PatternMetrics;
            const geometryCell = resolveGeometryCell(
                geometry,
                cell as RenderableTopologyCell,
                resolvedMetrics,
                asPolygonGeometryCache(cache),
            );
            return geometryCell
                ? { x: geometryCell.centerX, y: geometryCell.centerY }
                : { x: 0, y: 0 };
        },

        resolveCoordinateCenter({ x, y, cellSize, metrics }: GeometryResolveCoordinateCenterArgs) {
            const resolvedMetrics = (metrics || buildMetrics({
                width: Math.max(x + 1, 1),
                height: Math.max(y + 1, 1),
                cellSize,
                topology: null,
            })) as PatternMetrics;
            const scale = descriptorScale(descriptor, cellSize);
            const shiftX = y % 2 === 1 ? (descriptor.row_offset_x || 0) : 0;
            return {
                x: 1 + ((((x + 0.5) * descriptor.unit_width) + shiftX - resolvedMetrics.baseMinX) * scale),
                y: 1 + ((((y + 0.5) * descriptor.unit_height) - resolvedMetrics.baseMinY) * scale),
            };
        },

        drawCell({ context, cell, stateValue, metrics, cache, colors, colorLookup, resolveRenderedCellColor }: RenderedCellArgs) {
            const geometryCell = resolveGeometryCell(
                geometry,
                cell as RenderableTopologyCell,
                metrics as PatternMetrics,
                asPolygonGeometryCache(cache),
            );
            const color = resolveRenderedCellColor(
                stateValue,
                colorLookup,
                colors,
                { geometry, cell: geometryCell?.cell || cell },
            );
            if (!geometryCell) {
                return;
            }
            if (context.fillStyle !== color) {
                context.fillStyle = color;
            }
            tracePolygonPath(context, geometryCell.vertices);
            context.fill();
        },

        applyViewportPreview(args: GeometryViewportPreviewArgs) {
            return applyMixedViewportPreview(args);
        },
    };
}
