import { getCellGap, hexGridMetrics, squareGridMetrics } from "../geometry/shared.js";
import type { GridMetrics, HexGeometryCell } from "../types/rendering.js";

interface PointyHexCenterCell {
    x: number;
    y: number;
    radius: number;
    hexWidth: number;
    horizontalPitch: number;
    verticalPitch: number;
}

interface SquareMetrics extends GridMetrics {
    pitch: number;
}

interface HexMetrics extends GridMetrics {
    radius: number;
    hexWidth: number;
    horizontalPitch: number;
    verticalPitch: number;
    xInset: number;
    yInset: number;
}

export function pointyHexCenterOffset(x: number, y: number, cellSize: number): PointyHexCenterCell {
    const gap = getCellGap(cellSize);
    const radius = cellSize / 2;
    const hexWidth = Math.sqrt(3) * radius;
    const horizontalPitch = hexWidth + gap;
    const verticalPitch = (0.75 * cellSize) + gap;
    const xInset = (hexWidth / 2) + gap;
    const yInset = radius + gap;

    return {
        x: xInset + (x * horizontalPitch) + (y % 2 === 1 ? hexWidth / 2 : 0),
        y: yInset + (y * verticalPitch),
        radius,
        hexWidth,
        horizontalPitch,
        verticalPitch,
    };
}

export function squareCenterOffset(x: number, y: number, cellSize: number): { x: number; y: number } {
    const gap = getCellGap(cellSize);
    const pitch = cellSize + gap;
    return {
        x: gap + (x * pitch) + (cellSize / 2),
        y: gap + (y * pitch) + (cellSize / 2),
    };
}

export function resolveSquareCellFromOffset(
    offsetX: number,
    offsetY: number,
    width: number,
    height: number,
    cellSize: number,
    metrics: GridMetrics | null = null,
): { x: number; y: number } | null {
    const resolvedMetrics = (metrics || squareGridMetrics(width, height, cellSize)) as SquareMetrics;
    if (offsetX < resolvedMetrics.gap || offsetY < resolvedMetrics.gap) {
        return null;
    }

    const x = Math.floor((offsetX - resolvedMetrics.gap) / resolvedMetrics.pitch);
    const y = Math.floor((offsetY - resolvedMetrics.gap) / resolvedMetrics.pitch);
    if (x < 0 || y < 0 || x >= width || y >= height) {
        return null;
    }

    const localX = (offsetX - resolvedMetrics.gap) % resolvedMetrics.pitch;
    const localY = (offsetY - resolvedMetrics.gap) % resolvedMetrics.pitch;
    if (localX >= cellSize || localY >= cellSize) {
        return null;
    }

    return { x, y };
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

export function resolveHexCellFromOffset(
    offsetX: number,
    offsetY: number,
    width: number,
    height: number,
    cellSize: number,
    metrics: GridMetrics | null = null,
    geometryCache: { type?: string; cells?: HexGeometryCell[][] } | null = null,
): { x: number; y: number } | null {
    const resolvedMetrics = (metrics || hexGridMetrics(width, height, cellSize)) as HexMetrics;
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
            const cachedRow = geometryCache?.type === "hex" && Array.isArray(geometryCache.cells)
                ? geometryCache.cells[y]
                : null;
            const cachedCell = cachedRow?.[x];
            const cell = cachedCell ?? pointyHexCenterOffset(x, y, cellSize);
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
                return { x, y };
            }
        }
    }

    return null;
}
