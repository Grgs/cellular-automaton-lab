import { tracePolygonPath } from "../canvas/draw.js";
import {
    buildMixedTopologyGeometryCache,
    isPolygonGeometryCache,
    resolveMixedCellFromOffset,
} from "../canvas/geometry-mixed.js";
import { penroseCellGeometry } from "../canvas/geometry-penrose.js";
import { PENROSE_GEOMETRY, PENROSE_VERTEX_GEOMETRY } from "../topology.js";
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
    const cells = Array.isArray(topology?.cells) ? topology.cells : [];
    const allVertices = cells.flatMap((cell) => Array.isArray(cell.vertices) ? cell.vertices : []);

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
        width: Number(topology?.topology_spec?.width) || Number(topology?.width) || width,
        height: Number(topology?.topology_spec?.height) || Number(topology?.height) || height,
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

function resolveGeometryCell(
    cell: RenderableTopologyCell,
    metrics: PenroseMetrics,
    cache: PolygonGeometryCache | null,
): PolygonGeometryCell | null {
    if (cell?.id && cache?.cellsById?.has(cell.id)) {
        return cache.cellsById.get(cell.id) ?? null;
    }
    return penroseCellGeometry(cell, metrics);
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
            return buildMixedTopologyGeometryCache(topology, (cell) => penroseCellGeometry(cell, metrics as PenroseMetrics));
        },

        buildCellGeometry({ cell, metrics }) {
            return penroseCellGeometry(cell as RenderableTopologyCell, metrics as PenroseMetrics);
        },

        resolveCellFromOffset({ offsetX, offsetY, cache }: GeometryResolveCellFromOffsetArgs) {
            return resolveMixedCellFromOffset(
                offsetX,
                offsetY,
                cache && "cellsById" in cache ? cache : null,
            );
        },

        resolveCellCenter({ cell, width = 0, height = 0, cellSize, topology, metrics, cache }: GeometryResolveCellCenterArgs) {
            const resolvedMetrics = (metrics || buildPenroseMetrics(geometry, topology ?? null, cellSize, width, height)) as PenroseMetrics;
            const geometryCell = resolveGeometryCell(
                cell as RenderableTopologyCell,
                resolvedMetrics,
                isPolygonGeometryCache(cache) ? cache : null,
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

        drawCell({ context, cell, stateValue, metrics, cache, colors, colorLookup, resolveRenderedCellColor }: RenderedCellArgs) {
            const geometryCell = resolveGeometryCell(
                cell as RenderableTopologyCell,
                metrics as PenroseMetrics,
                isPolygonGeometryCache(cache) ? cache : null,
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
        },

        applyViewportPreview() {
            return { applied: false, renderGrid: false };
        },
    };
}

export const penroseGeometryAdapter = createPenroseGeometryAdapter(PENROSE_GEOMETRY);
export const penroseVertexGeometryAdapter = createPenroseGeometryAdapter(PENROSE_VERTEX_GEOMETRY);
