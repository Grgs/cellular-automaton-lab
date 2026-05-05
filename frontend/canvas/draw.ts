import { triangleVertices } from "./geometry-triangle.js";
import {
    COMPACT_POLYGON_STROKE_WIDTH,
    GESTURE_OUTLINE_MIN_STROKE_WIDTH,
    HOVER_MIN_STROKE_WIDTH,
    SELECTION_MIN_STROKE_WIDTH,
    SHIELD_FILL_BRIDGE_STROKE_WIDTH,
    STANDARD_POLYGON_STROKE_WIDTH,
} from "./render-constants.js";
import type {
    CanvasRenderStyle,
    GeometryCache,
    Point2D,
    PolygonGeometryCache,
    RenderedCellArgs,
} from "../types/rendering.js";

type PathTarget = CanvasRenderingContext2D | Path2D;

interface DrawPolygonCellArgs {
    context: CanvasRenderingContext2D;
    vertices: readonly Point2D[];
    fillColor: string;
    renderLayer: RenderedCellArgs["renderLayer"];
    renderStyle: CanvasRenderStyle | undefined;
    committedStrokeColor?: string | null;
    drawPreviewStroke?: boolean;
    fillBridgeColor?: string | null;
    fillBridgeStrokeWidth?: number;
}

export function tracePolygonPath(
    context: CanvasRenderingContext2D,
    vertices: readonly Point2D[],
): void {
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
    targetContext.lineWidth = resolvePolygonStrokeWidth(renderStyle);
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

export function resolvePolygonStrokeWidth(renderStyle: CanvasRenderStyle): number {
    return renderStyle.mode === "compact"
        ? COMPACT_POLYGON_STROKE_WIDTH
        : STANDARD_POLYGON_STROKE_WIDTH;
}

export function resolveShieldFillBridgeStrokeWidth(
    renderStyle: CanvasRenderStyle | undefined,
): number {
    return Math.max(
        SHIELD_FILL_BRIDGE_STROKE_WIDTH,
        renderStyle ? resolvePolygonStrokeWidth(renderStyle) : SHIELD_FILL_BRIDGE_STROKE_WIDTH,
    );
}

export function resolveTransientOverlayStyle(
    renderLayer: RenderedCellArgs["renderLayer"],
    renderStyle: CanvasRenderStyle | undefined,
): {
    tintColor: string | null;
    strokeColor: string;
    strokeWidth: number;
    drawBaseFill: boolean;
} | null {
    if (!renderStyle) {
        return null;
    }
    if (renderLayer === "hover") {
        return {
            tintColor: renderStyle.hoverTintColor,
            strokeColor: renderStyle.hoverStrokeColor,
            strokeWidth: Math.max(resolvePolygonStrokeWidth(renderStyle), HOVER_MIN_STROKE_WIDTH),
            drawBaseFill: true,
        };
    }
    if (renderLayer === "selected") {
        return {
            tintColor: renderStyle.selectionTintColor,
            strokeColor: renderStyle.selectionStrokeColor,
            strokeWidth: Math.max(
                resolvePolygonStrokeWidth(renderStyle) + 1,
                SELECTION_MIN_STROKE_WIDTH,
            ),
            drawBaseFill: true,
        };
    }
    if (renderLayer === "gesture-paint") {
        return {
            tintColor: null,
            strokeColor: renderStyle.gesturePaintStrokeColor,
            strokeWidth: Math.max(
                resolvePolygonStrokeWidth(renderStyle) + 1,
                GESTURE_OUTLINE_MIN_STROKE_WIDTH,
            ),
            drawBaseFill: false,
        };
    }
    if (renderLayer === "gesture-erase") {
        return {
            tintColor: null,
            strokeColor: renderStyle.gestureEraseStrokeColor,
            strokeWidth: Math.max(
                resolvePolygonStrokeWidth(renderStyle) + 1,
                GESTURE_OUTLINE_MIN_STROKE_WIDTH,
            ),
            drawBaseFill: false,
        };
    }
    return null;
}

export function drawPolygonCellWithTransientOverlay({
    context,
    vertices,
    fillColor,
    renderLayer,
    renderStyle,
    committedStrokeColor = null,
    drawPreviewStroke = false,
    fillBridgeColor = null,
    fillBridgeStrokeWidth = 0,
}: DrawPolygonCellArgs): void {
    const overlayStyle = resolveTransientOverlayStyle(renderLayer, renderStyle);
    if (!overlayStyle || overlayStyle.drawBaseFill) {
        if (fillBridgeColor && fillBridgeStrokeWidth > 0) {
            context.save();
            context.strokeStyle = fillBridgeColor;
            context.lineWidth = fillBridgeStrokeWidth;
            context.lineJoin = "round";
            context.lineCap = "round";
            tracePolygonPath(context, vertices);
            context.stroke();
            context.restore();
        }
        if (context.fillStyle !== fillColor) {
            context.fillStyle = fillColor;
        }
        tracePolygonPath(context, vertices);
        context.fill();
        if (committedStrokeColor) {
            if (context.strokeStyle !== committedStrokeColor) {
                context.strokeStyle = committedStrokeColor;
            }
            context.lineWidth = renderStyle ? resolvePolygonStrokeWidth(renderStyle) : 1;
            context.stroke();
        }
    }
    if (overlayStyle) {
        if (overlayStyle.tintColor) {
            context.fillStyle = overlayStyle.tintColor;
            tracePolygonPath(context, vertices);
            context.fill();
        }
        context.strokeStyle = overlayStyle.strokeColor;
        context.lineWidth = overlayStyle.strokeWidth;
        tracePolygonPath(context, vertices);
        context.stroke();
        return;
    }
    if (drawPreviewStroke && renderLayer === "preview" && renderStyle) {
        context.strokeStyle = renderStyle.lineColor;
        context.lineWidth = resolvePolygonStrokeWidth(renderStyle);
        context.stroke();
    }
}

export function drawPolygonGrid(
    targetContext: CanvasRenderingContext2D,
    renderStyle: CanvasRenderStyle,
    geometryCache: PolygonGeometryCache | null,
): void {
    if (!geometryCache?.strokePath) {
        return;
    }
    targetContext.strokeStyle = renderStyle.lineColor;
    targetContext.lineWidth = resolvePolygonStrokeWidth(renderStyle);
    targetContext.stroke(geometryCache.strokePath);
}
