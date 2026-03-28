import { triangleGridMetrics } from "../geometry/shared.js";
import type { GridMetrics, Point2D, TriangleGeometryCell } from "../types/rendering.js";

interface TriangleMetrics extends GridMetrics {
    triangleHeight: number;
    horizontalPitch: number;
    yInset: number;
    xInset: number;
}

export function triangleLayout(cellSize: number): {
    triangleSide: number;
    triangleHeight: number;
    horizontalPitch: number;
    xInset: number;
    yInset: number;
} {
    const triangleSide = cellSize;
    const triangleHeight = (Math.sqrt(3) * triangleSide) / 2;
    const horizontalPitch = triangleSide / 2;
    const inset = 1;

    return {
        triangleSide,
        triangleHeight,
        horizontalPitch,
        xInset: inset,
        yInset: inset,
    };
}

export function triangleOrientation(x: number, y: number): "up" | "down" {
    return (x + y) % 2 === 0 ? "up" : "down";
}

export function triangleVertices(x: number, y: number, cellSize: number): Point2D[] {
    const { xInset, yInset, triangleSide, triangleHeight, horizontalPitch } = triangleLayout(cellSize);
    const leftX = xInset + (x * horizontalPitch);
    const topY = yInset + (y * triangleHeight);

    if (triangleOrientation(x, y) === "up") {
        return [
            { x: leftX, y: topY + triangleHeight },
            { x: leftX + (triangleSide / 2), y: topY },
            { x: leftX + triangleSide, y: topY + triangleHeight },
        ];
    }

    return [
        { x: leftX, y: topY },
        { x: leftX + triangleSide, y: topY },
        { x: leftX + (triangleSide / 2), y: topY + triangleHeight },
    ];
}

export function triangleCenterOffset(x: number, y: number, cellSize: number): Point2D {
    const vertices = triangleVertices(x, y, cellSize);
    const [first, second, third] = vertices;
    if (!first || !second || !third) {
        return { x: 0, y: 0 };
    }
    return {
        x: (first.x + second.x + third.x) / 3,
        y: (first.y + second.y + third.y) / 3,
    };
}

function pointInTriangle(offsetX: number, offsetY: number, vertices: readonly Point2D[]): boolean {
    const [a, b, c] = vertices;
    if (!a || !b || !c) {
        return false;
    }
    const sign = (left: Point2D, right: Point2D, point: Point2D) => (
        ((left.x - point.x) * (right.y - point.y))
        - ((right.x - point.x) * (left.y - point.y))
    );
    const point = { x: offsetX, y: offsetY };
    const d1 = sign(point, a, b);
    const d2 = sign(point, b, c);
    const d3 = sign(point, c, a);
    const hasNegative = d1 < 0 || d2 < 0 || d3 < 0;
    const hasPositive = d1 > 0 || d2 > 0 || d3 > 0;
    return !(hasNegative && hasPositive);
}

export function resolveTriangleCellFromOffset(
    offsetX: number,
    offsetY: number,
    width: number,
    height: number,
    cellSize: number,
    metrics: GridMetrics | null = null,
    geometryCache: { type?: string; cells?: TriangleGeometryCell[][] } | null = null,
): { x: number; y: number } | null {
    const resolvedMetrics = (metrics || triangleGridMetrics(width, height, cellSize)) as TriangleMetrics;
    const approximateRow = Math.floor((offsetY - resolvedMetrics.yInset) / resolvedMetrics.triangleHeight);
    const approximateColumn = Math.round((offsetX - resolvedMetrics.xInset) / resolvedMetrics.horizontalPitch);

    for (let y = approximateRow - 1; y <= approximateRow + 1; y += 1) {
        if (y < 0 || y >= height) {
            continue;
        }
        for (let x = approximateColumn - 2; x <= approximateColumn + 2; x += 1) {
            if (x < 0 || x >= width) {
                continue;
            }
            const cachedRow = geometryCache?.type === "triangle" && Array.isArray(geometryCache.cells)
                ? geometryCache.cells[y]
                : null;
            const cell = cachedRow?.[x] ?? { vertices: triangleVertices(x, y, cellSize) };
            if (
                "minX" in cell
                && typeof cell.minX === "number"
                && typeof cell.maxX === "number"
                && typeof cell.minY === "number"
                && typeof cell.maxY === "number"
            ) {
                if (offsetX < cell.minX || offsetX > cell.maxX || offsetY < cell.minY || offsetY > cell.maxY) {
                    continue;
                }
            }
            if (pointInTriangle(offsetX, offsetY, cell.vertices)) {
                return { x, y };
            }
        }
    }

    return null;
}
