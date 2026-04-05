import {
    resolveTransientOverlayStyle,
} from "../canvas/draw.js";
import {
    applyRegularViewportPreview,
    clampGridDimension,
    fitRenderCellSizeWithMetrics,
    getCellGap,
    squareGridMetrics,
} from "./shared.js";
import { parseRegularCellId, regularCellId } from "../topology.js";
import type { PaintableCell } from "../types/editor.js";
import type {
    GeometryAdapter,
    GeometryBuildMetricsArgs,
    GeometryDrawOverlayArgs,
    GeometryResolveCellCenterArgs,
    GeometryResolveCellFromOffsetArgs,
    GeometryResolveCoordinateCenterArgs,
    GeometryViewportPreviewArgs,
    GridMetrics,
    RenderedCellArgs,
} from "../types/rendering.js";

interface SquareMetrics extends GridMetrics {
    pitch: number;
}

function resolveSquareCoordinates(cell: PaintableCell | null | undefined): { x: number; y: number } {
    const parsed = parseRegularCellId(cell?.id);
    return {
        x: typeof cell?.x === "number" && Number.isInteger(cell.x) ? cell.x : parsed?.x || 0,
        y: typeof cell?.y === "number" && Number.isInteger(cell.y) ? cell.y : parsed?.y || 0,
    };
}

export const squareGeometryAdapter: GeometryAdapter = {
    geometry: "square",
    family: "regular",

    buildMetrics({ width, height, cellSize }: GeometryBuildMetricsArgs) {
        return squareGridMetrics(width, height, cellSize);
    },

    fitViewport({ viewportWidth, viewportHeight, cellSize }) {
        const gap = getCellGap(cellSize);
        return {
            width: clampGridDimension(Math.floor((viewportWidth - gap) / (cellSize + gap))),
            height: clampGridDimension(Math.floor((viewportHeight - gap) / (cellSize + gap))),
        };
    },

    fitRenderCellSize({ viewportWidth, viewportHeight, width, height, fallbackCellSize }) {
        return fitRenderCellSizeWithMetrics({
            viewportWidth,
            viewportHeight,
            width,
            height,
            fallbackCellSize,
            buildMetrics: ({ width: nextWidth, height: nextHeight, cellSize }) => squareGridMetrics(nextWidth, nextHeight, cellSize),
        });
    },

    buildCache() {
        return null;
    },

    resolveCellFromOffset({ offsetX, offsetY, width, height, cellSize, metrics }: GeometryResolveCellFromOffsetArgs) {
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

        return { id: regularCellId(x, y), kind: "cell", x, y };
    },

    resolveCellCenter({ cell, width = 0, height = 0, cellSize, metrics }: GeometryResolveCellCenterArgs) {
        const { x, y } = resolveSquareCoordinates(cell);
        const resolvedMetrics = (metrics || squareGridMetrics(
            Math.max(width, x + 1, 1),
            Math.max(height, y + 1, 1),
            cellSize,
        )) as SquareMetrics;
        return {
            x: resolvedMetrics.gap + (x * resolvedMetrics.pitch) + (cellSize / 2),
            y: resolvedMetrics.gap + (y * resolvedMetrics.pitch) + (cellSize / 2),
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

    drawCell({ context, cell, stateValue, metrics, colors, colorLookup, resolveRenderedCellColor, renderStyle, renderLayer }: RenderedCellArgs) {
        const squareMetrics = metrics as SquareMetrics;
        const { x, y } = resolveSquareCoordinates(cell);
        const overlayStyle = resolveTransientOverlayStyle(renderLayer, renderStyle);
        const color = resolveRenderedCellColor(
            stateValue,
            colorLookup,
            colors,
            { geometry: this.geometry, x, y },
        );
        const cellLeft = squareMetrics.gap + (x * squareMetrics.pitch);
        const cellTop = squareMetrics.gap + (y * squareMetrics.pitch);
        if (!overlayStyle || overlayStyle.drawBaseFill) {
            if (context.fillStyle !== color) {
                context.fillStyle = color;
            }
            context.fillRect(cellLeft, cellTop, squareMetrics.cellSize, squareMetrics.cellSize);
        }
        if (overlayStyle) {
            if (overlayStyle.tintColor) {
                context.fillStyle = overlayStyle.tintColor;
                context.fillRect(cellLeft, cellTop, squareMetrics.cellSize, squareMetrics.cellSize);
            }
            context.strokeStyle = overlayStyle.strokeColor;
            context.lineWidth = overlayStyle.strokeWidth;
            context.strokeRect(cellLeft, cellTop, squareMetrics.cellSize, squareMetrics.cellSize);
        }
    },

    applyViewportPreview(args: GeometryViewportPreviewArgs) {
        return applyRegularViewportPreview({
            geometry: this.geometry,
            ...args,
        });
    },
};
