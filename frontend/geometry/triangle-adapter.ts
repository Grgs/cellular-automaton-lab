import {
    drawTriangleGrid,
    resolvePolygonStrokeWidth,
    resolveTransientOverlayStyle,
    tracePolygonPath,
} from "../canvas/draw.js";
import {
    applyRegularViewportPreview,
    clampGridDimension,
    fitGridDimension,
    fitRenderCellSizeWithMetrics,
    triangleGridMetrics,
} from "./shared.js";
import { parseRegularCellId, regularCellId } from "../topology.js";
import { asTriangleGeometryCache } from "./cache-guards.js";
import type { PaintableCell } from "../types/editor.js";
import type {
    GeometryAdapter,
    GeometryBuildCacheArgs,
    GeometryBuildMetricsArgs,
    GeometryDrawOverlayArgs,
    GeometryResolveCellCenterArgs,
    GeometryResolveCellFromOffsetArgs,
    GeometryResolveCoordinateCenterArgs,
    GeometryViewportPreviewArgs,
    GridMetrics,
    Point2D,
    RenderedCellArgs,
    TriangleGeometryCache,
    TriangleGeometryCell,
} from "../types/rendering.js";

interface TriangleMetrics extends GridMetrics {
    triangleSide: number;
    triangleHeight: number;
    horizontalPitch: number;
}

function triangleVertices(x: number, y: number, cellSize: number): Point2D[] {
    const triangleSide = cellSize;
    const triangleHeight = (Math.sqrt(3) * triangleSide) / 2;
    const horizontalPitch = triangleSide / 2;
    const leftX = 1 + x * horizontalPitch;
    const topY = 1 + y * triangleHeight;

    if ((x + y) % 2 === 0) {
        return [
            { x: leftX, y: topY + triangleHeight },
            { x: leftX + triangleSide / 2, y: topY },
            { x: leftX + triangleSide, y: topY + triangleHeight },
        ];
    }

    return [
        { x: leftX, y: topY },
        { x: leftX + triangleSide, y: topY },
        { x: leftX + triangleSide / 2, y: topY + triangleHeight },
    ];
}

function triangleVertexTriplet(vertices: readonly Point2D[]): [Point2D, Point2D, Point2D] | null {
    const [first, second, third] = vertices;
    if (!first || !second || !third) {
        return null;
    }
    return [first, second, third];
}

function buildTriangleGeometryCache(
    width: number,
    height: number,
    cellSize: number,
): TriangleGeometryCache {
    const cells: TriangleGeometryCell[][] = Array.from({ length: height }, () =>
        Array<TriangleGeometryCell>(width),
    );
    const strokePath = typeof Path2D === "undefined" ? null : new Path2D();

    for (let y = 0; y < height; y += 1) {
        const row = cells[y];
        if (!row) {
            continue;
        }
        for (let x = 0; x < width; x += 1) {
            const vertices = triangleVertices(x, y, cellSize);
            const triplet = triangleVertexTriplet(vertices);
            if (!triplet) {
                continue;
            }
            const [first, second, third] = triplet;
            const centerX = (first.x + second.x + third.x) / 3;
            const centerY = (first.y + second.y + third.y) / 3;
            const minX = Math.min(first.x, second.x, third.x);
            const maxX = Math.max(first.x, second.x, third.x);
            const minY = Math.min(first.y, second.y, third.y);
            const maxY = Math.max(first.y, second.y, third.y);
            const cell = {
                vertices,
                centerX,
                centerY,
                minX,
                maxX,
                minY,
                maxY,
            };
            row[x] = cell;
            if (strokePath) {
                strokePath.moveTo(first.x, first.y);
                strokePath.lineTo(second.x, second.y);
                strokePath.lineTo(third.x, third.y);
                strokePath.closePath();
            }
        }
    }

    return { type: "triangle", cells, strokePath };
}

function pointInTriangle(offsetX: number, offsetY: number, vertices: readonly Point2D[]): boolean {
    const triplet = triangleVertexTriplet(vertices);
    if (!triplet) {
        return false;
    }
    const [a, b, c] = triplet;
    const sign = (left: Point2D, right: Point2D, point: Point2D) =>
        (left.x - point.x) * (right.y - point.y) - (right.x - point.x) * (left.y - point.y);
    const point = { x: offsetX, y: offsetY };
    const d1 = sign(point, a, b);
    const d2 = sign(point, b, c);
    const d3 = sign(point, c, a);
    const hasNegative = d1 < 0 || d2 < 0 || d3 < 0;
    const hasPositive = d1 > 0 || d2 > 0 || d3 > 0;
    return !(hasNegative && hasPositive);
}

function estimateViewportHeight(viewportHeight: number, cellSize: number): number {
    const metrics = triangleGridMetrics(1, 1, cellSize) as TriangleMetrics;
    const available = viewportHeight - 2 * metrics.yInset;
    if (available <= 0) {
        return 5;
    }
    return Math.floor(available / metrics.triangleHeight);
}

function estimateViewportWidth(viewportWidth: number, cellSize: number): number {
    const metrics = triangleGridMetrics(1, 1, cellSize) as TriangleMetrics;
    const available = viewportWidth - 2 * metrics.xInset - metrics.triangleSide;
    if (available <= 0) {
        return 5;
    }
    return Math.floor(available / metrics.horizontalPitch) + 1;
}

function resolveTriangleCoordinates(cell: PaintableCell | null | undefined): {
    x: number;
    y: number;
} {
    const parsed = parseRegularCellId(cell?.id);
    return {
        x: typeof cell?.x === "number" && Number.isInteger(cell.x) ? cell.x : parsed?.x || 0,
        y: typeof cell?.y === "number" && Number.isInteger(cell.y) ? cell.y : parsed?.y || 0,
    };
}

export const triangleGeometryAdapter: GeometryAdapter = {
    geometry: "triangle",
    family: "regular",

    buildMetrics({ width, height, cellSize }: GeometryBuildMetricsArgs) {
        return triangleGridMetrics(width, height, cellSize);
    },

    fitViewport({ viewportWidth, viewportHeight, cellSize }) {
        const estimatedHeight = estimateViewportHeight(viewportHeight, cellSize);
        const height = fitGridDimension(
            estimatedHeight,
            (candidateHeight) =>
                triangleGridMetrics(1, candidateHeight, cellSize).cssHeight <= viewportHeight,
        );
        const estimatedWidth = estimateViewportWidth(viewportWidth, cellSize);
        const width = fitGridDimension(
            estimatedWidth,
            (candidateWidth) =>
                triangleGridMetrics(candidateWidth, height, cellSize).cssWidth <= viewportWidth,
        );
        return {
            width: clampGridDimension(width),
            height: clampGridDimension(height),
        };
    },

    fitRenderCellSize({ viewportWidth, viewportHeight, width, height, fallbackCellSize }) {
        return fitRenderCellSizeWithMetrics({
            viewportWidth,
            viewportHeight,
            width,
            height,
            fallbackCellSize,
            buildMetrics: ({ width: nextWidth, height: nextHeight, cellSize }) =>
                triangleGridMetrics(nextWidth, nextHeight, cellSize),
        });
    },

    buildCache({ width, height, cellSize, maxCachedCells }: GeometryBuildCacheArgs) {
        if (width * height > maxCachedCells) {
            return null;
        }
        return buildTriangleGeometryCache(width, height, cellSize);
    },

    resolveCellFromOffset({
        offsetX,
        offsetY,
        width,
        height,
        cellSize,
        metrics,
        cache,
    }: GeometryResolveCellFromOffsetArgs) {
        const resolvedMetrics = (metrics ||
            triangleGridMetrics(width, height, cellSize)) as TriangleMetrics;
        const triangleCache = asTriangleGeometryCache(cache);
        const approximateRow = Math.floor(
            (offsetY - resolvedMetrics.yInset) / resolvedMetrics.triangleHeight,
        );
        const approximateColumn = Math.round(
            (offsetX - resolvedMetrics.xInset) / resolvedMetrics.horizontalPitch,
        );

        for (let y = approximateRow - 1; y <= approximateRow + 1; y += 1) {
            if (y < 0 || y >= height) {
                continue;
            }
            for (let x = approximateColumn - 2; x <= approximateColumn + 2; x += 1) {
                if (x < 0 || x >= width) {
                    continue;
                }
                const cachedRow = triangleCache?.cells[y] ?? null;
                const resolvedCell = cachedRow?.[x] ?? {
                    vertices: triangleVertices(x, y, cellSize),
                };
                if (
                    "minX" in resolvedCell &&
                    typeof resolvedCell.minX === "number" &&
                    typeof resolvedCell.maxX === "number" &&
                    typeof resolvedCell.minY === "number" &&
                    typeof resolvedCell.maxY === "number" &&
                    (offsetX < resolvedCell.minX ||
                        offsetX > resolvedCell.maxX ||
                        offsetY < resolvedCell.minY ||
                        offsetY > resolvedCell.maxY)
                ) {
                    continue;
                }
                if (pointInTriangle(offsetX, offsetY, resolvedCell.vertices)) {
                    return { id: regularCellId(x, y), kind: "cell", x, y };
                }
            }
        }

        return null;
    },

    resolveCellCenter({ cell, cellSize, cache }: GeometryResolveCellCenterArgs) {
        const { x, y } = resolveTriangleCoordinates(cell);
        const triangleCache = asTriangleGeometryCache(cache);
        const cachedRow = triangleCache?.cells[y] ?? null;
        const resolvedCell = cachedRow?.[x] ?? { vertices: triangleVertices(x, y, cellSize) };
        if (
            "centerX" in resolvedCell &&
            typeof resolvedCell.centerX === "number" &&
            "centerY" in resolvedCell &&
            typeof resolvedCell.centerY === "number"
        ) {
            return { x: resolvedCell.centerX, y: resolvedCell.centerY };
        }
        const triplet = triangleVertexTriplet(resolvedCell.vertices);
        if (!triplet) {
            return { x: 0, y: 0 };
        }
        const [first, second, third] = triplet;
        return {
            x: (first.x + second.x + third.x) / 3,
            y: (first.y + second.y + third.y) / 3,
        };
    },

    resolveCoordinateCenter({ x, y, cellSize }: GeometryResolveCoordinateCenterArgs) {
        return this.resolveCellCenter({
            cell: { id: regularCellId(x, y), x, y },
            width: Math.max(x + 1, 1),
            height: Math.max(y + 1, 1),
            cellSize,
        });
    },

    drawCell({
        context,
        cell,
        stateValue,
        cache,
        colors,
        colorLookup,
        renderStyle,
        metrics,
        renderLayer,
        resolveRenderedCellColor,
    }: RenderedCellArgs) {
        const { x, y } = resolveTriangleCoordinates(cell);
        const overlayStyle = resolveTransientOverlayStyle(renderLayer, renderStyle);
        const color = resolveRenderedCellColor(stateValue, colorLookup, colors, {
            geometry: this.geometry,
            x,
            y,
        });
        const triangleCache = asTriangleGeometryCache(cache);
        const cachedRow = triangleCache?.cells[y] ?? null;
        const resolvedCell = cachedRow?.[x] ?? {
            vertices: triangleVertices(x, y, metrics.cellSize),
        };
        if (!overlayStyle || overlayStyle.drawBaseFill) {
            if (context.fillStyle !== color) {
                context.fillStyle = color;
            }
            tracePolygonPath(context, resolvedCell.vertices);
            context.fill();
        }
        if (overlayStyle) {
            if (overlayStyle.tintColor) {
                context.fillStyle = overlayStyle.tintColor;
                tracePolygonPath(context, resolvedCell.vertices);
                context.fill();
            }
            context.strokeStyle = overlayStyle.strokeColor;
            context.lineWidth = overlayStyle.strokeWidth;
            tracePolygonPath(context, resolvedCell.vertices);
            context.stroke();
            return;
        }
        if (renderLayer === "preview" && renderStyle?.triangleStrokeEnabled) {
            context.strokeStyle = renderStyle.lineColor;
            context.lineWidth = resolvePolygonStrokeWidth(renderStyle);
            tracePolygonPath(context, resolvedCell.vertices);
            context.stroke();
        }
    },

    drawOverlay({ context, width, height, cache, renderStyle, cellSize }: GeometryDrawOverlayArgs) {
        drawTriangleGrid(context, width, height, renderStyle, cache, cellSize);
    },

    applyViewportPreview(args: GeometryViewportPreviewArgs) {
        return applyRegularViewportPreview({
            geometry: this.geometry,
            ...args,
        });
    },
};
