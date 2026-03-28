import { triangleVertices } from "./geometry-triangle.js";
import type { CanvasRenderStyle, GeometryCache, Point2D } from "../types/rendering.js";

type PathTarget = CanvasRenderingContext2D | Path2D;

export function tracePolygonPath(context: CanvasRenderingContext2D, vertices: readonly Point2D[]): void {
    const [first, ...rest] = vertices;
    if (!first) {
        return;
    }
    context.beginPath();
    context.moveTo(first.x, first.y);
    rest.forEach((vertex) => {
        context.lineTo(vertex.x, vertex.y);
    });
    context.closePath();
}

export function appendPolygonPath(target: PathTarget, vertices: readonly Point2D[]): void {
    const [first, ...rest] = vertices;
    if (!first) {
        return;
    }
    target.moveTo(first.x, first.y);
    rest.forEach((vertex) => {
        target.lineTo(vertex.x, vertex.y);
    });
    target.closePath();
}

export function traceHexPath(
    context: CanvasRenderingContext2D,
    centerX: number,
    centerY: number,
    radius: number,
    hexWidth: number,
): void {
    const halfWidth = hexWidth / 2;
    const halfRadius = radius / 2;
    context.beginPath();
    context.moveTo(centerX, centerY - radius);
    context.lineTo(centerX + halfWidth, centerY - halfRadius);
    context.lineTo(centerX + halfWidth, centerY + halfRadius);
    context.lineTo(centerX, centerY + radius);
    context.lineTo(centerX - halfWidth, centerY + halfRadius);
    context.lineTo(centerX - halfWidth, centerY - halfRadius);
    context.closePath();
}

export function drawTriangleGrid(
    targetContext: CanvasRenderingContext2D,
    width: number,
    height: number,
    renderStyle: CanvasRenderStyle,
    geometryCache: GeometryCache | null,
    cellSize: number,
): void {
    if (!renderStyle.triangleStrokeEnabled) {
        return;
    }
    targetContext.strokeStyle = renderStyle.lineColor;
    targetContext.lineWidth = 1;
    if (geometryCache?.type === "triangle" && geometryCache.strokePath) {
        targetContext.stroke(geometryCache.strokePath);
        return;
    }

    for (let y = 0; y < height; y += 1) {
        for (let x = 0; x < width; x += 1) {
            tracePolygonPath(targetContext, triangleVertices(x, y, cellSize));
            targetContext.stroke();
        }
    }
}
