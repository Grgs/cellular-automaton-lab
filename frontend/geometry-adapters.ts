import { DEFAULT_GEOMETRY, gridMetrics, normalizeGeometry } from "./geometry-core.js";
import { getGeometryAdapter } from "./geometry/registry.js";
import type { PaintableCell } from "./types/editor.js";
import type { TopologyPayload } from "./types/domain.js";
import type { GeometryCache, GridMetrics, MixedGeometryCell } from "./types/rendering.js";

export function isMixedGeometry(geometry: string): boolean {
    return getGeometryAdapter(geometry).family === "mixed";
}

export function buildMixedCellGeometry(
    cell: PaintableCell,
    metrics: GridMetrics,
    geometry: string,
): MixedGeometryCell {
    const adapter = getGeometryAdapter(geometry);
    if (adapter.family !== "mixed" || typeof adapter.buildCellGeometry !== "function") {
        return null;
    }
    return adapter.buildCellGeometry({ cell, metrics });
}

export function resolveCellFromCanvasOffset(
    offsetX: number,
    offsetY: number,
    width: number,
    height: number,
    cellSize: number,
    geometry = DEFAULT_GEOMETRY,
    metrics: GridMetrics | null = null,
    geometryCache: GeometryCache | null = null,
): PaintableCell | null {
    return getGeometryAdapter(geometry).resolveCellFromOffset({
        offsetX,
        offsetY,
        width,
        height,
        cellSize,
        metrics,
        cache: geometryCache,
    });
}

export function cellCenterOffset(
    x: number,
    y: number,
    cellSize: number,
    geometry = DEFAULT_GEOMETRY,
): { x: number; y: number } {
    const adapter = getGeometryAdapter(geometry);
    return adapter.resolveCoordinateCenter({
        x,
        y,
        cellSize,
    });
}

export function topologyCellCenter(
    cell: PaintableCell,
    cellSize: number,
    geometry = DEFAULT_GEOMETRY,
    width = 0,
    height = 0,
    metrics: GridMetrics | null = null,
    geometryCache: GeometryCache | null = null,
    topology: TopologyPayload | null = null,
): { x: number; y: number } {
    const normalizedGeometry = normalizeGeometry(geometry);
    const adapter = getGeometryAdapter(normalizedGeometry);
    return adapter.resolveCellCenter({
        cell,
        width,
        height,
        cellSize,
        topology,
        metrics: metrics || gridMetrics(width, height, cellSize, normalizedGeometry, topology),
        cache: geometryCache,
    });
}
