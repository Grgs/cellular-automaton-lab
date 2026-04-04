import { traceHexPath } from "../canvas/draw.js";
import {
    applyRegularViewportPreview,
    clampGridDimension,
    fitGridDimension,
    fitRenderCellSizeWithMetrics,
    hexGridMetrics,
} from "./shared.js";
import { parseRegularCellId, regularCellId } from "../topology.js";
import { asHexGeometryCache } from "./cache-guards.js";
import type { PaintableCell } from "../types/editor.js";
import type {
    GeometryAdapter,
    GeometryBuildCacheArgs,
    GeometryBuildMetricsArgs,
    HexGeometryCache,
    HexGeometryCell,
    GeometryResolveCellCenterArgs,
    GeometryResolveCellFromOffsetArgs,
    GeometryResolveCoordinateCenterArgs,
    GeometryViewportPreviewArgs,
    GridMetrics,
    RenderedCellArgs,
} from "../types/rendering.js";

interface PointyHexCenterCell {
    x: number;
    y: number;
    radius: number;
    hexWidth: number;
    horizontalPitch: number;
    verticalPitch: number;
}

interface HexMetrics extends GridMetrics {
    radius: number;
    hexWidth: number;
    horizontalPitch: number;
    verticalPitch: number;
    xInset: number;
    yInset: number;
    oddRowOffset: number;
    hexHeight: number;
}

function pointyHexCenterOffset(
    x: number,
    y: number,
    cellSize: number,
    metrics: GridMetrics | null = null,
): PointyHexCenterCell {
    const resolvedMetrics = (metrics || hexGridMetrics(Math.max(x + 1, 1), Math.max(y + 1, 1), cellSize)) as HexMetrics;
    return {
        x: resolvedMetrics.xInset + (x * resolvedMetrics.horizontalPitch) + (y % 2 === 1 ? resolvedMetrics.hexWidth / 2 : 0),
        y: resolvedMetrics.yInset + (y * resolvedMetrics.verticalPitch),
        radius: resolvedMetrics.radius,
        hexWidth: resolvedMetrics.hexWidth,
        horizontalPitch: resolvedMetrics.horizontalPitch,
        verticalPitch: resolvedMetrics.verticalPitch,
    };
}

function pointInPointyHex(
    offsetX: number,
    offsetY: number,
    centerX: number,
    centerY: number,
    radius: number,
    hexWidth: number,
): boolean {
    const dx = Math.abs(offsetX - centerX);
    const dy = Math.abs(offsetY - centerY);
    if (dy > radius || dx > hexWidth / 2) {
        return false;
    }
    if (dy <= radius / 2) {
        return true;
    }
    return dx <= (hexWidth * (radius - dy)) / radius;
}

function buildHexGeometryCache(width: number, height: number, metrics: HexMetrics): HexGeometryCache {
    const cells: HexGeometryCell[][] = Array.from({ length: height }, () => Array<HexGeometryCell>(width));

    for (let y = 0; y < height; y += 1) {
        const rowOffset = y % 2 === 1 ? metrics.hexWidth / 2 : 0;
        const row = cells[y];
        if (!row) {
            continue;
        }
        for (let x = 0; x < width; x += 1) {
            const centerX = metrics.xInset + (x * metrics.horizontalPitch) + rowOffset;
            const centerY = metrics.yInset + (y * metrics.verticalPitch);
            row[x] = {
                centerX,
                centerY,
                radius: metrics.radius,
                hexWidth: metrics.hexWidth,
                minX: centerX - (metrics.hexWidth / 2),
                maxX: centerX + (metrics.hexWidth / 2),
                minY: centerY - metrics.radius,
                maxY: centerY + metrics.radius,
            };
        }
    }

    return { type: "hex", cells };
}

function estimateViewportHeight(viewportHeight: number, cellSize: number): number {
    const metrics = hexGridMetrics(1, 1, cellSize) as HexMetrics;
    const available = viewportHeight - (2 * metrics.yInset) - metrics.hexHeight;
    if (available <= 0) {
        return 5;
    }
    return Math.floor(available / metrics.verticalPitch) + 1;
}

function estimateViewportWidth(viewportWidth: number, height: number, cellSize: number): number {
    const metrics = hexGridMetrics(1, Math.max(height, 2), cellSize) as HexMetrics;
    const available = viewportWidth - (2 * metrics.xInset) - metrics.oddRowOffset - metrics.hexWidth;
    if (available <= 0) {
        return 5;
    }
    return Math.floor(available / metrics.horizontalPitch) + 1;
}

function resolveHexCoordinates(cell: PaintableCell | null | undefined): { x: number; y: number } {
    const parsed = parseRegularCellId(cell?.id);
    return {
        x: typeof cell?.x === "number" && Number.isInteger(cell.x) ? cell.x : parsed?.x || 0,
        y: typeof cell?.y === "number" && Number.isInteger(cell.y) ? cell.y : parsed?.y || 0,
    };
}

export const hexGeometryAdapter: GeometryAdapter = {
    geometry: "hex",
    family: "regular",

    buildMetrics({ width, height, cellSize }: GeometryBuildMetricsArgs) {
        return hexGridMetrics(width, height, cellSize);
    },

    fitViewport({ viewportWidth, viewportHeight, cellSize }) {
        const estimatedHeight = estimateViewportHeight(viewportHeight, cellSize);
        const height = fitGridDimension(
            estimatedHeight,
            (candidateHeight) => hexGridMetrics(1, candidateHeight, cellSize).cssHeight <= viewportHeight,
        );
        const estimatedWidth = estimateViewportWidth(viewportWidth, height, cellSize);
        const width = fitGridDimension(
            estimatedWidth,
            (candidateWidth) => hexGridMetrics(candidateWidth, height, cellSize).cssWidth <= viewportWidth,
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
            buildMetrics: ({ width: nextWidth, height: nextHeight, cellSize }) => hexGridMetrics(nextWidth, nextHeight, cellSize),
        });
    },

    buildCache({ width, height, metrics, maxCachedCells }: GeometryBuildCacheArgs) {
        if ((width * height) > maxCachedCells) {
            return null;
        }
        return buildHexGeometryCache(width, height, metrics as HexMetrics);
    },

    resolveCellFromOffset({ offsetX, offsetY, width, height, cellSize, metrics, cache }: GeometryResolveCellFromOffsetArgs) {
        const resolvedMetrics = (metrics || hexGridMetrics(width, height, cellSize)) as HexMetrics;
        const hexCache = asHexGeometryCache(cache);
        const approximateRow = Math.round((offsetY - resolvedMetrics.yInset) / resolvedMetrics.verticalPitch);

        for (let y = approximateRow - 1; y <= approximateRow + 1; y += 1) {
            if (y < 0 || y >= height) {
                continue;
            }
            const rowOffset = y % 2 === 1 ? resolvedMetrics.hexWidth / 2 : 0;
            const approximateColumn = Math.round((offsetX - resolvedMetrics.xInset - rowOffset) / resolvedMetrics.horizontalPitch);

            for (let x = approximateColumn - 1; x <= approximateColumn + 1; x += 1) {
                if (x < 0 || x >= width) {
                    continue;
                }
                const cachedRow = hexCache?.cells[y] ?? null;
                const cachedCell = cachedRow?.[x];
                const cell = cachedCell ?? pointyHexCenterOffset(x, y, cellSize, resolvedMetrics);
                const centerX = "centerX" in cell ? cell.centerX : cell.x;
                const centerY = "centerY" in cell ? cell.centerY : cell.y;
                const radius = cell.radius;
                const hexWidth = cell.hexWidth;
                if (offsetX < centerX - (hexWidth / 2) || offsetX > centerX + (hexWidth / 2)) {
                    continue;
                }
                if (offsetY < centerY - radius || offsetY > centerY + radius) {
                    continue;
                }
                if (pointInPointyHex(offsetX, offsetY, centerX, centerY, radius, hexWidth)) {
                    return { id: regularCellId(x, y), kind: "cell", x, y };
                }
            }
        }

        return null;
    },

    resolveCellCenter({ cell, width = 0, height = 0, cellSize, metrics, cache }: GeometryResolveCellCenterArgs) {
        const { x, y } = resolveHexCoordinates(cell);
        const hexCache = asHexGeometryCache(cache);
        const cachedRow = hexCache?.cells[y] ?? null;
        const cachedCell = cachedRow?.[x]
            ? cachedRow[x]
            : pointyHexCenterOffset(
                x,
                y,
                cellSize,
                metrics || hexGridMetrics(Math.max(width, x + 1, 1), Math.max(height, y + 1, 1), cellSize),
            );
        return {
            x: "centerX" in cachedCell ? cachedCell.centerX : cachedCell.x,
            y: "centerY" in cachedCell ? cachedCell.centerY : cachedCell.y,
        };
    },

    resolveCoordinateCenter({ x, y, cellSize, metrics }: GeometryResolveCoordinateCenterArgs) {
        return this.resolveCellCenter({
            cell: { id: regularCellId(x, y), x, y },
            width: Math.max(x + 1, 1),
            height: Math.max(y + 1, 1),
            cellSize,
            metrics: metrics ?? null,
        });
    },

    drawCell({ context, cell, stateValue, metrics, cache, colors, colorLookup, resolveRenderedCellColor }: RenderedCellArgs) {
        const { x, y } = resolveHexCoordinates(cell);
        const hexMetrics = metrics as HexMetrics;
        const hexCache = asHexGeometryCache(cache);
        const color = resolveRenderedCellColor(
            stateValue,
            colorLookup,
            colors,
            { geometry: this.geometry, x, y },
        );
        if (context.fillStyle !== color) {
            context.fillStyle = color;
        }
        const cachedRow = hexCache?.cells[y] ?? null;
        const resolvedCell = cachedRow?.[x]
            ? cachedRow[x]
            : pointyHexCenterOffset(x, y, hexMetrics.cellSize, hexMetrics);
        const centerX = "centerX" in resolvedCell ? resolvedCell.centerX : resolvedCell.x;
        const centerY = "centerY" in resolvedCell ? resolvedCell.centerY : resolvedCell.y;
        traceHexPath(context, centerX, centerY, resolvedCell.radius, resolvedCell.hexWidth);
        context.fill();
    },

    applyViewportPreview(args: GeometryViewportPreviewArgs) {
        return applyRegularViewportPreview({
            geometry: this.geometry,
            ...args,
        });
    },
};
