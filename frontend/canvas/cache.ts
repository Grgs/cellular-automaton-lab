import { getGeometryAdapter } from "../geometry/registry.js";
import type { TopologyPayload } from "../types/domain.js";
import type { GeometryAdapter, GeometryCache, GridMetrics } from "../types/rendering.js";

export const MAX_CACHED_GEOMETRY_CELLS = 20000;

export function resolveGeometryCache({
    existingKey,
    existingCache,
    width,
    height,
    cellSize,
    geometry,
    metrics,
    topology,
}: {
    existingKey: string;
    existingCache: GeometryCache | null;
    width: number;
    height: number;
    cellSize: number;
    geometry: string;
    metrics: GridMetrics;
    topology: TopologyPayload | null;
}): { cacheKey: string; geometryCache: GeometryCache | null } {
    const cacheKey = `${geometry}:${width}:${height}:${cellSize}:${topology?.topology_revision || ""}`;
    if (cacheKey === existingKey) {
        return { cacheKey, geometryCache: existingCache };
    }

    const adapter = getGeometryAdapter(geometry) as GeometryAdapter;

    return {
        cacheKey,
        geometryCache: adapter.buildCache({
            width,
            height,
            cellSize,
            metrics,
            topology,
            maxCachedCells: MAX_CACHED_GEOMETRY_CELLS,
        }),
    };
}
