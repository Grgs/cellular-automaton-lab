import { penroseCellGeometry } from "../canvas/geometry-penrose.js";
import { PENROSE_GEOMETRY, PENROSE_VERTEX_GEOMETRY } from "../topology.js";
import { fitRenderCellSizeWithMetrics } from "./shared.js";
import {
    buildPolygonGeometryCache,
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

interface PenroseMetrics extends GridMetrics {
    scale: number;
    minRawX: number;
    minRawY: number;
    maxRawX: number;
    maxRawY: number;
}

function buildPenroseMetrics(
    geometry: string,
    topology: TopologyPayload | null,
    cellSize: number,
    width = 0,
    height = 0,
): PenroseMetrics {
    const scale = Math.max(0.25, Number(cellSize) || 1) * 10;
    const margin = Math.max(16, scale * 0.45);
    const bounds = measureTopologyVertexBounds(topology);

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
        width: Number(topology?.topology_spec?.width) || Number(topology?.width) || width,
        height: Number(topology?.topology_spec?.height) || Number(topology?.height) || height,
        cellSize,
        gap: 0,
        scale,
        minRawX: bounds.minX,
        minRawY: bounds.minY,
        maxRawX: bounds.maxX,
        maxRawY: bounds.maxY,
        xInset: margin - (bounds.minX * scale),
        yInset: margin + (bounds.maxY * scale),
        cssWidth: ((bounds.maxX - bounds.minX) * scale) + (margin * 2),
        cssHeight: ((bounds.maxY - bounds.minY) * scale) + (margin * 2),
    };
}

function createPenroseGeometryAdapter(geometry: string): GeometryAdapter {
    return {
        geometry,
        family: "mixed",

        buildMetrics({ width, height, cellSize, topology }) {
            return buildPenroseMetrics(geometry, topology ?? null, cellSize, width, height);
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
                    buildPenroseMetrics(geometry, nextTopology, cellSize, nextWidth, nextHeight)
                ),
            });
        },

        buildCache({ topology, metrics }: GeometryBuildCacheArgs) {
            return buildPolygonGeometryCache(topology, (cell) => penroseCellGeometry(cell, metrics as PenroseMetrics));
        },

        buildCellGeometry({ cell, metrics, cache }) {
            return resolvePolygonGeometryCell(
                cell as RenderableTopologyCell,
                asPolygonGeometryCache(cache),
                (uncachedCell) => penroseCellGeometry(uncachedCell, metrics as PenroseMetrics),
            );
        },

        resolveCellFromOffset({ offsetX, offsetY, cache }) {
            return resolvePolygonCellFromOffset({ offsetX, offsetY, cache });
        },

        resolveCellCenter({ cell, width = 0, height = 0, cellSize, topology, metrics, cache }: GeometryResolveCellCenterArgs) {
            return resolvePolygonCellCenter({
                cell,
                width,
                height,
                cellSize,
                topology,
                metrics,
                cache,
                buildMetrics: ({ width: nextWidth, height: nextHeight, topology: nextTopology, cellSize: nextCellSize }) => (
                    buildPenroseMetrics(geometry, nextTopology ?? null, nextCellSize, nextWidth, nextHeight)
                ),
                buildCellGeometry: (nextCell, nextMetrics, polygonCache) => resolvePolygonGeometryCell(
                    nextCell,
                    polygonCache,
                    (uncachedCell) => penroseCellGeometry(uncachedCell, nextMetrics as PenroseMetrics),
                ),
            });
        },

        resolveCoordinateCenter({ x, y, cellSize }: GeometryResolveCoordinateCenterArgs) {
            const scale = Math.max(6, Number(cellSize) || 1) * 10;
            return {
                x: x * scale,
                y: y * scale,
            };
        },

        drawCell({ context, cell, stateValue, metrics, cache, colors, colorLookup, resolveRenderedCellColor, renderStyle, renderLayer }: RenderedCellArgs) {
            const geometryCell = resolvePolygonGeometryCell(
                cell as RenderableTopologyCell,
                asPolygonGeometryCache(cache),
                (uncachedCell) => penroseCellGeometry(uncachedCell, metrics as PenroseMetrics),
            );
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
            });
        },

        applyViewportPreview() {
            return { applied: false, renderGrid: false };
        },
    };
}

export const penroseGeometryAdapter = createPenroseGeometryAdapter(PENROSE_GEOMETRY);
export const penroseVertexGeometryAdapter = createPenroseGeometryAdapter(PENROSE_VERTEX_GEOMETRY);
