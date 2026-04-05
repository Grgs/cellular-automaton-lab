import { resolvePolygonStrokeWidth, tracePolygonPath } from "../canvas/draw.js";
import {
    buildMixedTopologyGeometryCache,
    resolveMixedCellFromOffset,
} from "../canvas/geometry-mixed.js";
import { asPolygonGeometryCache } from "./cache-guards.js";
import { fitRenderCellSizeWithMetrics } from "./shared.js";
import type {
    GeometryAdapter,
    GeometryBuildCacheArgs,
    GeometryResolveCellCenterArgs,
    GeometryResolveCellFromOffsetArgs,
    GeometryResolveCoordinateCenterArgs,
    GridMetrics,
    PolygonGeometryCache,
    PolygonGeometryCell,
    RenderedCellArgs,
    RenderableTopologyCell,
} from "../types/rendering.js";
import type { TopologyPayload } from "../types/domain.js";

interface AperiodicMetrics extends GridMetrics {
    scale: number;
    minRawX: number;
    minRawY: number;
    maxRawX: number;
    maxRawY: number;
}

const SHIELD_RENDER_POLYGON_SCALE = 0.64;
const SHIELD_RENDER_COORDINATE_SCALE = 0.35;

function displayCoordinateScale(geometry: string): number {
    return geometry === "shield" ? SHIELD_RENDER_COORDINATE_SCALE : 1;
}

function scaleVerticesAroundCenter(
    vertices: { x: number; y: number }[],
    centerX: number,
    centerY: number,
    scale: number,
): { x: number; y: number }[] {
    return vertices.map((vertex) => ({
        x: centerX + ((vertex.x - centerX) * scale),
        y: centerY + ((vertex.y - centerY) * scale),
    }));
}

function shieldDisplayVertices(
    rawVertices: readonly { x: number; y: number }[],
    centerX: number,
    centerY: number,
): { x: number; y: number }[] {
    return scaleVerticesAroundCenter([...rawVertices], centerX, centerY, SHIELD_RENDER_POLYGON_SCALE);
}

function buildAperiodicMetrics(
    geometry: string,
    topology: TopologyPayload | null,
    cellSize: number,
    width = 0,
    height = 0,
): AperiodicMetrics {
    const scale = Math.max(0.25, Number(cellSize) || 1) * 10;
    const coordinateScale = displayCoordinateScale(geometry);
    const margin = geometry === "chair"
        ? Math.max(8, scale * 0.15)
        : geometry === "shield"
            ? Math.max(10, scale * 0.18)
        : Math.max(16, scale * 0.45);
    const cells = Array.isArray(topology?.cells) ? topology.cells : [];
    const allVertices = geometry === "shield"
        ? cells.flatMap((cell) => {
            if (!Array.isArray(cell.vertices) || cell.vertices.length === 0) {
                return [];
            }
            const centerX = Number.isFinite(Number(cell.center?.x))
                ? Number(cell.center?.x) * coordinateScale
                : (cell.vertices.reduce((sum, vertex) => sum + Number(vertex.x), 0) / cell.vertices.length) * coordinateScale;
            const centerY = Number.isFinite(Number(cell.center?.y))
                ? Number(cell.center?.y) * coordinateScale
                : (cell.vertices.reduce((sum, vertex) => sum + Number(vertex.y), 0) / cell.vertices.length) * coordinateScale;
            return shieldDisplayVertices(
                cell.vertices.map((vertex) => ({
                    x: Number(vertex.x) * coordinateScale,
                    y: Number(vertex.y) * coordinateScale,
                })),
                centerX,
                centerY,
            );
        })
        : cells.flatMap((cell) => Array.isArray(cell.vertices) ? cell.vertices : []);

    if (allVertices.length === 0) {
        return {
            geometry,
            width,
            height,
            cellSize,
            gap: 0,
            scale,
            xInset: margin,
            yInset: margin,
            cssWidth: margin * 2,
            cssHeight: margin * 2,
            minRawX: 0,
            minRawY: 0,
            maxRawX: 0,
            maxRawY: 0,
        };
    }

    const rawX = allVertices.map((vertex) => Number(vertex.x));
    const rawY = allVertices.map((vertex) => Number(vertex.y));
    const minRawX = Math.min(...rawX);
    const maxRawX = Math.max(...rawX);
    const minRawY = Math.min(...rawY);
    const maxRawY = Math.max(...rawY);

    return {
        geometry,
        width: Number(topology?.width) || Number(topology?.topology_spec?.width) || width,
        height: Number(topology?.height) || Number(topology?.topology_spec?.height) || height,
        cellSize,
        gap: 0,
        scale,
        minRawX,
        minRawY,
        maxRawX,
        maxRawY,
        xInset: margin - (minRawX * scale),
        yInset: margin + (maxRawY * scale),
        cssWidth: ((maxRawX - minRawX) * scale) + (margin * 2),
        cssHeight: ((maxRawY - minRawY) * scale) + (margin * 2),
    };
}

function topologyCellGeometry(
    cell: RenderableTopologyCell,
    metrics: AperiodicMetrics,
): PolygonGeometryCell | null {
    if (!Array.isArray(cell?.vertices) || cell.vertices.length === 0) {
        return null;
    }
    const coordinateScale = displayCoordinateScale(metrics.geometry);
    let vertices = cell.vertices.map((vertex) => ({
        x: metrics.xInset + ((Number(vertex.x) * coordinateScale) * metrics.scale),
        y: metrics.yInset - ((Number(vertex.y) * coordinateScale) * metrics.scale),
    }));
    const initialMinX = Math.min(...vertices.map((vertex) => vertex.x));
    const initialMaxX = Math.max(...vertices.map((vertex) => vertex.x));
    const initialMinY = Math.min(...vertices.map((vertex) => vertex.y));
    const initialMaxY = Math.max(...vertices.map((vertex) => vertex.y));
    const centerX = Number.isFinite(Number(cell.center?.x))
        ? metrics.xInset + ((Number(cell.center?.x) * coordinateScale) * metrics.scale)
        : (initialMinX + initialMaxX) / 2;
    const centerY = Number.isFinite(Number(cell.center?.y))
        ? metrics.yInset - ((Number(cell.center?.y) * coordinateScale) * metrics.scale)
        : (initialMinY + initialMaxY) / 2;
    if (metrics.geometry === "shield") {
        vertices = shieldDisplayVertices(vertices, centerX, centerY);
    }
    const minX = Math.min(...vertices.map((vertex) => vertex.x));
    const maxX = Math.max(...vertices.map((vertex) => vertex.x));
    const minY = Math.min(...vertices.map((vertex) => vertex.y));
    const maxY = Math.max(...vertices.map((vertex) => vertex.y));
    return {
        cell,
        vertices,
        centerX,
        centerY,
        minX,
        maxX,
        minY,
        maxY,
    };
}

function resolveGeometryCell(
    cell: RenderableTopologyCell,
    metrics: AperiodicMetrics,
    cache: PolygonGeometryCache | null,
): PolygonGeometryCell | null {
    if (cell?.id && cache?.cellsById?.has(cell.id)) {
        return cache.cellsById.get(cell.id) ?? null;
    }
    return topologyCellGeometry(cell, metrics);
}

export function createAperiodicPrototileGeometryAdapter(geometry: string): GeometryAdapter {
    return {
        geometry,
        family: "mixed",

        buildMetrics({ width, height, cellSize, topology }) {
            return buildAperiodicMetrics(geometry, topology ?? null, cellSize, width, height);
        },

        fitViewport({ fallbackDimensions }) {
            return fallbackDimensions ?? { width: 0, height: 0 };
        },

        fitRenderCellSize({ viewportWidth, viewportHeight, width, height, topology, fallbackCellSize }) {
            return fitRenderCellSizeWithMetrics({
                viewportWidth,
                viewportHeight,
                width,
                height,
                topology: topology ?? null,
                fallbackCellSize,
                buildMetrics: ({ width: nextWidth, height: nextHeight, topology: nextTopology, cellSize }) => (
                    buildAperiodicMetrics(geometry, nextTopology, cellSize, nextWidth, nextHeight)
                ),
            });
        },

        buildCache({ topology, metrics }: GeometryBuildCacheArgs) {
            return buildMixedTopologyGeometryCache(topology, (cell) => topologyCellGeometry(cell, metrics as AperiodicMetrics));
        },

        buildCellGeometry({ cell, metrics }) {
            return topologyCellGeometry(cell as RenderableTopologyCell, metrics as AperiodicMetrics);
        },

        resolveCellFromOffset({ offsetX, offsetY, cache }: GeometryResolveCellFromOffsetArgs) {
            return resolveMixedCellFromOffset(
                offsetX,
                offsetY,
                cache && "cellsById" in cache ? cache : null,
            );
        },

        resolveCellCenter({ cell, width = 0, height = 0, cellSize, topology, metrics, cache }: GeometryResolveCellCenterArgs) {
            const resolvedMetrics = (metrics || buildAperiodicMetrics(geometry, topology ?? null, cellSize, width, height)) as AperiodicMetrics;
            const geometryCell = resolveGeometryCell(
                cell as RenderableTopologyCell,
                resolvedMetrics,
                asPolygonGeometryCache(cache),
            );
            return geometryCell
                ? { x: geometryCell.centerX, y: geometryCell.centerY }
                : { x: 0, y: 0 };
        },

        resolveCoordinateCenter({ x, y, cellSize }: GeometryResolveCoordinateCenterArgs) {
            const scale = Math.max(6, Number(cellSize) || 1) * 10;
            return {
                x: x * scale,
                y: y * scale,
            };
        },

        drawCell({ context, cell, stateValue, metrics, cache, colors, colorLookup, resolveRenderedCellColor, renderStyle, renderLayer }: RenderedCellArgs) {
            const geometryCell = resolveGeometryCell(
                cell as RenderableTopologyCell,
                metrics as AperiodicMetrics,
                asPolygonGeometryCache(cache),
            );
            const color = resolveRenderedCellColor(
                stateValue,
                colorLookup,
                colors,
                { geometry, cell: geometryCell?.cell || cell },
            );
            if (!geometryCell) {
                return;
            }
            if (context.fillStyle !== color) {
                context.fillStyle = color;
            }
            tracePolygonPath(context, geometryCell.vertices);
            context.fill();
            const strokeColor = renderStyle?.aperiodicLineColor || renderStyle?.lineColor;
            if (strokeColor) {
                if (context.strokeStyle !== strokeColor) {
                    context.strokeStyle = strokeColor;
                }
                context.lineWidth = renderStyle ? resolvePolygonStrokeWidth(renderStyle) : 1;
                context.stroke();
            }
            if (renderLayer === "hover" && renderStyle) {
                context.fillStyle = renderStyle.hoverTintColor;
                tracePolygonPath(context, geometryCell.vertices);
                context.fill();
                context.strokeStyle = renderStyle.hoverStrokeColor;
                context.lineWidth = Math.max(resolvePolygonStrokeWidth(renderStyle), 1.5);
                tracePolygonPath(context, geometryCell.vertices);
                context.stroke();
            }
        },

        applyViewportPreview() {
            return { applied: false, renderGrid: false };
        },
    };
}
