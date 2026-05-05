import { getGeometryAdapter, isSupportedGeometry } from "./geometry/registry.js";
import {
    DEFAULT_GEOMETRY,
    DEFAULT_GRID_DIMENSIONS,
    MAX_GRID_DIMENSION,
    MIN_GRID_DIMENSION,
    clampGridDimension,
    getCellGap,
} from "./geometry/shared.js";
import type { ViewportDimensions } from "./types/controller.js";
import type { TopologyPayload } from "./types/domain.js";
import type { GeometryAdapter, GridMetrics } from "./types/rendering.js";

export {
    DEFAULT_GEOMETRY,
    MIN_GRID_DIMENSION,
    MAX_GRID_DIMENSION,
    DEFAULT_GRID_DIMENSIONS,
    getCellGap,
    clampGridDimension,
};

export function normalizeGeometry(geometry: string | null | undefined): string {
    return typeof geometry === "string" && isSupportedGeometry(geometry)
        ? geometry
        : DEFAULT_GEOMETRY;
}

export function gridMetrics(
    width: number,
    height: number,
    cellSize: number,
    geometry = DEFAULT_GEOMETRY,
    topology: TopologyPayload | null = null,
): GridMetrics {
    const adapter = getGeometryAdapter(geometry) as GeometryAdapter;
    return adapter.buildMetrics({
        width,
        height,
        cellSize,
        topology,
    });
}

export function computeViewportGridSize(
    viewportElement: Element | null,
    cellSize: number,
    fallback = DEFAULT_GRID_DIMENSIONS,
    geometry = DEFAULT_GEOMETRY,
): ViewportDimensions {
    if (!viewportElement) {
        return fallback;
    }

    const viewportWidth = Math.max(0, viewportElement.clientWidth);
    const viewportHeight = Math.max(0, viewportElement.clientHeight);
    if (viewportWidth === 0 || viewportHeight === 0) {
        return fallback;
    }

    const adapter = getGeometryAdapter(geometry) as GeometryAdapter;
    return (
        adapter.fitViewport?.({
            viewportWidth,
            viewportHeight,
            cellSize,
        }) ?? fallback
    );
}
