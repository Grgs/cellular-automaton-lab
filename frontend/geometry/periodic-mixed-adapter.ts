import {
    applyMixedViewportPreview,
    constrainMixedViewportDimensions,
    fitGridDimension,
    fitRenderCellSizeWithMetrics,
} from "./shared.js";
import {
    buildPolygonGeometryCache,
    buildTransformedPolygonGeometryCell,
    drawPolygonCacheOverlay,
    drawResolvedPolygonCell,
    measureTopologyVertexBounds,
    resolvePolygonCellCenter,
    resolvePolygonCellFromOffset,
    resolvePolygonGeometryCell,
} from "./polygon-adapter-shared.js";
import { asPolygonGeometryCache } from "./cache-guards.js";
import { getPeriodicFaceTilingDescriptor } from "./periodic-face-tilings.js";
import type {
    GeometryAdapter,
    GeometryBuildCacheArgs,
    GeometryBuildMetricsArgs,
    GeometryDrawOverlayArgs,
    GeometryResolveCellCenterArgs,
    GeometryResolveCoordinateCenterArgs,
    GeometryViewportPreviewArgs,
    GridMetrics,
    PeriodicFaceTilingDescriptor,
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

function descriptorScale(
    descriptor: PeriodicFaceTilingDescriptor | null,
    cellSize: number,
): number {
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
    const maxX =
        (descriptor?.max_x || 0) +
        (Math.max(width, 1) - 1) * unitWidth +
        (hasShiftedRows && rowOffsetX > 0 ? rowOffsetX : 0);
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
    const bounds = measureTopologyVertexBounds(topology);
    if (!bounds) {
        return patternBounds(descriptor, width, height);
    }
    return bounds;
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
    const cssWidth = 2 + (bounds.maxX - bounds.minX) * scale;
    const cssHeight = 2 + (bounds.maxY - bounds.minY) * scale;
    return {
        geometry: descriptor.geometry,
        width,
        height,
        cellSize,
        gap: 0,
        xInset: 1 - bounds.minX * scale,
        yInset: 1 - bounds.minY * scale,
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

    const span =
        axis === "width"
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
    const estimatedHeight = estimatePatternDimension(
        viewportHeight,
        descriptor,
        cellSize,
        "height",
    );
    const height = fitGridDimension(
        estimatedHeight,
        (candidateHeight) =>
            buildPatternMetrics({
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
        (candidateWidth) =>
            buildPatternMetrics({
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

function buildGeometryCellFromTopology(cell: RenderableTopologyCell, metrics: PatternMetrics) {
    return buildTransformedPolygonGeometryCell(
        cell,
        (vertex) => ({
            x: 1 + (Number(vertex.x) - metrics.baseMinX) * metrics.scale,
            y: 1 + (Number(vertex.y) - metrics.baseMinY) * metrics.scale,
        }),
        (center) =>
            center
                ? {
                      x: 1 + (Number(center.x) - metrics.baseMinX) * metrics.scale,
                      y: 1 + (Number(center.y) - metrics.baseMinY) * metrics.scale,
                  }
                : null,
    );
}

function createPatternViewportFit(descriptor: PeriodicFaceTilingDescriptor) {
    return ({
        viewportWidth,
        viewportHeight,
        cellSize,
    }: {
        viewportWidth: number;
        viewportHeight: number;
        cellSize: number;
    }) => patternViewportDimensions(descriptor, viewportWidth, viewportHeight, cellSize);
}

function createMetricsBuilder(descriptor: PeriodicFaceTilingDescriptor) {
    return ({ width, height, cellSize, topology }: GeometryBuildMetricsArgs) =>
        buildPatternMetrics({
            descriptor,
            width,
            height,
            cellSize,
            topology: topology ?? null,
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

        fitRenderCellSize({
            viewportWidth,
            viewportHeight,
            width,
            height,
            topology = null,
            fallbackCellSize,
        }) {
            return fitRenderCellSizeWithMetrics({
                viewportWidth,
                viewportHeight,
                width,
                height,
                topology,
                fallbackCellSize,
                buildMetrics: ({
                    width: nextWidth,
                    height: nextHeight,
                    topology: nextTopology,
                    cellSize,
                }) =>
                    buildMetrics({
                        width: nextWidth,
                        height: nextHeight,
                        topology: nextTopology,
                        cellSize,
                    }),
            });
        },

        buildCache({ topology, metrics }: GeometryBuildCacheArgs) {
            return buildPolygonGeometryCache(topology, (cell) =>
                buildGeometryCellFromTopology(cell, metrics as PatternMetrics),
            );
        },

        buildCellGeometry({ cell, metrics, cache }) {
            return resolvePolygonGeometryCell(
                cell as RenderableTopologyCell,
                asPolygonGeometryCache(cache),
                (uncachedCell) =>
                    buildGeometryCellFromTopology(uncachedCell, metrics as PatternMetrics),
            );
        },

        resolveCellFromOffset({ offsetX, offsetY, cache }) {
            return resolvePolygonCellFromOffset({ offsetX, offsetY, cache });
        },

        resolveCellCenter({
            cell,
            width = 0,
            height = 0,
            cellSize,
            metrics,
            cache,
            topology = null,
        }: GeometryResolveCellCenterArgs) {
            return resolvePolygonCellCenter({
                cell,
                width,
                height,
                cellSize,
                topology,
                metrics,
                cache,
                buildMetrics,
                buildCellGeometry: (nextCell, nextMetrics, polygonCache) =>
                    resolvePolygonGeometryCell(nextCell, polygonCache, (uncachedCell) =>
                        buildGeometryCellFromTopology(uncachedCell, nextMetrics as PatternMetrics),
                    ),
            });
        },

        resolveCoordinateCenter({ x, y, cellSize, metrics }: GeometryResolveCoordinateCenterArgs) {
            const resolvedMetrics = (metrics ||
                buildMetrics({
                    width: Math.max(x + 1, 1),
                    height: Math.max(y + 1, 1),
                    cellSize,
                    topology: null,
                })) as PatternMetrics;
            const scale = descriptorScale(descriptor, cellSize);
            const shiftX = y % 2 === 1 ? descriptor.row_offset_x || 0 : 0;
            return {
                x:
                    1 +
                    ((x + 0.5) * descriptor.unit_width + shiftX - resolvedMetrics.baseMinX) * scale,
                y: 1 + ((y + 0.5) * descriptor.unit_height - resolvedMetrics.baseMinY) * scale,
            };
        },

        drawCell({
            context,
            cell,
            stateValue,
            metrics,
            cache,
            colors,
            colorLookup,
            resolveRenderedCellColor,
            renderStyle,
            renderLayer,
        }: RenderedCellArgs) {
            const geometryCell = resolvePolygonGeometryCell(
                cell as RenderableTopologyCell,
                asPolygonGeometryCache(cache),
                (uncachedCell) =>
                    buildGeometryCellFromTopology(uncachedCell, metrics as PatternMetrics),
            );
            drawResolvedPolygonCell({
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
                drawPreviewStroke: true,
            });
        },

        drawOverlay({ context, cache, renderStyle }: GeometryDrawOverlayArgs) {
            drawPolygonCacheOverlay({ context, cache, renderStyle });
        },

        applyViewportPreview(args: GeometryViewportPreviewArgs) {
            return applyMixedViewportPreview(args);
        },
    };
}
