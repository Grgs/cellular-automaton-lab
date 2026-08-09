import type { Point2D } from "../types/rendering.js";

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
    const { xInset, yInset, triangleSide, triangleHeight, horizontalPitch } =
        triangleLayout(cellSize);
    const leftX = xInset + x * horizontalPitch;
    const topY = yInset + y * triangleHeight;

    if (triangleOrientation(x, y) === "up") {
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
