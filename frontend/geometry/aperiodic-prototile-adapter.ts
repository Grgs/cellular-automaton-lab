import {
    drawPolygonCellWithTransientOverlay,
    resolveShieldFillBridgeStrokeWidth,
} from "../canvas/draw.js";
import {
    buildMixedTopologyGeometryCache,
    resolveMixedCellFromOffset,
} from "../canvas/geometry-mixed.js";
import { asPolygonGeometryCache } from "./cache-guards.js";
import {
    APERIODIC_MIN_CENTER_CELL_SIZE,
    APERIODIC_MIN_METRIC_CELL_SIZE,
    APERIODIC_RENDER_SCALE_MULTIPLIER,
    CHAIR_RENDER_MARGIN_MIN,
    CHAIR_RENDER_MARGIN_SCALE,
    DEFAULT_APERIODIC_RENDER_MARGIN_MIN,
    DEFAULT_APERIODIC_RENDER_MARGIN_SCALE,
    SHIELD_RENDER_COORDINATE_SCALE,
    SHIELD_RENDER_MARGIN_MIN,
    SHIELD_RENDER_MARGIN_SCALE,
} from "./render-constants.js";
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

function displayCoordinateScale(geometry: string): number {
    return geometry === "shield" ? SHIELD_RENDER_COORDINATE_SCALE : 1;
}

function buildAperiodicMetrics(
    geometry: string,
    topology: TopologyPayload | null,
    cellSize: number,
    width = 0,
    height = 0,
): AperiodicMetrics {
    const scale = Math.max(APERIODIC_MIN_METRIC_CELL_SIZE, Number(cellSize) || 1) * APERIODIC_RENDER_SCALE_MULTIPLIER;
    const coordinateScale = displayCoordinateScale(geometry);
    const margin = geometry === "chair"
        ? Math.max(CHAIR_RENDER_MARGIN_MIN, scale * CHAIR_RENDER_MARGIN_SCALE)
        : geometry === "shield"
            ? Math.max(SHIELD_RENDER_MARGIN_MIN, scale * SHIELD_RENDER_MARGIN_SCALE)
        : Math.max(DEFAULT_APERIODIC_RENDER_MARGIN_MIN, scale * DEFAULT_APERIODIC_RENDER_MARGIN_SCALE);
    const cells = Array.isArray(topology?.cells) ? topology.cells : [];
    const allVertices = geometry === "shield"
        ? cells.flatMap((cell) => {
            if (!Array.isArray(cell.vertices) || cell.vertices.length === 0) {
                return [];
            }
            return cell.vertices.map((vertex) => ({
                x: Number(vertex.x) * coordinateScale,
                y: Number(vertex.y) * coordinateScale,
            }));
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
        coordinateScale,
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
            const scale = Math.max(APERIODIC_MIN_CENTER_CELL_SIZE, Number(cellSize) || 1) * APERIODIC_RENDER_SCALE_MULTIPLIER;
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
            drawPolygonCellWithTransientOverlay({
                context,
                vertices: geometryCell.vertices,
                fillColor: color,
                renderLayer,
                renderStyle,
                committedStrokeColor: geometry === "shield"
                    ? null
                    : renderStyle?.aperiodicLineColor || renderStyle?.lineColor || null,
                fillBridgeColor: (
                    geometry === "shield"
                    && renderLayer !== "gesture-paint"
                    && renderLayer !== "gesture-erase"
                )
                    ? color
                    : null,
                fillBridgeStrokeWidth: (
                    geometry === "shield"
                    && renderLayer !== "gesture-paint"
                    && renderLayer !== "gesture-erase"
                )
                    ? resolveShieldFillBridgeStrokeWidth(renderStyle)
                    : 0,
            });
        },

        applyViewportPreview() {
            return { applied: false, renderGrid: false };
        },
    };
}
