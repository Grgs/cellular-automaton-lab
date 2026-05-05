import { asPolygonGeometryCache } from "../geometry/cache-guards.js";
import { summarizePositiveAreaPolygonOverlaps } from "../geometry/polygon-overlap.js";
import type { TopologyPayload } from "../types/domain.js";
import type {
    GeometryBounds,
    GeometryCache,
    RenderDiagnosticsSampleCell,
    RenderDiagnosticsSnapshot,
    RenderableTopologyCell,
} from "../types/rendering.js";
import type { CanvasSurfaceMetrics } from "./surface.js";

type SampleRole = "lexicographicFirst" | "centerNearest" | "boundaryFurthest";

function isFinitePoint(
    value: { x?: number | null; y?: number | null } | null | undefined,
): value is { x: number; y: number } {
    return Number.isFinite(Number(value?.x)) && Number.isFinite(Number(value?.y));
}

function boundsFromVertices(vertices: Array<{ x: number; y: number }>): GeometryBounds | null {
    if (vertices.length === 0) {
        return null;
    }
    const xValues = vertices.map((vertex) => Number(vertex.x));
    const yValues = vertices.map((vertex) => Number(vertex.y));
    const minX = Math.min(...xValues);
    const maxX = Math.max(...xValues);
    const minY = Math.min(...yValues);
    const maxY = Math.max(...yValues);
    return {
        minX,
        maxX,
        minY,
        maxY,
        width: maxX - minX,
        height: maxY - minY,
    };
}

function boundsCenter(bounds: GeometryBounds): { x: number; y: number } {
    return {
        x: bounds.minX + bounds.width / 2,
        y: bounds.minY + bounds.height / 2,
    };
}

function rawGeometryForCell(cell: RenderableTopologyCell): {
    center: { x: number; y: number };
    bounds: GeometryBounds;
} | null {
    if (!Array.isArray(cell.vertices) || cell.vertices.length === 0) {
        return null;
    }
    const bounds = boundsFromVertices(cell.vertices);
    if (bounds === null) {
        return null;
    }
    return {
        center: isFinitePoint(cell.center)
            ? { x: Number(cell.center.x), y: Number(cell.center.y) }
            : boundsCenter(bounds),
        bounds,
    };
}

function renderedBoundsForCell(geometryCell: {
    minX: number;
    maxX: number;
    minY: number;
    maxY: number;
}): GeometryBounds {
    return {
        minX: geometryCell.minX,
        maxX: geometryCell.maxX,
        minY: geometryCell.minY,
        maxY: geometryCell.maxY,
        width: geometryCell.maxX - geometryCell.minX,
        height: geometryCell.maxY - geometryCell.minY,
    };
}

function centerDistanceSquared(
    center: { x: number; y: number },
    target: { x: number; y: number },
): number {
    const dx = center.x - target.x;
    const dy = center.y - target.y;
    return dx * dx + dy * dy;
}

function aggregateBounds(boundsList: GeometryBounds[]): GeometryBounds | null {
    if (boundsList.length === 0) {
        return null;
    }
    return boundsList.reduce((combined, bounds) => ({
        minX: Math.min(combined.minX, bounds.minX),
        maxX: Math.max(combined.maxX, bounds.maxX),
        minY: Math.min(combined.minY, bounds.minY),
        maxY: Math.max(combined.maxY, bounds.maxY),
        width: Math.max(combined.maxX, bounds.maxX) - Math.min(combined.minX, bounds.minX),
        height: Math.max(combined.maxY, bounds.maxY) - Math.min(combined.minY, bounds.minY),
    }));
}

function orientationTokenCounts(cells: RenderableTopologyCell[]): Record<string, number> | null {
    const counts = new Map<string, number>();
    for (const cell of cells) {
        if (typeof cell.orientation_token !== "string" || cell.orientation_token.length === 0) {
            continue;
        }
        counts.set(cell.orientation_token, (counts.get(cell.orientation_token) ?? 0) + 1);
    }
    if (counts.size === 0) {
        return null;
    }
    return Object.fromEntries(
        Array.from(counts.entries()).sort((left, right) => left[0].localeCompare(right[0])),
    );
}

function angularSectorCounts(
    centers: Array<{ x: number; y: number }>,
    origin: { x: number; y: number },
    sectorCount: number = 12,
): number[] | null {
    if (centers.length === 0 || sectorCount <= 0) {
        return null;
    }
    const counts = Array.from({ length: sectorCount }, () => 0);
    const sectorAngle = (Math.PI * 2) / sectorCount;
    for (const center of centers) {
        const dx = center.x - origin.x;
        const dy = center.y - origin.y;
        const angle = Math.atan2(dy, dx);
        const normalizedAngle = angle >= 0 ? angle : angle + Math.PI * 2;
        const index = Math.min(sectorCount - 1, Math.floor(normalizedAngle / sectorAngle));
        counts[index] = (counts[index] ?? 0) + 1;
    }
    return counts;
}

export function sampleRenderDiagnostics(
    topology: TopologyPayload | null,
    geometryCache: GeometryCache | null,
    {
        geometry,
        adapterFamily,
        metrics,
        cellSize,
    }: {
        geometry: string;
        adapterFamily: "regular" | "mixed" | "aperiodic";
        metrics: CanvasSurfaceMetrics;
        cellSize: number;
    },
): RenderDiagnosticsSnapshot | null {
    if (!topology?.cells?.length) {
        return null;
    }
    const polygonCache = asPolygonGeometryCache(geometryCache);
    if (polygonCache === null) {
        return null;
    }
    const topologyCells = topology.cells
        .map((cell) => {
            const typedCell = cell as RenderableTopologyCell;
            const rawGeometry = rawGeometryForCell(typedCell);
            const renderedGeometry = typedCell.id
                ? (polygonCache.cellsById.get(typedCell.id) ?? null)
                : null;
            if (rawGeometry === null || renderedGeometry === null) {
                return null;
            }
            return {
                cell: typedCell,
                rawCenter: rawGeometry.center,
                rawBounds: rawGeometry.bounds,
                renderedCenter: { x: renderedGeometry.centerX, y: renderedGeometry.centerY },
                renderedBounds: renderedBoundsForCell(renderedGeometry),
            };
        })
        .filter((entry): entry is NonNullable<typeof entry> => entry !== null)
        .sort((left, right) => left.cell.id.localeCompare(right.cell.id));
    if (topologyCells.length === 0) {
        return null;
    }
    const topologyBounds = boundsFromVertices(
        topologyCells.flatMap((entry) => entry.cell.vertices ?? []),
    );
    if (topologyBounds === null) {
        return null;
    }
    const topologyCenter = boundsCenter(topologyBounds);
    const renderedBounds = aggregateBounds(topologyCells.map((entry) => entry.renderedBounds));
    const renderedTopologyCenter = renderedBounds ? boundsCenter(renderedBounds) : null;
    const usedIds = new Set<string>();
    const roles: SampleRole[] = ["lexicographicFirst", "centerNearest", "boundaryFurthest"];
    const sampleCells = {
        lexicographicFirst: null,
        centerNearest: null,
        boundaryFurthest: null,
    } as RenderDiagnosticsSnapshot["sampleCells"];

    const resolveRole = (role: SampleRole): (typeof topologyCells)[number] | null => {
        const candidates = topologyCells.filter((entry) => !usedIds.has(entry.cell.id));
        if (candidates.length === 0) {
            return null;
        }
        if (role === "lexicographicFirst") {
            return candidates[0] ?? null;
        }
        if (role === "centerNearest") {
            return (
                [...candidates].sort((left, right) => {
                    const distanceDelta =
                        centerDistanceSquared(left.rawCenter, topologyCenter) -
                        centerDistanceSquared(right.rawCenter, topologyCenter);
                    return distanceDelta !== 0
                        ? distanceDelta
                        : left.cell.id.localeCompare(right.cell.id);
                })[0] ?? null
            );
        }
        return (
            [...candidates].sort((left, right) => {
                const distanceDelta =
                    centerDistanceSquared(right.rawCenter, topologyCenter) -
                    centerDistanceSquared(left.rawCenter, topologyCenter);
                return distanceDelta !== 0
                    ? distanceDelta
                    : left.cell.id.localeCompare(right.cell.id);
            })[0] ?? null
        );
    };

    for (const role of roles) {
        const selected = resolveRole(role);
        if (!selected) {
            continue;
        }
        usedIds.add(selected.cell.id);
        sampleCells[role] = {
            role,
            cellId: selected.cell.id,
            kind: typeof selected.cell.kind === "string" ? selected.cell.kind : null,
            rawCenter: selected.rawCenter,
            rawBounds: selected.rawBounds,
            renderedCenter: selected.renderedCenter,
            renderedBounds: selected.renderedBounds,
        } satisfies RenderDiagnosticsSampleCell;
    }

    return {
        geometry,
        adapterGeometry: geometry,
        adapterFamily,
        topologyBounds,
        renderMetrics: {
            cellSize,
            renderCellSize: cellSize,
            scale: typeof metrics.scale === "number" ? metrics.scale : null,
            coordinateScale:
                typeof metrics.coordinateScale === "number" ? metrics.coordinateScale : 1,
            xInset: metrics.xInset,
            yInset: metrics.yInset,
            cssWidth: metrics.cssWidth,
            cssHeight: metrics.cssHeight,
            canvasWidth: metrics.pixelWidth,
            canvasHeight: metrics.pixelHeight,
        },
        sampleCells,
        metricInputs: {
            renderedTopologyCenter,
            renderedCellCount: topologyCells.length,
            orientationTokenCounts: orientationTokenCounts(
                topologyCells.map((entry) => entry.cell),
            ),
            angularSectorCounts: renderedTopologyCenter
                ? angularSectorCounts(
                      topologyCells.map((entry) => entry.renderedCenter),
                      renderedTopologyCenter,
                  )
                : null,
        },
        overlapHotspots: null,
    };
}

export function resolveRenderDiagnosticsSnapshot(
    renderDiagnostics: RenderDiagnosticsSnapshot | null,
    geometryCache: GeometryCache | null,
): RenderDiagnosticsSnapshot | null {
    if (renderDiagnostics === null) {
        return null;
    }
    if (renderDiagnostics.overlapHotspots !== null) {
        return structuredClone(renderDiagnostics);
    }
    const polygonCache = asPolygonGeometryCache(geometryCache);
    const transformSampleIds = Object.values(renderDiagnostics.sampleCells)
        .map((sample) => sample?.cellId ?? null)
        .filter((cellId): cellId is string => typeof cellId === "string");
    return structuredClone({
        ...renderDiagnostics,
        overlapHotspots: polygonCache
            ? summarizePositiveAreaPolygonOverlaps(polygonCache.cells, {
                  maxStoredPairs: 50,
                  transformSampleIds,
              })
            : null,
    });
}

export function resolveRenderedCellCenter(
    geometryCache: GeometryCache | null,
    cellId: string,
): { x: number; y: number } | null {
    const polygonCache = asPolygonGeometryCache(geometryCache);
    const renderedGeometry = polygonCache?.cellsById.get(cellId) ?? null;
    if (!renderedGeometry) {
        return null;
    }
    return {
        x: renderedGeometry.centerX,
        y: renderedGeometry.centerY,
    };
}
