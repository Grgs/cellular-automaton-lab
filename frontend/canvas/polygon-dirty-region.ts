import { polygonSpatialIndexIntersectionCandidates } from "../geometry/polygon-spatial-index.js";
import { asPolygonGeometryCache } from "../geometry/cache-guards.js";
import type { TopologyIndex, TopologyPayload } from "../types/domain.js";
import type { GeometryCache, PolygonIntersectionBounds } from "../types/rendering.js";

export const INCREMENTAL_CANDIDATE_RATIO_LIMIT = 0.25;
export const INCREMENTAL_DIRTY_AREA_RATIO_LIMIT = 0.35;
export const POLYGON_DIRTY_REGION_PADDING = 2;
export const POLYGON_DIRTY_QUERY_PADDING = 4;

export interface PolygonDirtyRegionPlan {
    cellIndexes: number[];
    dirtyAreaRatio: number;
    bounds: PolygonIntersectionBounds;
}

interface ResolvePolygonDirtyRegionPlanOptions {
    topology: TopologyPayload | null;
    topologyIndex: TopologyIndex;
    geometryCache: GeometryCache | null;
    changedCellIndexes: readonly number[];
    canvasWidth: number;
    canvasHeight: number;
    dirtyPadding?: number;
    candidatePadding?: number;
}

export function resolvePolygonDirtyRegionPlan({
    topology,
    topologyIndex,
    geometryCache,
    changedCellIndexes,
    canvasWidth,
    canvasHeight,
    dirtyPadding = POLYGON_DIRTY_REGION_PADDING,
    candidatePadding = POLYGON_DIRTY_QUERY_PADDING,
}: ResolvePolygonDirtyRegionPlanOptions): PolygonDirtyRegionPlan | null {
    const polygonCache = asPolygonGeometryCache(geometryCache);
    const spatialIndex = polygonCache?.spatialIndex;
    if (
        !topology ||
        !polygonCache ||
        !spatialIndex ||
        changedCellIndexes.length === 0 ||
        canvasWidth <= 0 ||
        canvasHeight <= 0
    ) {
        return null;
    }

    let minX = Number.POSITIVE_INFINITY;
    let maxX = Number.NEGATIVE_INFINITY;
    let minY = Number.POSITIVE_INFINITY;
    let maxY = Number.NEGATIVE_INFINITY;
    for (const cellIndex of changedCellIndexes) {
        const topologyCell = topology.cells[cellIndex];
        const geometryCell = topologyCell && polygonCache.cellsById.get(topologyCell.id);
        if (!geometryCell) {
            return null;
        }
        minX = Math.min(minX, geometryCell.minX);
        maxX = Math.max(maxX, geometryCell.maxX);
        minY = Math.min(minY, geometryCell.minY);
        maxY = Math.max(maxY, geometryCell.maxY);
    }
    minX = Math.floor(minX - dirtyPadding);
    maxX = Math.ceil(maxX + dirtyPadding);
    minY = Math.floor(minY - dirtyPadding);
    maxY = Math.ceil(maxY + dirtyPadding);

    const clampedMinX = Math.max(0, Math.min(canvasWidth, minX));
    const clampedMaxX = Math.max(0, Math.min(canvasWidth, maxX));
    const clampedMinY = Math.max(0, Math.min(canvasHeight, minY));
    const clampedMaxY = Math.max(0, Math.min(canvasHeight, maxY));
    const dirtyArea =
        Math.max(0, clampedMaxX - clampedMinX) * Math.max(0, clampedMaxY - clampedMinY);
    const dirtyAreaRatio = dirtyArea / (canvasWidth * canvasHeight);
    if (dirtyAreaRatio > INCREMENTAL_DIRTY_AREA_RATIO_LIMIT) {
        return null;
    }

    const candidateIndexes = new Set<number>();
    for (const candidate of polygonSpatialIndexIntersectionCandidates(spatialIndex, {
        minX: minX - candidatePadding,
        maxX: maxX + candidatePadding,
        minY: minY - candidatePadding,
        maxY: maxY + candidatePadding,
    })) {
        const indexedCell = topologyIndex.byId.get(candidate.cell.id);
        if (!indexedCell) {
            return null;
        }
        candidateIndexes.add(indexedCell.index);
    }
    for (const changedCellIndex of changedCellIndexes) {
        candidateIndexes.add(changedCellIndex);
    }

    const candidateLimit = Math.floor(topology.cells.length * INCREMENTAL_CANDIDATE_RATIO_LIMIT);
    if (candidateIndexes.size === 0 || candidateIndexes.size > candidateLimit) {
        return null;
    }

    return {
        cellIndexes: [...candidateIndexes].sort((left, right) => left - right),
        dirtyAreaRatio,
        bounds: { minX, maxX, minY, maxY },
    };
}
