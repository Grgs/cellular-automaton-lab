import { resolveShieldFillBridgeStrokeWidth } from "../canvas/draw.js";
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
import {
    buildPolygonGeometryCache,
    buildTransformedPolygonGeometryCell,
    drawResolvedPolygonCell,
    measureTopologyVertexBounds,
    resolvePolygonCellCenter,
    resolvePolygonCellFromOffset,
    resolvePolygonGeometryCell,
} from "./polygon-adapter-shared.js";
import { asPolygonGeometryCache } from "./cache-guards.js";
import type {
    GeometryAdapter,
    GeometryBuildCacheArgs,
    GeometryResolveCellCenterArgs,
    GeometryResolveCoordinateCenterArgs,
    GridMetrics,
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
    const scale =
        Math.max(APERIODIC_MIN_METRIC_CELL_SIZE, Number(cellSize) || 1) *
        APERIODIC_RENDER_SCALE_MULTIPLIER;
    const coordinateScale = displayCoordinateScale(geometry);
    const margin =
        geometry === "chair"
            ? Math.max(CHAIR_RENDER_MARGIN_MIN, scale * CHAIR_RENDER_MARGIN_SCALE)
            : geometry === "shield"
              ? Math.max(SHIELD_RENDER_MARGIN_MIN, scale * SHIELD_RENDER_MARGIN_SCALE)
              : Math.max(
                    DEFAULT_APERIODIC_RENDER_MARGIN_MIN,
                    scale * DEFAULT_APERIODIC_RENDER_MARGIN_SCALE,
                );
    const bounds = measureTopologyVertexBounds(topology, (vertex) => ({
        x: Number(vertex.x) * coordinateScale,
        y: Number(vertex.y) * coordinateScale,
    }));

    if (!bounds) {
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

    return {
        geometry,
        width: Number(topology?.width) || Number(topology?.topology_spec?.width) || width,
        height: Number(topology?.height) || Number(topology?.topology_spec?.height) || height,
        cellSize,
        gap: 0,
        scale,
        coordinateScale,
        minRawX: bounds.minX,
        minRawY: bounds.minY,
        maxRawX: bounds.maxX,
        maxRawY: bounds.maxY,
        xInset: margin - bounds.minX * scale,
        yInset: margin + bounds.maxY * scale,
        cssWidth: (bounds.maxX - bounds.minX) * scale + margin * 2,
        cssHeight: (bounds.maxY - bounds.minY) * scale + margin * 2,
    };
}

function topologyCellGeometry(cell: RenderableTopologyCell, metrics: AperiodicMetrics) {
    const coordinateScale = displayCoordinateScale(metrics.geometry);
    return buildTransformedPolygonGeometryCell(
        cell,
        (vertex) => ({
            x: metrics.xInset + Number(vertex.x) * coordinateScale * metrics.scale,
            y: metrics.yInset - Number(vertex.y) * coordinateScale * metrics.scale,
        }),
        (center) =>
            center
                ? {
                      x: metrics.xInset + Number(center.x) * coordinateScale * metrics.scale,
                      y: metrics.yInset - Number(center.y) * coordinateScale * metrics.scale,
                  }
                : null,
    );
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

        fitRenderCellSize({
            viewportWidth,
            viewportHeight,
            width,
            height,
            topology,
            fallbackCellSize,
        }) {
            return fitRenderCellSizeWithMetrics({
                viewportWidth,
                viewportHeight,
                width,
                height,
                topology: topology ?? null,
                fallbackCellSize,
                buildMetrics: ({
                    width: nextWidth,
                    height: nextHeight,
                    topology: nextTopology,
                    cellSize,
                }) =>
                    buildAperiodicMetrics(geometry, nextTopology, cellSize, nextWidth, nextHeight),
            });
        },

        buildCache({ topology, metrics }: GeometryBuildCacheArgs) {
            return buildPolygonGeometryCache(topology, (cell) =>
                topologyCellGeometry(cell, metrics as AperiodicMetrics),
            );
        },

        buildCellGeometry({ cell, metrics, cache }) {
            return resolvePolygonGeometryCell(
                cell as RenderableTopologyCell,
                asPolygonGeometryCache(cache),
                (uncachedCell) => topologyCellGeometry(uncachedCell, metrics as AperiodicMetrics),
            );
        },

        resolveCellFromOffset({ offsetX, offsetY, cache }) {
            return resolvePolygonCellFromOffset({ offsetX, offsetY, cache });
        },

        resolveCellCenter({
            cell,
            width = 0,
            height = 0,
            cellSize,
            topology,
            metrics,
            cache,
        }: GeometryResolveCellCenterArgs) {
            return resolvePolygonCellCenter({
                cell,
                width,
                height,
                cellSize,
                topology,
                metrics,
                cache,
                buildMetrics: ({
                    width: nextWidth,
                    height: nextHeight,
                    topology: nextTopology,
                    cellSize: nextCellSize,
                }) =>
                    buildAperiodicMetrics(
                        geometry,
                        nextTopology ?? null,
                        nextCellSize,
                        nextWidth,
                        nextHeight,
                    ),
                buildCellGeometry: (nextCell, nextMetrics, polygonCache) =>
                    resolvePolygonGeometryCell(nextCell, polygonCache, (uncachedCell) =>
                        topologyCellGeometry(uncachedCell, nextMetrics as AperiodicMetrics),
                    ),
            });
        },

        resolveCoordinateCenter({ x, y, cellSize }: GeometryResolveCoordinateCenterArgs) {
            const scale =
                Math.max(APERIODIC_MIN_CENTER_CELL_SIZE, Number(cellSize) || 1) *
                APERIODIC_RENDER_SCALE_MULTIPLIER;
            return {
                x: x * scale,
                y: y * scale,
            };
        },

        drawCell({
            context,
            cell,
            stateValue,
            metrics,
            cache,
            colors,
            colorLookup,
            resolveRenderedCellColor,
            renderStyle,
            renderLayer,
        }: RenderedCellArgs) {
            const geometryCell = resolvePolygonGeometryCell(
                cell as RenderableTopologyCell,
                asPolygonGeometryCache(cache),
                (uncachedCell) => topologyCellGeometry(uncachedCell, metrics as AperiodicMetrics),
            );
            const color = geometryCell
                ? resolveRenderedCellColor(stateValue, colorLookup, colors, {
                      geometry,
                      cell: geometryCell.cell,
                  })
                : null;
            drawResolvedPolygonCell({
                geometry,
                geometryCell,
                cell,
                stateValue,
                context,
                colors,
                colorLookup,
                resolveRenderedCellColor,
                renderLayer,
                renderStyle,
                resolvedFillColor: color,
                committedStrokeColor:
                    geometry === "shield"
                        ? null
                        : renderStyle?.aperiodicLineColor || renderStyle?.lineColor || null,
                fillBridgeColor:
                    geometry === "shield" &&
                    renderLayer !== "gesture-paint" &&
                    renderLayer !== "gesture-erase"
                        ? color
                        : null,
                fillBridgeStrokeWidth:
                    geometry === "shield" &&
                    renderLayer !== "gesture-paint" &&
                    renderLayer !== "gesture-erase"
                        ? resolveShieldFillBridgeStrokeWidth(renderStyle)
                        : 0,
            });
        },

        applyViewportPreview() {
            return { applied: false, renderGrid: false };
        },
    };
}
