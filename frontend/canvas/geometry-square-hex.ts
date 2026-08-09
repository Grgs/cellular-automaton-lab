import { getCellGap } from "../geometry/shared.js";

interface PointyHexCenterCell {
    x: number;
    y: number;
    radius: number;
    hexWidth: number;
    horizontalPitch: number;
    verticalPitch: number;
}

export function pointyHexCenterOffset(x: number, y: number, cellSize: number): PointyHexCenterCell {
    const gap = getCellGap(cellSize);
    const radius = cellSize / 2;
    const hexWidth = Math.sqrt(3) * radius;
    const horizontalPitch = hexWidth + gap;
    const verticalPitch = 0.75 * cellSize + gap;
    const xInset = hexWidth / 2 + gap;
    const yInset = radius + gap;

    return {
        x: xInset + x * horizontalPitch + (y % 2 === 1 ? hexWidth / 2 : 0),
        y: yInset + y * verticalPitch,
        radius,
        hexWidth,
        horizontalPitch,
        verticalPitch,
    };
}
